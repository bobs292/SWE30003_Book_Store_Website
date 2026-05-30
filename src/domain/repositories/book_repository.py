from abc import ABC, abstractmethod


class BookRepository(ABC):
	@abstractmethod
	def list_books(self):
		raise NotImplementedError

	@abstractmethod
	def get_by_id(self, book_id):
		raise NotImplementedError
