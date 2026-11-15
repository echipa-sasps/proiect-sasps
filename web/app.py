import secrets
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

from baseline.catalog import BaselineCatalog
from catalog.contract import CatalogError


def create_app(database: Path, *, catalog_factory=BaselineCatalog) -> Flask:
    app = Flask(__name__)
    app.config.update(SECRET_KEY=secrets.token_hex(32), MAX_CONTENT_LENGTH=16_384)
    # O instanta comuna permite ulterior refolosirea aceluiasi cache intre cereri.
    app.extensions["catalog"] = catalog_factory(Path(database))

    def catalog():
        return app.extensions["catalog"]

    @app.context_processor
    def template_context():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(32)
        return {"csrf_token": session["csrf_token"]}

    @app.get("/")
    def index():
        query = request.args.get("q", "").strip()
        status = request.args.get("status", "all")
        if status not in {"all", "available", "borrowed"}:
            status = "all"
        try:
            page = max(1, int(request.args.get("page", "1")))
        except ValueError:
            page = 1
        books = catalog().search_books(query) if query else catalog().list_books()
        total = len(books)
        available = sum(book.available for book in books)
        if status != "all":
            books = [book for book in books if book.available == (status == "available")]
        count = len(books)
        pages = max(1, (count + 7) // 8)
        page = min(page, pages)
        start = (page - 1) * 8
        return render_template(
            "index.html", books=books[start:start + 8], query=query, status=status,
            total=total, available=available, count=count, page=page, pages=pages,
            start=start + 1 if count else 0, end=min(start + 8, count),
        )

    @app.get("/carti/<int:book_id>")
    def detail(book_id):
        book = catalog().get_book(book_id)
        if book is None:
            abort(404)
        return render_template("detail.html", book=book)

    @app.post("/carti/<int:book_id>/<action>")
    def change_status(book_id, action):
        token = session.get("csrf_token")
        if not token or not secrets.compare_digest(token, request.form.get("csrf_token", "")):
            abort(400)
        if action not in {"imprumuta", "returneaza"}:
            abort(404)
        try:
            operation = catalog().borrow_book if action == "imprumuta" else catalog().return_book
            operation(book_id)
            flash("Cartea a fost împrumutată." if action == "imprumuta"
                  else "Cartea a fost returnată. Mulțumim!", "success")
        except CatalogError:
            flash("Operația nu a putut fi efectuată. Verifică disponibilitatea cărții.", "error")
        if request.form.get("view") == "detail":
            return redirect(url_for("detail", book_id=book_id), code=303)
        # Redirectul este construit intern, pastrand cautarea si pagina curente.
        return redirect(url_for("index", q=request.form.get("q", ""),
                                status=request.form.get("status", "all"),
                                page=request.form.get("page", "1")), code=303)

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", code=404,
                               message="Pagina căutată nu se află în catalog."), 404

    @app.errorhandler(400)
    def invalid_request(error):
        return render_template("error.html", code=400,
                               message="Formularul a expirat. Reîncarcă pagina și încearcă din nou."), 400

    return app
