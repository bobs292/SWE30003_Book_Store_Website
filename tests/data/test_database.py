import json
import sqlite3

import pytest

import src.data.database as db_module
from src.data.database import get_connection, init_db

# ============================================================================
# Fixtures
# Each test gets its own temporary database file so tests never affect
# each other or the real store.db. Without this isolation, a failing test
# could leave the database in a broken state that causes every test after
# it to fail for unrelated reasons.
# monkeypatch is a pytest built-in that temporarily replaces a module-level
# variable for the duration of a single test, then restores it automatically.
# tmp_path is a pytest built-in that creates a fresh empty directory for
# each test and cleans it up afterwards.


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    # Redirect DB_PATH and SEEDS_PATH away from the real files so every
    # test starts with a clean empty database and its own seed file.
    # autouse=True means this fixture runs automatically for every test in
    # this file without needing to list it as a parameter.
    db_file = tmp_path / "test.db"
    seeds_file = tmp_path / "data.json"
    monkeypatch.setattr(db_module, "DB_PATH", str(db_file))
    monkeypatch.setattr(db_module, "SEEDS_PATH", str(seeds_file))
    return tmp_path


# ============================================================================
# get_connection
# Tests that get_connection returns a working SQLite connection and that
# row_factory is configured correctly. row_factory is what allows columns
# to be accessed by name (row["email"]) instead of by position (row[0]).
# If row_factory is not set, every repository would break whenever columns
# are added or reordered in the schema.


def test_get_connection_returns_connection():
    # get_connection should return a live sqlite3 connection object that
    # can be used to run queries. If it returns None or raises an error
    # the database cannot be used at all.
    conn = get_connection()
    assert conn is not None
    conn.close()


def test_get_connection_row_factory_allows_column_access_by_name():
    # row_factory = sqlite3.Row means query results can be accessed by
    # column name like row["email"] instead of by index like row[0].
    # Without this every repository would need to use positional indexes
    # which makes the code fragile if columns are ever reordered.
    # This test creates a temporary table to verify the behaviour directly
    # without depending on any of the application tables existing.
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE t (a TEXT, b TEXT)")
    cursor.execute("INSERT INTO t VALUES (?, ?)", ("hello", "world"))
    row = cursor.execute("SELECT * FROM t").fetchone()
    assert row["a"] == "hello"
    assert row["b"] == "world"
    conn.close()


# ============================================================================
# init_db - table creation
# Tests that init_db creates the expected tables and columns. We use
# sqlite_master which is SQLite's built-in record of all tables, and
# PRAGMA table_info which returns one row per column for a given table.
# These tests confirm the schema matches what the rest of the application
# expects before any real data is inserted.


def test_init_db_does_not_raise():
    # Confirms that every CREATE TABLE statement in init_db is valid SQL
    # and executes without error. If any statement has a syntax error or
    # uses an unsupported constraint, sqlite3 will raise an OperationalError
    # and this test will fail with a clear message pointing to the problem.
    # This is the first thing to check when the schema changes.
    try:
        init_db()
    except Exception as e:
        pytest.fail(f"init_db raised an unexpected exception: {e}")


def test_init_db_creates_customers_table():
    # After init_db runs the customers table must exist in the database.
    # sqlite_master is SQLite's internal catalogue of all tables, views,
    # and indexes. Querying it by name confirms the table was created.
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND " "name='customers'"
    )
    assert cursor.fetchone() is not None
    conn.close()


def test_init_db_creates_books_table():
    # After init_db runs the books table must exist in the database.
    # If this fails it means the books CREATE TABLE statement was not
    # reached or raised an error before completing.
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND " "name='books'"
    )
    assert cursor.fetchone() is not None
    conn.close()


