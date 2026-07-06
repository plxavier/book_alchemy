from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_migrate import Migrate
from data_models import db, Author, Book
import sys
import logging
import os

# ========== LOGGING ==========
try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)
except Exception as error:
    print(f"Error configuring logging: {error}")
    sys.exit(1)

# ========== APP CREATION ==========
try:
    app = Flask(__name__)

    # Create data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')
        print("✅ Created data/ folder")

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/library.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'book-alchemy-secret-key'

    db.init_app(app)
    migrate = Migrate(app, db)

    logger.info("Book Alchemy - Flask application created successfully")
    print("✅ Flask application created successfully")
except Exception as error:
    logger.error(f"Error creating Flask application: {error}")
    print(f"❌ Error creating Flask application: {error}")
    sys.exit(1)


# ========== DATABASE INITIALIZATION ==========
def init_db():
    """Create database tables if they don't exist."""
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully")
            print("✅ Database tables created successfully")
    except Exception as error:
        logger.error(f"Error initializing database: {error}")
        print(f"❌ Error initializing database: {error}")


# ========== ROUTES ==========

@app.route('/')
def index():
    """Home page - display library statistics."""
    try:
        total_books = Book.query.count()
        total_authors = Author.query.count()
        unread_books = Book.query.filter_by(read_status=False).count()
        recent_books = Book.query.order_by(Book.created_at.desc()).limit(5).all()

        return render_template('index.html',
                               total_books=total_books,
                               total_authors=total_authors,
                               unread_books=unread_books,
                               recent_books=recent_books)
    except Exception as error:
        logger.error(f"Error in index: {error}")
        return render_template('index.html', error=str(error))


# ========== BOOK ROUTES ==========

@app.route('/books')
def books():
    """List all books with search and sorting."""
    try:
        search_query = request.args.get('search', '').strip()
        sort_by = request.args.get('sort', 'title')

        query = Book.query

        if search_query:
            query = query.filter(
                Book.title.ilike(f'%{search_query}%') |
                Book.author.has(Author.name.ilike(f'%{search_query}%'))
            )

        if sort_by == 'title':
            query = query.order_by(Book.title)
        elif sort_by == 'author':
            query = query.order_by(Author.name).join(Author)
        elif sort_by == 'rating':
            query = query.order_by(Book.rating.desc())
        elif sort_by == 'year':
            query = query.order_by(Book.publication_year.desc())
        else:
            query = query.order_by(Book.title)

        all_books = query.all()

        return render_template('books.html',
                               books=all_books,
                               search_query=search_query,
                               sort_by=sort_by)
    except Exception as error:
        logger.error(f"Error in books: {error}")
        flash(f"Error loading books: {error}", 'error')
        return render_template('books.html', books=[])


@app.route('/book/<int:book_id>')
def book_detail(book_id):
    """View a single book's details."""
    try:
        book = Book.query.get_or_404(book_id)
        return render_template('book_detail.html', book=book)
    except Exception as error:
        logger.error(f"Error in book_detail: {error}")
        flash(f"Error loading book: {error}", 'error')
        return redirect(url_for('books'))


@app.route('/book/add', methods=['GET', 'POST'])
def add_book():
    """Add a new book."""
    try:
        authors = Author.query.order_by(Author.name).all()

        if request.method == 'POST':
            try:
                title = request.form.get('title', '').strip()
                author_id = request.form.get('author_id')
                isbn = request.form.get('isbn', '').strip()
                publication_year = request.form.get('publication_year')
                genre = request.form.get('genre', '').strip()
                pages = request.form.get('pages')
                read_status = request.form.get('read_status') == 'on'
                rating = request.form.get('rating')
                notes = request.form.get('notes', '').strip()

                if not title:
                    flash('Book title is required!', 'error')
                    return render_template('add_book.html', authors=authors)

                if not author_id:
                    flash('Please select an author!', 'error')
                    return render_template('add_book.html', authors=authors)

                try:
                    author_id = int(author_id)
                except ValueError:
                    flash('Invalid author selection!', 'error')
                    return render_template('add_book.html', authors=authors)

                author = Author.query.get(author_id)
                if not author:
                    flash('Selected author not found!', 'error')
                    return render_template('add_book.html', authors=authors)

                new_book = Book(
                    title=title,
                    author_id=author_id,
                    isbn=isbn if isbn else None,
                    publication_year=int(publication_year) if publication_year and publication_year.isdigit() else None,
                    genre=genre if genre else None,
                    pages=int(pages) if pages and pages.isdigit() else None,
                    read_status=read_status,
                    rating=int(rating) if rating and rating.isdigit() and 1 <= int(rating) <= 5 else None,
                    notes=notes if notes else None
                )

                db.session.add(new_book)
                db.session.commit()
                flash(f'📖 Book "{title}" added successfully!', 'success')
                return redirect(url_for('books'))

            except Exception as error:
                db.session.rollback()
                logger.error(f"Error adding book: {error}")
                flash(f'Error adding book: {error}', 'error')
                return render_template('add_book.html', authors=authors)

        return render_template('add_book.html', authors=authors)
    except Exception as error:
        logger.error(f"Error in add_book GET: {error}")
        flash(f'Error loading page: {error}', 'error')
        return redirect(url_for('books'))


