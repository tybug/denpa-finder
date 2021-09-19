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

Q = AtomicQuery