def test_init_db_is_idempotent():
    # Calling init_db more than once should not raise an error or create
    # duplicate tables. The CREATE TABLE IF NOT EXISTS clause handles this.
    # This matters because init_db is called on every app startup, so if
    # the database already exists from a previous run it must not fail.
    # We exclude SQLite's internal tables (those prefixed with sqlite_) from
    # the count. SQLite automatically creates sqlite_sequence when any table
    # uses AUTOINCREMENT, so without the filter the count would be 3 not 2.
    init_db()
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND "
        "name NOT LIKE 'sqlite_%'"
    )
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 5


def test_customers_table_has_expected_columns():
    # Confirms the customers table has all the columns the customer
    # repository expects. PRAGMA table_info returns one row per column
    # with the column name in the 'name' field. If a column is missing
    # the repository will raise an error when it tries to use it.
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(customers)")
    columns = {row["name"] for row in cursor.fetchall()}
    conn.close()
    expected = {
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "password",
        "street",
        "suburb",
        "state",
        "postcode",
    }
    assert expected.issubset(columns)


def test_books_table_has_expected_columns():
    # Confirms the books table has all the columns the book repository
    # expects. If a column is renamed or removed here without updating
    # the repository, the repository tests will fail with a KeyError.
    # Catching it here first makes the cause clearer.
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(books)")
    columns = {row["name"] for row in cursor.fetchall()}
    conn.close()
    expected = {
        "isbn",
        "title",
        "author",
        "genre",
        "description",
        "price",
        "stock",
    }
    assert expected.issubset(columns)


# ============================================================================
# init_db - books table constraints
# Tests that the CHECK constraints on the books table reject invalid data
# at the database level. sqlite3.IntegrityError is the exception SQLite
# raises when a CHECK or UNIQUE constraint is violated.
# These tests follow the same boundary value pattern as the customer
# repository tests: one test for the lower bound, one for the upper bound,
# and one confirming valid values are accepted.


def _insert_book(conn, **overrides):
    # Helper that inserts a fully valid book with optional field overrides.
    # Centralising the defaults here means each test only needs to specify
    # the one field it is testing, keeping tests short and focused.
    # **overrides uses Python's keyword argument unpacking so callers can
    # write _insert_book(conn, title='') to test an empty title.
    defaults = dict(
        title="Test Book",
        author="Test Author",
        isbn="9780000000001",
        genre="Fiction",
        description="A test book.",
        price=10.0,
        stock=5,
    )
    defaults.update(overrides)
    conn.execute(
        """
        INSERT INTO books (title, author, isbn, genre, description,
        price, stock)
        VALUES (:title, :author, :isbn, :genre, :description,
        :price, :stock)
    """,
        defaults,
    )
    conn.commit()


def test_book_title_empty_raises(isolated_db):
    # An empty title should be rejected. The CHECK constraint requires
    # length(title) >= 1 so a zero-length string must fail.
    init_db()
    conn = get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        _insert_book(conn, title="")
    conn.close()


def test_book_title_over_limit_raises(isolated_db):
    # A title longer than 200 characters should be rejected. 201 characters
    # is the first value that exceeds the upper bound.
    init_db()
    conn = get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        _insert_book(conn, title="A" * 201)
    conn.close()


def test_book_author_empty_raises(isolated_db):
    # An empty author field should be rejected. A book must always have
    # an identifiable author in the catalogue.
    init_db()
    conn = get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        _insert_book(conn, author="")
    conn.close()


def test_book_author_over_limit_raises(isolated_db):
    # An author name longer than 200 characters should be rejected.
    init_db()
    conn = get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        _insert_book(conn, author="A" * 201)
    conn.close()


def test_book_price_negative_raises(isolated_db):
    # A negative price makes no sense for a purchasable product and should
    # be rejected. The CHECK constraint requires price >= 0.
    init_db()
    conn = get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        _insert_book(conn, price=-1.0)
    conn.close()


def test_book_price_zero_is_valid(isolated_db):
    # A price of zero is allowed for free or promotional books. Zero is
    # the lower boundary that should pass the CHECK constraint.
    init_db()
    conn = get_connection()
    _insert_book(conn, price=0.0)
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM books WHERE title = ?", ("Test Book",))
    assert cursor.fetchone()["price"] == 0.0
    conn.close()


