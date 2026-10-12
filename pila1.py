stack = []


def push(item, capacity):
    if not is_full(capacity):
        stack.append(item)
        return "Elemento apilado..."
    return "La pila está llena..."

def isEmpty():
    return not len(stack)

def is_full(capacity):
    return len(stack) == capacity

def main():
    capacity = int(input("Dime el tamaño de la pila:"))
    
def peek():
    if not isEmpty():
        return stack[-1]
    return "La pila está vacía..."

def pop_stack():
    if not isEmpty():
        return stack.pop()
    return "La pila está vacía..."

def show_stack():
    message = ""
    for item in reversed(stack):
        message += f"|{item :>6} |\n"
        message += f""
    return message

capacity = int(input("Dime el tamaño de la pila:"))
while True:
    item = input("Dime el valor")
    print(push(item, capacity))
    answer = input("Desea ingresar otro dato [S / N]: ")
    if answer.lower() == "n":
        break
    
print("Mostrar tope")
print(peek())
print(peek())

while True:
    answer = input("Desea sacar un dato [S | N]: ")
    if answer.lower() == "s":
        print(pop_stack())
    elif answer.lower() == "n":
        break
    else:
        print("opcion no valida...")