from dataclasses import dataclass
from typing import Optional


@dataclass
class Book:
    """Represents a book in the catalogue.

    Attributes:
        id: ISBN — primary identifier used throughout the app
        title: Book title
        author: Author name
        genre: Genre category
        description: Book description
        price: Sale price
        stock: Units available
        cover_url: URL to cached cover image, or None if not cached
    """

    id: str
    title: str = ""
    author: str = ""
    genre: str = "General"
    description: str = ""
    price: float = 0.0
    stock: int = 0
    cover_url: Optional[str] = None

    @property
    def isbn(self) -> str:
        return self.id
