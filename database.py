import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data.json')


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


def load_data():
	if not os.path.exists(DATA_PATH):
		return {'books': []}

	try:
		with open(DATA_PATH, 'r', encoding='utf-8') as handle:
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


def load_books():
	data = load_data()
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