def test_book_stock_negative_raises(isolated_db):
    # Negative stock is not meaningful and should be rejected. The CHECK
    # constraint requires stock >= 0.
    init_db()
    conn = get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        _insert_book(conn, stock=-1)
    conn.close()


def test_book_stock_zero_is_valid(isolated_db):
    # A stock of zero is valid and means the book is currently out of stock.
    # Zero is the lower boundary that should pass the CHECK constraint.
    init_db()
    conn = get_connection()
    _insert_book(conn, stock=0)
    cursor = conn.cursor()
    cursor.execute("SELECT stock FROM books WHERE title = ?", ("Test Book",))
    assert cursor.fetchone()["stock"] == 0
    conn.close()


def test_book_isbn_null_raises(isolated_db):
    # ISBN is the primary key, so it is mandatory. A null isbn has no key
    # and must be rejected. This is the inverse of the old behaviour, where
    # isbn was an optional business attribute that could be null.
    init_db()
    conn = get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        _insert_book(conn, isbn=None)
    conn.close()


def test_book_isbn_empty_raises(isolated_db):
    # An empty string is technically not null but is a useless key. The
    # CHECK(length(isbn) >= 1) constraint rejects it so it cannot slip in
    # as a valid primary key.
    init_db()
    conn = get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        _insert_book(conn, isbn="")
    conn.close()


def test_book_duplicate_isbn_raises(isolated_db):
    # isbn is the primary key, so two books cannot share one. Inserting a
    # second book with an isbn already in the table must raise.
    init_db()
    conn = get_connection()
    _insert_book(conn, isbn="9780000000123", title="First")
    with pytest.raises(sqlite3.IntegrityError):
        _insert_book(conn, isbn="9780000000123", title="Second")
    conn.close()


def test_book_valid_insert_succeeds(isolated_db):
    # A book with all valid fields should insert without any errors and
    # appear in the table. This is the baseline that confirms the schema
    # accepts correct data before testing what it rejects.
    init_db()
    conn = get_connection()
    _insert_book(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM books")
    assert cursor.fetchone()[0] == 1
    conn.close()


def test_phone_number_must_be_unique(isolated_db):
    # The UNIQUE constraint on phone_number should reject a second customer
    # with the same non-null phone number.
    init_db()
    conn = get_connection()
    conn.execute(
        "INSERT INTO customers (first_name, last_name, email, phone_number, password) "
        "VALUES (?, ?, ?, ?, ?)",
        ("John", "Smith", "a@b.co", "0412345678", "a" * 60),
    )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO customers (first_name, last_name, email, "
            "phone_number, password) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Jane", "Doe", "c@d.co", "0412345678", "b" * 60),
        )
    conn.close()


# ============================================================================
# _seed_books
# Tests that the seed loader reads data.json and populates the books table
# on first run, upserts existing rows on later runs (matched by ISBN) so
# edits like a changed price take effect, skips entries that have no ISBN,
# and handles edge cases like a missing seed file gracefully.
# _seed_books is called inside init_db so all these tests call init_db
# after writing seed data to the temporary SEEDS_PATH.


def test_seed_books_populates_table_on_first_run(isolated_db):
    # When the books table is empty and data.json exists, init_db should
    # insert all books from the seed file. This test writes two books to
    # the seed file and checks that both appear in the database after init_db.
    seed_data = {
        "books": [
            {
                "title": "Seed Book One",
                "author": "Author A",
                "isbn": "9780000000001",
                "genre": "Fiction",
                "description": "First seed book.",
                "price": 15.0,
                "stock": 3,
            },
            {
                "title": "Seed Book Two",
                "author": "Author B",
                "isbn": "9780000000002",
                "genre": "Nonfiction",
                "description": "Second seed book.",
                "price": 20.0,
                "stock": 7,
            },
        ]
    }
    with open(db_module.SEEDS_PATH, "w", encoding="utf-8") as f:
        json.dump(seed_data, f)

    init_db()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM books")
    assert cursor.fetchone()[0] == 2
    conn.close()


