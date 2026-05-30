# Patterns Reference

This document explains the patterns used in this project using the customer
registration flow as a concrete example. Use this as a reference when
implementing new features.

---

## The Register Flow

When a customer submits the registration form the request travels through
three layers before anything is saved to the database.

```
Browser POST /register
    presentation/routes/auth_routes.py          reads the form, calls the service
    domain/services/auth_service.py             enforces business rules, calls the repository
    domain/repositories/customer_repository.py  defines what operations exist
    data/repositories/customer_repository.py    performs the actual SQL
```

Each layer only talks to the layer directly below it. The presentation layer
never touches the database. The domain layer never touches Flask.

---

## Pattern 1: Abstract Base Class

The abstract repository defines what operations must exist without saying how
they work. This is the contract.

```python
# src/domain/repositories/customer_repository.py
from abc import ABC, abstractmethod

class CustomerRepository(ABC):

    @abstractmethod
    def save(self, customer):
        # Persists a new customer to the data store.
        pass

    @abstractmethod
    def find_by_email(self, email):
        # Returns a Customer object matching the given email, or None if not found.
        pass

    @abstractmethod
    def find_by_id(self, customer_id):
        # Returns a Customer object matching the given id, or None if not found.
        pass
```

If a class inherits from CustomerRepository and does not implement all three
methods, Python raises an error immediately. The abstract class is the
guarantee that any concrete implementation will have the same interface.

The domain layer only ever imports this class. It never imports the concrete
SQLite implementation. This means the business logic has no knowledge of how
or where data is stored.

---

## Pattern 2: Value Object

A value object is an object defined entirely by its attributes with no
identity of its own. Two value objects with the same attributes are considered
identical. They should be treated as immutable.

Address is a value object in this project. Rather than storing four loose
fields on Customer, all four address fields are grouped into a single class.
This makes it structurally impossible to create a partial address.

```python
# src/domain/models/customer.py
class Address:
    def __init__(self, street, suburb, state, postcode):
        self.street = street
        self.suburb = suburb
        self.state = state
        self.postcode = postcode
```

Customer accepts an optional Address object rather than four optional fields.

```python
class Customer(User):
    def __init__(self, first_name, last_name, email, password,
                 phone_number=None, address=None, customer_id=None):
        super().__init__(first_name, last_name, email, password)
        self.phone_number = phone_number
        self.address = address
        self.customer_id = customer_id
```

The database stores address as four columns. The repository is responsible
for flattening the Address object on save and reconstructing it on load.
This mapping is a data layer concern and lives only in the concrete repository.

---

## Pattern 3: Repository

The concrete repository inherits from the abstract class and implements each
method with actual SQL. This is the only place in the project where SQL is
written for customers.

```python
# src/data/repositories/customer_repository.py
class SqliteCustomerRepository(CustomerRepository):

    def save(self, customer):
        # Flatten the Address object into four columns for storage.
        street = customer.address.street if customer.address else None
        suburb = customer.address.suburb if customer.address else None
        state = customer.address.state if customer.address else None
        postcode = customer.address.postcode if customer.address else None
        ...

    def _row_to_customer(self, row):
        # Reconstruct the Address object from the four database columns if present.
        address = None
        if row["street"] is not None:
            address = Address(
                street=row["street"],
                suburb=row["suburb"],
                state=row["state"],
                postcode=row["postcode"]
            )
        return Customer(
            first_name=row["first_name"],
            ...
            address=address,
            customer_id=row["customer_id"]
        )
```

The service never imports this class. It only ever imports the abstract class.
The concrete class is only named once in the entire project, in app.py.

---

## Pattern 4: Service

The service contains the business rules. It receives the abstract repository
as a constructor argument and uses it to load and save data. It has no
knowledge of Flask, SQLite, or any infrastructure concern.

```python
# src/domain/services/auth_service.py
from src.domain.repositories.customer_repository import CustomerRepository

class AuthService:
    def __init__(self, customer_repo: CustomerRepository):
        self.customer_repo = customer_repo

    def register(self, first_name, last_name, email, password, ...):
        if self.customer_repo.find_by_email(email):
            raise ValueError("An account with this email already exists.")
        customer = Customer(
            first_name=first_name,
            ...
            password=generate_password_hash(password)
        )
        self.customer_repo.save(customer)

    def login(self, email, password):
        customer = self.customer_repo.find_by_email(email)
        if not customer:
            raise ValueError("Invalid email or password.")
        if not check_password_hash(customer.password, password):
            raise ValueError("Invalid email or password.")
        return {"customer_id": customer.customer_id, "email": customer.email}
```

Notice the type hint is CustomerRepository, not SqliteCustomerRepository. The
service does not know or care which concrete implementation is injected.

Services return plain dictionaries to the presentation layer. They never
return domain model objects. This means the presentation layer has no
knowledge of the internal domain models.

---

## Pattern 5: Dependency Injection

Dependency injection is the practice of passing dependencies into a class
rather than creating them inside it. In this project it happens in app.py.

```python
# src/app.py
from src.data.repositories.customer_repository import SqliteCustomerRepository
from src.domain.services.auth_service import AuthService
from src.presentation.routes.auth_routes import create_auth_routes

def create_app():
    # Concrete class named here only.
    customer_repo = SqliteCustomerRepository()

    # Injected into the service. The service only knows it as CustomerRepository.
    auth_service = AuthService(customer_repo)

    # Injected into the routes. The routes only know it as AuthService.
    app.register_blueprint(create_auth_routes(auth_service))
```

This is the only file in the project that imports SqliteCustomerRepository.
To swap to a different database, change this one line and nothing else needs
to change.

---

## Pattern 6: Factory Function

A factory function creates and returns an object rather than letting the
caller construct it directly. Routes use this pattern so that services can
be injected into them.

```python
# src/presentation/routes/auth_routes.py
def create_auth_routes(auth_service):
    auth = Blueprint('auth', __name__)

    @auth.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            try:
                auth_service.register(
                    first_name=request.form.get('first_name'),
                    last_name=request.form.get('last_name'),
                    email=request.form.get('email'),
                    password=request.form.get('password'),
                    phone_number=request.form.get('phone_number') or None
                )
                flash('Registration successful. Please log in.', 'success')
                return redirect(url_for('auth.login'))
            except ValueError as e:
                flash(str(e), 'error')
        return render_template('register.html')

    return auth
```

The route does not import the service directly. It receives it as an argument
from app.py. The route only handles HTTP concerns: reading the form, calling
the service, and returning a response.

---

## Applying This to a New Feature

When adding a new feature, follow this order:

1. Add the model to src/domain/models/ if a new entity is needed
2. Add the abstract repository to src/domain/repositories/ if new data
   operations are needed
3. Add the concrete repository to src/data/repositories/ implementing the
   abstract class
4. Add or update the service in src/domain/services/ with the business logic
5. Update the route in src/presentation/routes/ to call the service
6. Wire it in app.py by instantiating the repository and injecting it

Never skip a layer. Never import a concrete repository from a service. Never
import a model or repository from a route. If import-linter blocks your
commit, check which layer boundary you have crossed and move the import to
the correct file.
