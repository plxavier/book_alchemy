from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Author(db.Model):
    __tablename__ = 'authors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    birth_year = db.Column(db.Integer)
    death_year = db.Column(db.Integer)
    nationality = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with books
    books = db.relationship('Book', backref='author', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Author {self.name}>'

    def to_dict(self):
        try:
            return {
                'id': self.id,
                'name': self.name,
                'birth_year': self.birth_year,
                'death_year': self.death_year,
                'nationality': self.nationality,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'book_count': len(self.books)
            }
        except Exception as error:
            print(f"Error converting Author to dict: {error}")
            return {}


class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(20), unique=True)
    publication_year = db.Column(db.Integer)
    genre = db.Column(db.String(50))
    pages = db.Column(db.Integer)
    read_status = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Integer)  # 1-5
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign key to Author
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), nullable=False)

    def __repr__(self):
        return f'<Book {self.title}>'

    def to_dict(self):
        try:
            return {
                'id': self.id,
                'title': self.title,
                'isbn': self.isbn,
                'publication_year': self.publication_year,
                'genre': self.genre,
                'pages': self.pages,
                'read_status': self.read_status,
                'rating': self.rating,
                'notes': self.notes,
                'author_id': self.author_id,
                'author_name': self.author.name if self.author else None,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }
        except Exception as error:
            print(f"Error converting Book to dict: {error}")
            return {}