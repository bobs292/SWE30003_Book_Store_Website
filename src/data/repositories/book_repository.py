import json
import os

from src.domain.repositories.book_repository import BookRepository


def _coerce_int(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def _coerce_float(value, default=0.0):
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


class JsonBookRepository(BookRepository):
	def __init__(self, data_path=None):
		base_dir = os.path.dirname(__file__)
		default_path = os.path.normpath(os.path.join(base_dir, '..', 'seeds', 'data.json'))
		self._data_path = data_path or default_path

	def _load_raw(self):
		if not os.path.exists(self._data_path):
			return {'books': []}

		try:
			with open(self._data_path, 'r', encoding='utf-8') as handle:
				raw = handle.read().strip()
		except OSError:
			return {'books': []}

		if not raw:
			return {'books': []}

		try:
			data = json.loads(raw)
		except json.JSONDecodeError:
			return {'books': []}

		if isinstance(data, dict):
			return data
		if isinstance(data, list):
			return {'books': data}

		return {'books': []}

	def list_books(self):
		data = self._load_raw()
		books = data.get('books', [])
		normalized = []

		for index, book in enumerate(books, start=1):
			if not isinstance(book, dict):
				continue
			normalized.append({
				'id': _coerce_int(book.get('id', index), index),
				'title': str(book.get('title', f'Book {index}')),
				'author': str(book.get('author', 'Unknown')),
				'genre': str(book.get('genre') or 'General'),
				'description': str(book.get('description') or ''),
				'cover_color': str(book.get('cover_color') or '#d6cbb8'),
				'price': round(_coerce_float(book.get('price', 0.0), 0.0), 2),
				'stock': max(_coerce_int(book.get('stock', 0), 0), 0),
			})

		return normalized

	def get_by_id(self, book_id):
		target = str(book_id)
		for book in self.list_books():
			if str(book.get('id')) == target:
				return book
		return None
