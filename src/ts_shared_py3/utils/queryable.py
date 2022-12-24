""" this module defines an object that allows you to run SQL-like
queries on python dicts and named-tuples
it is used to get counts of filtered data inside of SQO objs (called by generated rules)
with query params expressed as name-value pairs

below is "queryable" code
"""
import operator
import itertools
import inspect

itee = itertools.tee

operators = {
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
    ">=": operator.ge,
    ">": operator.gt,
    "in": operator.contains,
    "nin": lambda x, y: not operator.contains(x, y),
}


def _can_take_at_least_n_args(f, n=2):
    """helper to check that a function can take at least two unnamed args

    :param f:     function to test
    :param n:     # of required args to func
    :returns boolean:    true if function accepts specified # of args
    """
    (pos, args, kwargs, defaults) = inspect.getargspec(f)
    if args is not None or len(pos) >= n:
        return True
    else:
        return False


def query(D, key, val, operator="==", keynotfound=None, isTuple=False):
    """actual query method

    :param D:  data--a list of dictionaries to search
    :param key:  the key to query
    :param val:  the value
    :param operator:  "==", ">=", "in", et all, or any two-arg function
    :param keynotfound:  value if key is not found
    :param isTuple:  niu

    :returns list:  elements in D such that operator(D.get(key,None), val) is true
    """
    D = itee(D, 2)[1]  # take a teed copy

    # let's let operator be any two argument callable function, *then*
    # fall back on the delegation table.
    if callable(operator):
        if not _can_take_at_least_n_args(operator, 2):
            raise ValueError("operator must take at least 2 arguments")
            # alternately, we could wrap it in a lambda, like:
            # op = lambda(x,y): operator(x),
            # but we have to check to see how many args it really wants (inc. 0!)
        op = operator
    else:
        op = operators.get(operator, None)
    if not op:
        raise ValueError(
            "operator must be one of %r, or a two-argument function".format(operators)
        )

    def try_op(f, x, y):
        try:
            # ans = f(x,y)
            return f(x, y)
        except Exception as exc:
            return False

    # if isTuple:
    #     return (x for x in D if try_op(op, getattr(x,key,keynotfound), val))     #getattr(x,key,keynotfound),val)
    # else    # must be a dict
    return (x for x in D if try_op(op, x.get(key, keynotfound), val))


class Queryable(object):
    """creates instance of a searchable list of dicts/namedTuples"""

    def __init__(self, D):
        """constructor for a Queryable obj
        pass a list of dicts or namedTuples
        """
        self.D = itee(D, 2)[1]

    def tolist(self):
        """return matching rows as a list"""
        return list(itee(self.D, 2)[1])

    def count(self):
        return len([i for i in self.D])

    def query(self, *args, **kwargs):
        """run a query against this Queryable obj"""
        return Queryable(query(self.D, *args, **kwargs))

    q = query  # q is a shortcut alias to the query method


if __name__ == "__main__":
    """test basic queries & chaining of queries"""
    # a list of dicts to query against
    data = [
        dict(a=None, b=1, c=4, d=[1, 2, 3]),
        dict(a=13, d=dict(a=1, b=2)),
        dict(c=13, e="some string"),
        dict(c=10, e="some other string"),
        dict(a=10, e="some other string"),
        {("author", "email"): ("Gregg Lind", "gregg.lind at fakearoo.com")},
    ]

    print(data)
    # c > 10 and "other" in e
    smartObj = Queryable(data)
    Q = smartObj.q("c", 3, ">")
    # print Q.tolist()
    # now chain another query
    # Q = Q.q('e', 'other', 'in')
    # print Q.tolist()
