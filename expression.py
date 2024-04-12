class Expr:
    """
    Expression -> Equality ;
    Equality -> Comparison ( ( "!=" | "==" ) Comparison )* ;
    Comparison → Term ( ( ">" | ">=" | "<" | "<=" ) Term )* ;
    Term → Factor ( ( "-" | "+" ) Factor )* ;
    Factor → Unary ( ( "/" | "*" ) Unary )* ;
    Unary -> ("!" | "-")Unary | Primary;
    Primary → NUMBER | STRING | "true" | "false" | "nil" | "(" expression ")" ;
    """

    pass


class Binary(Expr):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right


class Unary(Expr):
    def __init__(self, operator, right):
        self.operator = operator
        self.right = right


class Literal(Expr):
    def __init__(self, value):
        self.value = value


class Grouping(Expr):
    def __init__(self, expr):
        self.expr = expr