@app.route('/book/<int:book_id>/edit', methods=['GET', 'POST'])
def edit_book(book_id):
    """Edit a book."""
    try:
        book = Book.query.get_or_404(book_id)
        authors = Author.query.order_by(Author.name).all()

        if request.method == 'POST':
            try:
                book.title = request.form.get('title', '').strip()
                book.author_id = int(request.form.get('author_id'))
                book.isbn = request.form.get('isbn', '').strip()
                book.publication_year = int(request.form.get('publication_year')) if request.form.get(
                    'publication_year') and request.form.get('publication_year').isdigit() else None
                book.genre = request.form.get('genre', '').strip()
                book.pages = int(request.form.get('pages')) if request.form.get('pages') and request.form.get(
                    'pages').isdigit() else None
                book.read_status = request.form.get('read_status') == 'on'
                book.rating = int(request.form.get('rating')) if request.form.get('rating') and request.form.get(
                    'rating').isdigit() and 1 <= int(request.form.get('rating')) <= 5 else None
                book.notes = request.form.get('notes', '').strip()

                db.session.commit()
                flash('✅ Book updated successfully!', 'success')
                return redirect(url_for('book_detail', book_id=book.id))

            except Exception as error:
                db.session.rollback()
                logger.error(f"Error updating book: {error}")
                flash(f'Error updating book: {error}', 'error')

        return render_template('edit_book.html', book=book, authors=authors)
    except Exception as error:
        logger.error(f"Error in edit_book: {error}")
        flash(f'Error loading page: {error}', 'error')
        return redirect(url_for('books'))


@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    """Delete a book."""
    try:
        book = Book.query.get_or_404(book_id)
        author = book.author
        title = book.title

        db.session.delete(book)
        db.session.commit()

        remaining_books = Book.query.filter_by(author_id=author.id).count()
        if remaining_books == 0:
            flash(f'📖 "{title}" deleted. Author "{author.name}" has no more books.', 'info')
        else:
            flash(f'✅ "{title}" deleted successfully!', 'success')

    except Exception as error:
        db.session.rollback()
        logger.error(f"Error deleting book: {error}")
        flash(f'Error deleting book: {error}', 'error')

    return redirect(url_for('books'))


# ========== AUTHOR ROUTES ==========

@app.route('/authors')
def authors():
    """List all authors."""
    try:
        all_authors = Author.query.order_by(Author.name).all()
        return render_template('authors.html', authors=all_authors)
    except Exception as error:
        logger.error(f"Error in authors: {error}")
        flash(f"Error loading authors: {error}", 'error')
        return render_template('authors.html', authors=[])


@app.route('/author/add', methods=['GET', 'POST'])
def add_author():
    """Add a new author."""
    try:
        if request.method == 'POST':
            try:
                name = request.form.get('name', '').strip()
                birth_year = request.form.get('birth_year')
                death_year = request.form.get('death_year')
                nationality = request.form.get('nationality', '').strip()

                if not name:
                    flash('Author name is required!', 'error')
                    return render_template('add_author.html')

                new_author = Author(
                    name=name,
                    birth_year=int(birth_year) if birth_year and birth_year.isdigit() else None,
                    death_year=int(death_year) if death_year and death_year.isdigit() else None,
                    nationality=nationality if nationality else None
                )

                db.session.add(new_author)
                db.session.commit()
                flash(f'✍️ Author "{name}" added successfully!', 'success')
                return redirect(url_for('authors'))

            except Exception as error:
                db.session.rollback()
                logger.error(f"Error adding author: {error}")
                flash(f'Error adding author: {error}', 'error')
                return render_template('add_author.html')

        return render_template('add_author.html')
    except Exception as error:
        logger.error(f"Error in add_author GET: {error}")
        flash(f'Error loading page: {error}', 'error')
        return redirect(url_for('authors'))


# ========== API ENDPOINTS ==========

@app.route('/api/books')
def api_books():
    """API endpoint for books."""
    try:
        books = Book.query.all()
        return jsonify([book.to_dict() for book in books])
    except Exception as error:
        logger.error(f"Error in api_books: {error}")
        return jsonify({'error': str(error)}), 500


@app.route('/api/authors')
def api_authors():
    """API endpoint for authors."""
    try:
        authors = Author.query.all()
        return jsonify([author.to_dict() for author in authors])
    except Exception as error:
        logger.error(f"Error in api_authors: {error}")
        return jsonify({'error': str(error)}), 500


# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 error: {request.url}")
    return render_template('error.html',
                           error_code=404,
                           error_message="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    db.session.rollback()
    return render_template('error.html',
                           error_code=500,
                           error_message="Internal server error"), 500


# ========== MAIN ==========
if __name__ == '__main__':
    try:
        print("\n" + "=" * 50)
        print("📚 Book Alchemy - Digital Library")
        print("📍 Running on http://127.0.0.1:5000")
        print("=" * 50 + "\n")

        init_db()

        app.run(host="0.0.0.0", port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user.")
        logger.info("Server stopped by user")
    except Exception as error:
        print(f"❌ Error starting server: {error}")
        logger.error(f"Error starting server: {error}")
        sys.exit(1)