def test_seed_books_does_not_duplicate_on_second_run(isolated_db):
    # Calling init_db a second time when the books table already has rows
    # should not insert duplicates. The seed function upserts on ISBN, so a
    # book already in the database is updated in place rather than added
    # again, leaving the row count unchanged.
    seed_data = {
        "books": [
            {
                "title": "Seed Book",
                "author": "Author A",
                "isbn": "9780000000001",
                "genre": "Fiction",
                "description": "",
                "price": 10.0,
                "stock": 1,
            }
        ]
    }
    with open(db_module.SEEDS_PATH, "w", encoding="utf-8") as f:
        json.dump(seed_data, f)

    init_db()
    init_db()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM books")
    assert cursor.fetchone()[0] == 1
    conn.close()


def test_seed_books_handles_missing_seed_file(isolated_db):
    # If data.json does not exist, init_db should complete without crashing
    # and leave the books table empty. This handles a fresh environment
    # where the seed file has not been created yet.
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM books")
    assert cursor.fetchone()[0] == 0
    conn.close()


def test_seed_books_stores_correct_values(isolated_db):
    # The values written to the database should exactly match the values
    # in data.json. This catches any field mapping errors in the INSERT
    # statement, for example if isbn and genre were accidentally swapped.
    seed_data = {
        "books": [
            {
                "title": "Verified Book",
                "author": "Verified Author",
                "isbn": "9780000000099",
                "genre": "Mystery",
                "description": "A verified description.",
                "price": 19.99,
                "stock": 4,
            }
        ]
    }
    with open(db_module.SEEDS_PATH, "w", encoding="utf-8") as f:
        json.dump(seed_data, f)

    init_db()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE title = ?", ("Verified Book",))
    row = cursor.fetchone()
    conn.close()

    assert row["title"] == "Verified Book"
    assert row["author"] == "Verified Author"
    assert row["isbn"] == "9780000000099"
    assert row["genre"] == "Mystery"
    assert row["description"] == "A verified description."
    assert row["price"] == 19.99
    assert row["stock"] == 4


def test_seed_books_skips_entry_without_isbn(isolated_db):
    # A seed entry with no isbn cannot be keyed and must be skipped rather
    # than inserted. This guards against the old bug where removing an isbn
    # from the seed file produced a second copy of the book with no cover.
    seed_data = {
        "books": [
            {
                "title": "Keyless Book",
                "author": "Author A",
                "genre": "Fiction",
                "description": "",
                "price": 10.0,
                "stock": 1,
            }
        ]
    }
    with open(db_module.SEEDS_PATH, "w", encoding="utf-8") as f:
        json.dump(seed_data, f)

    init_db()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM books")
    assert cursor.fetchone()[0] == 0
    conn.close()


def test_seed_books_removing_isbn_does_not_duplicate(isolated_db):
    # Reproduces the reported scenario directly. A book is seeded with an
    # isbn on the first run. On the second run its isbn has been removed
    # from the seed file. The keyless entry is skipped, so the original row
    # stays and no duplicate title appears.
    with_isbn = {
        "books": [
            {
                "title": "Gone Girl",
                "author": "Gillian Flynn",
                "isbn": "9780307588371",
                "genre": "Mystery",
                "description": "",
                "price": 19.99,
                "stock": 8,
            }
        ]
    }
    without_isbn = {
        "books": [
            {
                "title": "Gone Girl",
                "author": "Gillian Flynn",
                "genre": "Mystery",
                "description": "",
                "price": 19.99,
                "stock": 8,
            }
        ]
    }
    with open(db_module.SEEDS_PATH, "w", encoding="utf-8") as f:
        json.dump(with_isbn, f)
    init_db()

    with open(db_module.SEEDS_PATH, "w", encoding="utf-8") as f:
        json.dump(without_isbn, f)
    init_db()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM books WHERE title = ?", ("Gone Girl",))
    assert cursor.fetchone()[0] == 1
    conn.close()


