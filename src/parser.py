import expr
import stmt
from exceptions import ParserError
from plox_token import Token
from token_type import TokenType


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> list[stmt.Stmt]:
        statements = []
        while not self.is_at_end():
            statements.append(self.declaration())
        return statements

    def declaration(self):
        if self.match(TokenType.CLASS):
            return self.class_declaration()
        if self.match(TokenType.FUN):
            return self.fun_declaration("function")
        if self.match(TokenType.VAR):
            return self.var_declaration()
        return self.statement()

    def class_declaration(self) -> stmt.Stmt:
        name = self.consume(TokenType.IDENTIFIER, "Expect class name.")

        superclass = None
        if self.match(TokenType.LESS):
            superclass_token = self.consume(
                TokenType.IDENTIFIER, "Expect superclass name."
            )
            superclass = expr.Var(token=superclass_token)

        self.consume(TokenType.LEFT_BRACE, "Expect '{' before class body.")

        methods = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            methods.append(self.fun_declaration("method"))

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after class body.")

        return stmt.Class(name, superclass, methods)

    def fun_declaration(self, kind: str) -> stmt.Function:
        name = self.consume(TokenType.IDENTIFIER, f"Expect {kind} name")

        self.consume(TokenType.LEFT_PAREN, "Expect '(' for fun arguments")

        parameters = []
        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                parameter = self.consume(
                    TokenType.IDENTIFIER, "Expect parameter name."
                )
                parameters.append(parameter)

                if len(parameters) >= 255:
                    self.error(
                        self.peek(), "Can't have more than 255 arguments."
                    )

                if not self.match(TokenType.COMMA):
                    break

        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")

        self.consume(
            TokenType.LEFT_BRACE, "Expect '{' before " + kind + " body."
        )
        body = self.block_statement()
        return stmt.Function(name, parameters, body.statements)

    def var_declaration(self) -> stmt.Var:
        token = self.consume(TokenType.IDENTIFIER, "Expect variable name.")

        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return stmt.Var(token, initializer)

    def statement(self) -> stmt.Stmt:
        if self.match(TokenType.PRINT):
            return self.print_statement()
        elif self.match(TokenType.RETURN):
            return self.return_statement()
        elif self.match(TokenType.WHILE):
            return self.while_statement()
        elif self.match(TokenType.FOR):
            return self.for_statement()
        elif self.match(TokenType.LEFT_BRACE):
            return self.block_statement()
        elif self.match(TokenType.IF):
            return self.if_statement()
        return self.expression_statement()

    def print_statement(self) -> stmt.Print:
        value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return stmt.Print(value)

    def return_statement(self):
        keyword = self.previous()
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return stmt.Return(keyword, value)

    def block_statement(self):
        statements = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())
        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return stmt.Block(statements)

    def if_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after 'if'.")

        then_branch = self.statement()
        else_branch = None
        if self.match(TokenType.ELSE):
            else_branch = self.statement()

        return stmt.IfStmt(condition, then_branch, else_branch)

    def while_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after 'if'.")
        body = self.statement()

        return stmt.While(condition, body)

    def for_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")

        if self.match(TokenType.SEMICOLON):
            initializer = None
        elif self.match(TokenType.VAR):
            initializer = self.var_declaration()
        else:
            initializer = self.expression_statement()

        condition = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        increment = None
        if not self.check(TokenType.RIGHT_PAREN):
            increment = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")

        body = self.statement()

        if increment is not None:
            body = stmt.Block([body, stmt.Expression(increment)])

        if condition is None:
            condition = expr.Literal(True)
        body = stmt.While(condition, body)

        if initializer is not None:
            body = stmt.Block([initializer, body])

        return body

    def expression_statement(self) -> stmt.Expression:
        expression = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return stmt.Expression(expression)

    def expression(self) -> expr.Expr:
        return self.assigment()

    def assigment(self) -> expr.Expr:
        expression = self.or_condition()

        if self.match(TokenType.EQUAL):
            value = self.assigment()

            if isinstance(expression, expr.Var):
                token = expression.token
                return expr.Assign(token, value)
            elif isinstance(expression, expr.Get):
                get = expression
                return expr.Set(get.expression, get.name, value)

            raise ParserError(f"Invalid assigment target: {type(expression)}")

        return expression

    def or_condition(self) -> expr.Expr:
        expression = self.and_condition()

        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.and_condition()
            expression = expr.Logical(expression, operator, right)

        return expression

    def and_condition(self) -> expr.Expr:
        expression = self.equality()

        while self.match(TokenType.AND):
            operator = self.previous()
            right = self.equality()
            expression = expr.Logical(expression, operator, right)

        return expression

    def equality(self) -> expr.Expr:
        expression = self.comparison()

        while self.list_match([TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL]):
            operator = self.previous()
            right = self.comparison()
            expression = expr.Binary(expression, operator, right)
        return expression

    def comparison(self) -> expr.Expr:
        expression = self.term()

        comparison_types = [
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ]

        while self.list_match(comparison_types):
            operator = self.previous()
            right = self.term()
            expression = expr.Binary(expression, operator, right)

        return expression

    def term(self) -> expr.Expr:
        expression = self.factor()

        while self.list_match([TokenType.MINUS, TokenType.PLUS]):
            operator = self.previous()
            right = self.factor()
            expression = expr.Binary(expression, operator, right)

        return expression

    def factor(self) -> expr.Expr:
        expression = self.unary()

        while self.list_match([TokenType.SLASH, TokenType.STAR]):
            operator = self.previous()
            right = self.unary()
            expression = expr.Binary(expression, operator, right)

        return expression

    def unary(self) -> expr.Expr:
        if self.list_match([TokenType.BANG, TokenType.MINUS]):
            operator = self.previous()
            right = self.unary()
            return expr.Unary(operator, right)

        return self.call()

    def call(self) -> expr.Expr:
        expression = self.primary()

        while True:
            if self.match(TokenType.LEFT_PAREN):
                expression = self.finish_call(expression)
            elif self.match(TokenType.DOT):
                name = self.consume(
                    TokenType.IDENTIFIER, "Expect property name after '.'."
                )
                expression = expr.Get(expression, name)
            else:
                break

        return expression

    def finish_call(self, callee: expr.Expr) -> expr.Expr:
        arguments = []
        if not self.check(TokenType.RIGHT_PAREN):

            while True:
                arguments.append(self.expression())
                if not self.match(TokenType.COMMA):
                    break
                if len(arguments) >= 255:
                    self.error(
                        self.peek(), "Can't have more than 255 arguments."
                    )

        paren = self.consume(
            TokenType.RIGHT_PAREN, "Expect ')' after arguments."
        )
        return expr.Call(callee, paren, arguments)

    def primary(self) -> expr.Expr:
        if self.match(TokenType.FALSE):
            return expr.Literal(False)
        elif self.match(TokenType.TRUE):
            return expr.Literal(True)
        elif self.match(TokenType.NIL):
            return expr.Literal(None)

        elif self.list_match([TokenType.STRING, TokenType.NUMBER]):
            return expr.Literal(self.previous().literal)

        elif self.match(TokenType.LEFT_PAREN):
            expression = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return expr.Grouping(expression)

        elif self.match(TokenType.SUPER):
            keyword = self.previous()
            self.consume(TokenType.DOT, "Expect '.' after 'super'.")
            method = self.consume(
                TokenType.IDENTIFIER, "Expect superclass method name."
            )
            return expr.Super(keyword, method)

        elif self.match(TokenType.SELF):
            return expr.Self(self.previous())

        elif self.match(TokenType.IDENTIFIER):
            return expr.Var(self.previous())

        self.error(self.peek(), "Expect expression.")

    def consume(self, token_type: TokenType, message: str) -> Token | None:
        if self.check(token_type):
            return self.advance()

        return self.error(self.peek(), message)

    def match(self, token_type: TokenType) -> bool:
        if self.check(token_type):
            self.advance()
            return True

        return False

    def list_match(self, types: list[TokenType]) -> bool:
        for token_type in types:
            if self.check(token_type):
                self.advance()
                return True

        return False

    def check(self, expected_type: TokenType) -> bool:
        if self.is_at_end():
            return False
        return self.peek().token_type == expected_type

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def is_at_end(self) -> bool:
        return self.peek().token_type == TokenType.EOF

    @staticmethod
    def error(token: Token, message: str):
        msg = f"Error: {message}, token: {token}"
        raise ParserError(msg)

    def synchronize(self) -> None:
        self.advance()

        keywords = [
            TokenType.CLASS,
            TokenType.FUN,
            TokenType.VAR,
            TokenType.FOR,
            TokenType.IF,
            TokenType.WHILE,
            TokenType.PRINT,
            TokenType.RETURN,
        ]

        while not self.is_at_end():
            if self.previous().token_type == TokenType.SEMICOLON:
                return

            next_type = self.peek().token_type
            if next_type in keywords:
                return

            self.advance()
