from operator import and_, or_, not_

class Query:
    def __init__(self, queries, sentence):
        self.queries = queries
        self.sentence = sentence

    def op2_combine(self, op, q2):
        queries = self.queries | q2.queries
        def sentence(assignment):
            return op(self(assignment), q2(assignment))
        return Query(queries, sentence)

    def op1_combine(self, op):
        def sentence(assignment):
            return op(self(assignment))
        return Query(self.queries, sentence)

    def __and__(self, q2):
        return self.op2_combine(and_, q2)

    def __or__(self, q2):
        return self.op2_combine(or_, q2)

    def __invert__(self):
        return self.op1_combine(not_)

    def __call__(self, assignment):
        return self.sentence(assignment)


class AtomicQuery(Query):
    def __init__(self, query):
        # take set([x]) instead of set(x) to avoid x being split up when
        # it's an iterable (set("ab") == {"a", "b"}, not {"ab"})
        queries = set([query])

        def sentence(assignment):
            return assignment[query]

        super().__init__(queries, sentence)

    @staticmethod
    def from_string(query):
        p = Parser(query)
        return p.parse()

Q = AtomicQuery


class Token:
    AND = "&"
    OR = "|"
    NOT = "~"
    PAREN_LEFT = "("
    PAREN_RIGHT = ")"
    EOF = "EOF"

class Var:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"Var({self.name})"
    __repr__ = __str__

# I don't even know what class of parser to call this (nor at what level my
# grammar sits at in the parsing hierarchy), but it's certainly ... a parser.
# pretty sloppily written compared to formal parsers and grammars, but I'm not
# aiming for perfection here, just something good enough.
class Parser:
    def __init__(self, query):
        self.tokens = self.tokenize(query)

    def parse(self):
        q = self.parse_compound()
        token = self.tokens.pop(0)
        assert token is Token.EOF
        return q

    def parse_compound(self):
        q = self.parse_query()
        if self.tokens[0] in [Token.EOF, Token.PAREN_RIGHT]:
            return q
        op = self.parse_op()

        while True:
            q2 = self.parse_query()
            q = op(q, q2)
            if self.tokens[0] in [Token.EOF, Token.PAREN_RIGHT]:
                return q
            op = self.parse_op()

    def tokenize(self, query):
        tokens = []
        in_quoted_var = False
        var_name = ""

        i = 0

        while True:
            if i >= len(query):
                break
            char = query[i]
            remaining = query[i:]
            if char == "\"" and not in_quoted_var:
                in_quoted_var = True
            elif char == "\"" and in_quoted_var:
                tokens.append(Var(var_name))
                in_quoted_var = False
                var_name = ""
                # ignore the space or paren after closing quotes
                assert query[i + 1] in [" ", ")"]
                # skip over the space right after a closing quote, but don't
                # skip a closing paren
                if query[i + 1] == " ":
                    i += 1
            elif char == "(":
                tokens.append(Token.PAREN_LEFT)
            elif char == ")":
                # "finish" any existing variables, if any have been started
                if var_name != "":
                    tokens.append(Var(var_name))
                    var_name = ""
                tokens.append(Token.PAREN_RIGHT)

            elif char == "&":
                tokens.append(Token.AND)
            elif remaining.startswith("and "):
                tokens.append(Token.AND)
                i += 3

            elif char == "|":
                tokens.append(Token.OR)
            elif remaining.startswith("or "):
                tokens.append(Token.OR)
                i += 2

            elif char == "~":
                tokens.append(Token.NOT)
            elif remaining.startswith("not "):
                tokens.append(Token.NOT)
                i += 3
            elif char == " " and in_quoted_var:
                var_name += char
            elif char == " " and not in_quoted_var:
                tokens.append(Var(var_name))
                var_name = ""
            else:
                var_name += char

            i += 1

        tokens.append(Token.EOF)
        return tokens

    def parse_query(self):
        token = self.tokens.pop(0)

        if token is Token.NOT:
            token2 = self.tokens.pop(0)
            if token2 is Token.PAREN_LEFT:
                q = self.parse_compound()
                token3 = self.tokens.pop(0)
                assert token3 is Token.PAREN_RIGHT
                return ~q

            return ~Q(token2.name)

        assert isinstance(token, Var)
        return Q(token.name)

    def parse_op(self):
        token = self.tokens.pop(0)
        assert token in (Token.AND, Token.OR, Token.PAREN_RIGHT)
        if token is Token.AND:
            return and_
        if token is Token.OR:
            return or_
