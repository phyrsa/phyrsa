from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # Keywords
    MODULE = auto()
    EXPORT = auto()
    USING = auto()
    IMPORT = auto()
    FROM = auto()
    AS = auto()
    FN = auto()
    STRUCT = auto()
    MUTABLE = auto()
    SUM = auto()
    CONTRACT = auto()
    INSTANCE = auto()
    IF = auto()
    ELSE = auto()
    FOR = auto()
    WHILE = auto()
    MATCH = auto()
    PARALLEL = auto()
    CONST = auto()
    SKIP = auto()
    NEXT = auto()
    RETURN = auto()

    # Operators
    EQUALS = auto()           # =
    ARROW_LEFT = auto()       # <-
    PIPE = auto()             # |>
    DEFINED_AS = auto()       # ≜ or :=
    LAMBDA = auto()           # λ or \
    RIGHT_ARROW = auto()      # ->
    PLUS = auto()             # +
    MINUS = auto()            # -
    STAR = auto()             # * or ×
    SLASH = auto()            # /
    CARET = auto()            # ^ or ² or ³
    PLUS_MINUS = auto()       # ±
    SQRT = auto()             # √
    PI = auto()               # π
    LESS_EQUAL = auto()       # ≤ or <=
    GREATER_EQUAL = auto()    # ≥ or >=
    NOT_EQUAL = auto()        # ≠ or !=
    IN = auto()               # ∈
    LESS = auto()             # <
    GREATER = auto()          # >
    EQUAL_EQUAL = auto()      # ==
    DOT = auto()              # .
    DOT_OP = auto()           # .+ .- .* ./ .^
    QUESTION = auto()         # ?
    AT = auto()               # @
    COLON = auto()            # :
    DOUBLE_COLON = auto()     # ::

    # Punctuation
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()

    # Structure
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()