def test_seed_books_updates_changed_price_on_reseed(isolated_db):
    # When the seed file changes a value for an existing isbn, re-seeding
    # must update the row in place. This guards against the old bug where
    # books already in the table were skipped, so price edits never applied.
    original = {
        "books": [
            {
                "title": "The Martian",
                "author": "Andy Weir",
                "isbn": "9780553418026",
                "genre": "Science Fiction",
                "description": "",
                "price": 18.99,
                "stock": 5,
            }
        ]
    }
    updated = {
        "books": [
            {
                "title": "The Martian",
                "author": "Andy Weir",
                "isbn": "9780553418026",
                "genre": "Science Fiction",
                "description": "",
                "price": 9.99,
                "stock": 5,
            }
        ]
    }
    with open(db_module.SEEDS_PATH, "w", encoding="utf-8") as f:
        json.dump(original, f)
    init_db()

    with open(db_module.SEEDS_PATH, "w", encoding="utf-8") as f:
        json.dump(updated, f)
    init_db()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM books WHERE isbn = ?", ("9780553418026",))
    rows = cursor.fetchall()
    conn.close()

    # Exactly one row, and its price reflects the edited seed value.
    assert len(rows) == 1
    assert rows[0]["price"] == 9.99


# ============================================================================
# _seed_users
# Tests that the user seed loader reads data.json and populates the customers
# table on first run, upserts existing rows on later runs (matched by email)
# so profile edits take effect, skips entries with no email or no password,
# does not overwrite an existing password on re-seed, and handles a duplicate
# phone_number gracefully by skipping that entry rather than crashing startup.

# Any 60-character string satisfies the DB CHECK(length(password) >= 60).
# Real password hashes are longer, but the exact format is irrelevant here
# because we are testing seeding logic, not password hashing.
_SEED_HASH = "a" * 60


def _make_seed_user(**overrides):
    defaults = dict(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        password=_SEED_HASH,
        phone_number="0412345678",
        street="1 Test St",
        suburb="Melbourne",
        state="VIC",
        postcode="3000",
    )
    defaults.update(overrides)
    return defaults


def _write_seed(path, users):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"users": users}, f)


def test_seed_users_populates_table_on_first_run(isolated_db):
    # Two valid seed users should both appear in the customers table after init_db.
    _write_seed(
        db_module.SEEDS_PATH,
        [
            _make_seed_user(email="a@example.com", phone_number="0411111111"),
            _make_seed_user(email="b@example.com", phone_number="0422222222"),
        ],
    )
    init_db()

    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    conn.close()
    assert count == 2


def test_seed_users_does_not_duplicate_on_second_run(isolated_db):
    # Calling init_db a second time when the customers table already has a row
    # should leave the count unchanged — the upsert on email updates in place.
    _write_seed(db_module.SEEDS_PATH, [_make_seed_user()])
    init_db()
    init_db()

    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    conn.close()
    assert count == 1


def test_seed_users_handles_missing_seed_file(isolated_db):
    # When data.json does not exist, init_db must complete without error and
    # leave the customers table empty.
    init_db()

    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    conn.close()
    assert count == 0


def test_seed_users_stores_correct_values(isolated_db):
    # Every field in the seed entry must appear verbatim in the database row.
    # This catches column transpositions in the INSERT statement.
    _write_seed(
        db_module.SEEDS_PATH,
        [
            _make_seed_user(
                first_name="Jane",
                last_name="Smith",
                email="jane@example.com",
                phone_number="0498765432",
                street="42 Test Road",
                suburb="Sydney",
                state="NSW",
                postcode="2000",
            )
        ],
    )
    init_db()

    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM customers WHERE email = ?", ("jane@example.com",)
    ).fetchone()
    conn.close()

    assert row["first_name"] == "Jane"
    assert row["last_name"] == "Smith"
    assert row["email"] == "jane@example.com"
    assert row["phone_number"] == "0498765432"
    assert row["street"] == "42 Test Road"
    assert row["suburb"] == "Sydney"
    assert row["state"] == "NSW"
    assert row["postcode"] == "2000"


