class Stmt:
    """
    Program -> Declaration * EOF ;
    Declaration -> VarDecl | Statement :
    VarDecl -> "var" IDENTIFIER ( "=" expression )? ";" ;
    Statement -> ExprStmt | PrintStmt ;
    ExprStmt -> expression ";" ;
    PrintStmt -> "print" expression ";" ;
    """

    def accept(self, visitor):
        raise NotImplementedError(
            "accept method must be implemented by Expr subclasses"
        )


class Print(Stmt):
    def __init__(self, expr):
        self.expr = expr

    def accept(self, visitor):
        return visitor.visit_print_stmt(self)


class Expression(Stmt):
    def __init__(self, expr):
        self.expr = expr

    def accept(self, visitor):
        return visitor.visit_expression_stmt(self)


class Var(Stmt):
    def __init__(self, name, initializer):
        self.name = name
        self.initializer = initializer

    def accept(self, visitor):
        return visitor.visit_var_stmt(self)
