import os
import secrets
from pathlib import Path
from uuid import uuid4

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from PIL import Image, UnidentifiedImageError
from werkzeug.exceptions import RequestEntityTooLarge

from templates.stack import is_empty, is_full, push, peek, pop_stack, show


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"

DEFAULT_CAPACITY = 10
MAX_CAPACITY = 30
MAX_FILE_SIZE = 5 * 1024 * 1024

ALLOWED_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}

app = Flask(__name__)

app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY"),
    MAX_CONTENT_LENGTH=MAX_FILE_SIZE,
)

if not app.config["SECRET_KEY"]:
    raise RuntimeError(
        "Define la variable de entorno FLASK_SECRET_KEY antes de ejecutar Flask."
    )

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


def get_stack():
    """Obtiene una copia de la pila de la sesión actual."""
    return list(session.get("photo_stack", []))


def get_capacity():
    """Obtiene la capacidad configurada."""
    capacity = session.get("capacity", DEFAULT_CAPACITY)

    if (
        isinstance(capacity, bool)
        or not isinstance(capacity, int)
        or not 1 <= capacity <= MAX_CAPACITY
    ):
        return DEFAULT_CAPACITY

    return capacity


def validate_image(file_storage):
    """Valida el contenido real de una imagen."""
    file_storage.stream.seek(0)

    with Image.open(file_storage.stream) as image:
        image_format = image.format

        if image_format not in ALLOWED_FORMATS:
            raise ValueError("Formato no permitido. Usa JPG, PNG o WebP.")

        image.verify()

    file_storage.stream.seek(0)
    return ALLOWED_FORMATS[image_format]


def save_photo(file_storage, stack, capacity):
    """Valida y guarda una foto, añadiéndola a la pila."""
    if not file_storage or not file_storage.filename:
        raise ValueError("Selecciona una fotografía.")

    if is_full(stack, capacity):
        raise ValueError("La pila está llena.")

    filename = None

    try:
        extension = validate_image(file_storage)
        filename = f"{uuid4().hex}{extension}"
        destination = UPLOAD_FOLDER / filename

        file_storage.save(destination)

        if not push(stack, filename, capacity):
            destination.unlink(missing_ok=True)
            raise ValueError("La pila está llena.")

        session["photo_stack"] = stack
        return filename

    except (UnidentifiedImageError, OSError) as error:
        if filename:
            (UPLOAD_FOLDER / filename).unlink(missing_ok=True)

        raise ValueError("El archivo no es una imagen válida.") from error


@app.route("/")
def index():
    stack = get_stack()
    capacity = get_capacity()

    photos = [
        {
            "filename": filename,
            "url": url_for("static", filename=f"uploads/{filename}"),
        }
        for filename in show(stack)
    ]

    return render_template(
        "index.html",
        photos=photos,
        count=len(stack),
        capacity=capacity,
        top=peek(stack),
        is_empty=is_empty(stack),
        is_full=is_full(stack, capacity),
    )


@app.route("/upload", methods=["POST"])
def upload():
    stack = get_stack()
    capacity = get_capacity()

    files = request.files.getlist("photos")

    # También acepta una foto enviada desde la cámara mediante JavaScript.
    if request.files.get("photo"):
        files = [request.files["photo"]]

    files = [photo for photo in files if photo and photo.filename]

    if not files:
        message = "Selecciona o captura una fotografía."
        if request.is_json or request.headers.get("X-Requested-With") == "fetch":
            return jsonify(error=message), 400

        flash(message, "warning")
        return redirect(url_for("index"))

    saved = []

    try:
        for photo in files:
            filename = save_photo(photo, stack, capacity)
            saved.append(filename)

    except ValueError as error:
        for filename in saved:
            (UPLOAD_FOLDER / filename).unlink(missing_ok=True)

        # No conserves una pila parcialmente actualizada.
        session["photo_stack"] = [
            name for name in stack if name not in saved
        ]

        message = str(error)

        if request.headers.get("X-Requested-With") == "fetch":
            return jsonify(error=message), 400

        flash(message, "warning")
        return redirect(url_for("index"))

    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify(message="Fotografía agregada a la pila.")

    flash(f"Se agregaron {len(saved)} fotografía(s).", "success")
    return redirect(url_for("index"))


@app.route("/pop", methods=["POST"])
def pop():
    stack = get_stack()
    filename = pop_stack(stack)

    if filename is None:
        flash("La pila está vacía.", "warning")
    else:
        session["photo_stack"] = stack
        (UPLOAD_FOLDER / filename).unlink(missing_ok=True)
        flash("Se retiró la fotografía del tope.", "success")

    return redirect(url_for("index"))


@app.route("/peek", methods=["POST"])
def peek_photo():
    filename = peek(get_stack())

    if filename is None:
        flash("La pila está vacía.", "warning")
    else:
        flash(f"Foto del tope: {filename[:8]}…", "info")

    return redirect(url_for("index"))


@app.route("/clear", methods=["POST"])
def clear():
    stack = get_stack()

    for filename in stack:
        (UPLOAD_FOLDER / filename).unlink(missing_ok=True)

    session["photo_stack"] = []
    flash("Se retiraron todas las fotografías.", "info")

    return redirect(url_for("index"))


@app.errorhandler(RequestEntityTooLarge)
def file_too_large(_error):
    message = "La solicitud supera el límite de 5 MB."

    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify(error=message), 413

    flash(message, "warning")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)