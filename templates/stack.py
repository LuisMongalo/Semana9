def is_empty(stack):
    """Comprueba si la pila está vacía."""
    return len(stack) == 0


def is_full(stack, capacity):
    """Comprueba si la pila alcanzó su capacidad máxima."""
    return len(stack) >= capacity


def push(stack, item, capacity):
    """Agrega un elemento si existe espacio."""
    if is_full(stack, capacity):
        return False

    stack.append(item)
    return True


def peek(stack):
    """Consulta el elemento del tope sin retirarlo."""
    if is_empty(stack):
        return None

    return stack[-1]


def pop_stack(stack):
    """Retira y devuelve el elemento del tope."""
    if is_empty(stack):
        return None

    return stack.pop()


def show(stack):
    """Devuelve los elementos desde el tope hasta la base."""
    return list(reversed(stack))