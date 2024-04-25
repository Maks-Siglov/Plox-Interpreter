from typing import TYPE_CHECKING

from plox_token import Token

if TYPE_CHECKING:
    from plox_class import LoxClass


class LoxInstance:
    def __init__(self, klass: "LoxClass"):
        self.klass = klass
        self.fields = {}

    def get(self, name: Token):
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]

        method = self.klass.get_method(name.lexeme)
        if method is not None:
            return method.bind(self)

        raise RuntimeError(name, f"Undefined property '{name.lexeme}'.")

    def set(self, name: Token, value: Token):
        self.fields[name.lexeme] = value

    def __str__(self):
        return f"{self.klass.name} instance"