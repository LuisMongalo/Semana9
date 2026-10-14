
import os

from flask import Flask, flash, redirect, render_template, request, session, url_for


class Stack:
    """Implementa una pila limitada con comportamiento LIFO."""

    def __init__(self, capacity: int, items: list[str] | None = None):
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
            raise ValueError("La capacidad debe ser un entero positivo.")

        self.capacity = capacity
        self._items = list(items) if items is not None else []

        if len(self._items) > self.capacity:
            raise ValueError("Los elementos superan la capacidad de la pila.")

    @property
    def items(self) -> list[str]:
        """Devuelve una copia de los elementos."""
        return self._items.copy()

    @property
    def size(self) -> int:
        return len(self._items)

    @property
    def is_empty(self) -> bool:
        return not self._items

    @property
    def is_full(self) -> bool:
        return self.size >= self.capacity

    @property
    def top(self) -> str | None:
        return self._items[-1] if self._items else None

    def push(self, item: str) -> None:
        if self.is_full:
            raise OverflowError("La pila está llena.")

        if not isinstance(item, str) or not item.strip():
            raise ValueError("El elemento no puede estar vacío.")

        self._items.append(item.strip())

    def pop(self) -> str:
        if self.is_empty:
            raise IndexError("La pila está vacía.")

        return self._items.pop()

    def clear(self) -> None:
        self._items.clear()


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me")


DEFAULT_CAPACITY = 5
MAX_CAPACITY = 100
MAX_ITEM_LENGTH = 100


def get_stack() -> Stack:
    """Reconstruye la pila a partir de la sesión del usuario."""
    capacity = session.get("capacity", DEFAULT_CAPACITY)
    items = session.get("items", [])

    return Stack(capacity=capacity, items=items)


def save_stack(stack: Stack) -> None:
    """Guarda el estado de la pila en la sesión."""
    session["capacity"] = stack.capacity
    session["items"] = stack.items


@app.get("/")
def index():
    stack = get_stack()

    return render_template(
        "index.html",
        items=list(reversed(stack.items)),
        size=stack.size,
        capacity=stack.capacity,
        top=stack.top,
        is_empty=stack.is_empty,
        is_full=stack.is_full,
    )


@app.post("/configure")
def configure():
    try:
        capacity = int(request.form.get("capacity", ""))
    except (TypeError, ValueError):
        flash("Introduce una capacidad numérica válida.", "danger")
        return redirect(url_for("index"))

    if not 1 <= capacity <= MAX_CAPACITY:
        flash(
            f"La capacidad debe estar entre 1 y {MAX_CAPACITY}.",
            "danger",
        )
        return redirect(url_for("index"))

    stack = get_stack()

    if capacity < stack.size:
        flash(
            "La capacidad no puede ser menor que los elementos actuales.",
            "warning",
        )
        return redirect(url_for("index"))

    stack.capacity = capacity
    save_stack(stack)
    flash("Capacidad actualizada correctamente.", "success")

    return redirect(url_for("index"))


@app.post("/push")
def push():
    stack = get_stack()
    item = request.form.get("item", "").strip()

    if len(item) > MAX_ITEM_LENGTH:
        flash(
            f"El elemento no puede superar {MAX_ITEM_LENGTH} caracteres.",
            "danger",
        )
        return redirect(url_for("index"))

    try:
        stack.push(item)
    except (ValueError, OverflowError) as error:
        flash(str(error), "danger")
    else:
        save_stack(stack)
        flash(f"Elemento «{item}» apilado correctamente.", "success")

    return redirect(url_for("index"))


@app.post("/pop")
def pop():
    stack = get_stack()

    try:
        item = stack.pop()
    except IndexError as error:
        flash(str(error), "warning")
    else:
        save_stack(stack)
        flash(f"Elemento desapilado: {item}", "success")

    return redirect(url_for("index"))


@app.post("/peek")
def peek():
    stack = get_stack()

    if stack.is_empty:
        flash("La pila está vacía; no hay un tope que consultar.", "warning")
    else:
        flash(f"El elemento del tope es: {stack.top}", "info")

    return redirect(url_for("index"))


@app.post("/clear")
def clear():
    stack = get_stack()
    stack.clear()
    save_stack(stack)
    flash("La pila se ha vaciado correctamente.", "success")

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")