def test_seed_users_skips_entry_without_email(isolated_db):
    # A user with no email has no unique key and must be skipped silently.
    # The customers table should remain empty.
    user = _make_seed_user()
    del user["email"]
    _write_seed(db_module.SEEDS_PATH, [user])
    init_db()

    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    conn.close()
    assert count == 0


def test_seed_users_skips_entry_without_password(isolated_db):
    # A user with no password hash would produce an account that can never be
    # logged into. Such entries are skipped rather than inserted.
    user = _make_seed_user()
    del user["password"]
    _write_seed(db_module.SEEDS_PATH, [user])
    init_db()

    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    conn.close()
    assert count == 0


def test_seed_users_updates_profile_on_reseed(isolated_db):
    # When the seed file changes a profile field for an existing email,
    # re-seeding must update the stored row. This mirrors the book upsert
    # behaviour so seed file edits always take effect on the next run.
    _write_seed(db_module.SEEDS_PATH, [_make_seed_user(first_name="Jane")])
    init_db()

    _write_seed(db_module.SEEDS_PATH, [_make_seed_user(first_name="Janet")])
    init_db()

    conn = get_connection()
    row = conn.execute(
        "SELECT first_name FROM customers WHERE email = ?", ("test@example.com",)
    ).fetchone()
    conn.close()
    assert row["first_name"] == "Janet"


def test_seed_users_does_not_update_password_on_reseed(isolated_db):
    # Password is intentionally excluded from the ON CONFLICT UPDATE so a user
    # who registered with a seed email and later changed their password is not
    # silently overwritten when the server restarts.
    original_hash = "a" * 60
    new_hash = "b" * 60

    _write_seed(db_module.SEEDS_PATH, [_make_seed_user(password=original_hash)])
    init_db()

    _write_seed(db_module.SEEDS_PATH, [_make_seed_user(password=new_hash)])
    init_db()

    conn = get_connection()
    row = conn.execute(
        "SELECT password FROM customers WHERE email = ?", ("test@example.com",)
    ).fetchone()
    conn.close()
    assert row["password"] == original_hash


def test_seed_users_skips_duplicate_phone_number(isolated_db):
    # Two seed users sharing a phone_number violate the UNIQUE constraint.
    # The second entry must be skipped (with a printed warning) rather than
    # crashing the whole startup, and the first entry must remain intact.
    _write_seed(
        db_module.SEEDS_PATH,
        [
            _make_seed_user(email="first@example.com", phone_number="0411111111"),
            _make_seed_user(email="second@example.com", phone_number="0411111111"),
        ],
    )
    init_db()

    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    first = conn.execute(
        "SELECT email FROM customers WHERE email = ?", ("first@example.com",)
    ).fetchone()
    conn.close()

    assert count == 1
    assert first is not None


def test_seed_users_null_address_when_fields_absent(isolated_db):
    # A seed user with no address keys must produce NULL for all four address
    # columns, not an empty string or a partial address that would violate the
    # all-or-nothing CHECK constraint.
    user = {
        "first_name": "NoAddr",
        "last_name": "User",
        "email": "noaddr@example.com",
        "password": _SEED_HASH,
    }
    _write_seed(db_module.SEEDS_PATH, [user])
    init_db()

    conn = get_connection()
    row = conn.execute(
        "SELECT street, suburb, state, postcode FROM customers WHERE email = ?",
        ("noaddr@example.com",),
    ).fetchone()
    conn.close()

    assert row["street"] is None
    assert row["suburb"] is None
    assert row["state"] is None
    assert row["postcode"] is None
