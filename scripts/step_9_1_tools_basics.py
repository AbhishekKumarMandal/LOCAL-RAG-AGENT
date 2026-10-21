def calculator(operation, a, b):
    """
    Simple calculator tool.

    operation:
        add
        subtract
        multiply
        divide
    """

    if operation == "add":
        return a + b

    if operation == "subtract":
        return a - b

    if operation == "multiply":
        return a * b

    if operation == "divide":

        if b == 0:
            raise ValueError(
                "Cannot divide by zero"
            )

        return a / b

    raise ValueError(
        f"Unsupported operation: {operation}"
    )


if __name__ == "__main__":

    result = calculator(
        operation="multiply",
        a=17,
        b=23
    )

    print("Result:", result)