KEYWORDS = {
    "module": TokenType.MODULE, "export": TokenType.EXPORT,
    "using": TokenType.USING, "import": TokenType.IMPORT,
    "from": TokenType.FROM, "as": TokenType.AS,
    "fn": TokenType.FN, "struct": TokenType.STRUCT,
    "mutable": TokenType.MUTABLE, "sum": TokenType.SUM,
    "contract": TokenType.CONTRACT, "instance": TokenType.INSTANCE,
    "if": TokenType.IF, "else": TokenType.ELSE,
    "for": TokenType.FOR, "while": TokenType.WHILE,
    "match": TokenType.MATCH, "parallel": TokenType.PARALLEL,
    "const": TokenType.CONST, "skip": TokenType.SKIP,
    "next": TokenType.NEXT, "return": TokenType.RETURN,
}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.column})"


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.indent_stack = [0]
        self.tokens = []
        self.at_line_start = True

    def peek(self, offset=0):
        i = self.pos + offset
        return self.source[i] if i < len(self.source) else ''

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def add(self, ttype, value):
        self.tokens.append(Token(ttype, value, self.line, self.column))

    def tokenize(self):
        while self.pos < len(self.source):
            if self.at_line_start:
                self.handle_indentation()
                self.at_line_start = False
                if self.pos >= len(self.source):
                    break

            ch = self.peek()

            if ch in ' \t':
                self.advance()
                continue
            if ch == '#':
                self.skip_comment()
                continue
            if ch == '\n':
                self.add(TokenType.NEWLINE, '\\n')
                self.advance()
                self.at_line_start = True
                continue
            if ch.isdigit():
                self.read_number()
                continue
            if ch == '"':
                self.read_string()
                continue
            if ch.isalpha() or ch == '_':
                self.read_identifier()
                continue
            if not self.read_operator():
                raise SyntaxError(
                    f"Unexpected {ch!r} at line {self.line}, col {self.column}"
                )

        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.add(TokenType.DEDENT, '')
        self.add(TokenType.EOF, '')
        return self.tokens

    def handle_indentation(self):
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos] in ' \t':
            self.pos += 1
        indent = self.pos - start

        if self.pos >= len(self.source):
            return
        if self.source[self.pos] == '\n':
            return
        if self.source[self.pos] == '#':
            return

        current = self.indent_stack[-1]
        if indent > current:
            self.indent_stack.append(indent)
            self.add(TokenType.INDENT, ' ' * indent)
        elif indent < current:
            while len(self.indent_stack) > 1 and self.indent_stack[-1] > indent:
                self.indent_stack.pop()
                self.add(TokenType.DEDENT, '')
            if self.indent_stack[-1] != indent:
                raise SyntaxError(
                    f"Inconsistent indentation at line {self.line}"
                )

    def skip_comment(self):
        if self.peek(1) == '=':
            self.advance(); self.advance()
            depth = 1
            while self.pos < len(self.source) and depth > 0:
                if self.peek() == '=' and self.peek(1) == '#':
                    self.advance(); self.advance(); depth -= 1
                elif self.peek() == '#' and self.peek(1) == '=':
                    self.advance(); self.advance(); depth += 1
                else:
                    self.advance()
        else:
            while self.pos < len(self.source) and self.peek() != '\n':
                self.advance()

    def read_number(self):
        start = self.pos
        while self.pos < len(self.source) and (self.peek().isdigit() or self.peek() == '_'):
            self.advance()
        if self.peek() == '.' and self.peek(1).isdigit():
            self.advance()
            while self.pos < len(self.source) and (self.peek().isdigit() or self.peek() == '_'):
                self.advance()
        if self.peek() in ('e', 'E'):
            save = self.pos
            self.advance()
            if self.peek() in '+-':
                self.advance()
            if self.peek().isdigit():
                while self.pos < len(self.source) and self.peek().isdigit():
                    self.advance()
            else:
                self.pos = save
        self.add(TokenType.NUMBER, self.source[start:self.pos].replace('_', ''))

    def read_string(self):
        l, c = self.line, self.column
        self.advance()
        buf = []
        while self.pos < len(self.source) and self.peek() != '"':
            if self.peek() == '\\':
                self.advance()
                buf.append(self.advance())
            else:
                buf.append(self.advance())
        if self.pos >= len(self.source):
            raise SyntaxError(f"Unterminated string at line {l}")
        self.advance()
        self.tokens.append(Token(TokenType.STRING, ''.join(buf), l, c))

    def read_identifier(self):
        start = self.pos
        while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() == '_'):
            self.advance()
        word = self.source[start:self.pos]
        self.add(KEYWORDS.get(word, TokenType.IDENTIFIER), word)

    def read_operator(self):
        ch = self.peek()
        two = self.source[self.pos:self.pos + 2]

        two_map = {
            '<-': TokenType.ARROW_LEFT,
            '|>': TokenType.PIPE,
            '->': TokenType.RIGHT_ARROW,
            '::': TokenType.DOUBLE_COLON,
            '<=': TokenType.LESS_EQUAL,
            '>=': TokenType.GREATER_EQUAL,
            '!=': TokenType.NOT_EQUAL,
            '==': TokenType.EQUAL_EQUAL,
            ':=': TokenType.DEFINED_AS,
            '.+': TokenType.DOT_OP, '.-': TokenType.DOT_OP,
            '.*': TokenType.DOT_OP, './': TokenType.DOT_OP,
            '.^': TokenType.DOT_OP,
        }
        if two in two_map:
            self.advance(); self.advance()
            self.add(two_map[two], two)
            return True

        one_map = {
            '=': TokenType.EQUALS,
            '+': TokenType.PLUS, '-': TokenType.MINUS,
            '*': TokenType.STAR, '×': TokenType.STAR,
            '/': TokenType.SLASH,
            '^': TokenType.CARET, '²': TokenType.CARET, '³': TokenType.CARET,
            '±': TokenType.PLUS_MINUS,
            '√': TokenType.SQRT, 'π': TokenType.PI,
            '≤': TokenType.LESS_EQUAL, '≥': TokenType.GREATER_EQUAL,
            '≠': TokenType.NOT_EQUAL, '∈': TokenType.IN,
            '<': TokenType.LESS, '>': TokenType.GREATER,
            '.': TokenType.DOT, '?': TokenType.QUESTION,
            '@': TokenType.AT, ':': TokenType.COLON,
            '(': TokenType.LPAREN, ')': TokenType.RPAREN,
            '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
            '{': TokenType.LBRACE, '}': TokenType.RBRACE,
            ',': TokenType.COMMA,
            '≜': TokenType.DEFINED_AS, 'λ': TokenType.LAMBDA, '\\': TokenType.LAMBDA,
        }
        if ch in one_map:
            self.advance()
            self.add(one_map[ch], ch)
            return True

        return False


def tokenize(source: str):
    return Lexer(source).tokenize()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m phyrsa_syntax.lexer <file.phy>")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        for tok in tokenize(f.read()):
            print(tok)