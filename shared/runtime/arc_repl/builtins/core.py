"""
Core builtins — arithmetic, boolean, collections, type predicates, combinators, I/O.
"""

import functools
import operator

from ..evaluator import Closure
from ..shape import Shape
from .helpers import Grid, _call, _unwrap


def register(env):
    """Register core builtins into env."""

    # ============================================================
    # Arithmetic
    # ============================================================
    env.define('+', lambda *args: sum(args))
    env.define('-', lambda a, b=None: -a if b is None else a - b)
    env.define('*', lambda *args: functools.reduce(operator.mul, args, 1))
    env.define('/', lambda a, b: a / b if isinstance(a, float) or isinstance(b, float) else a // b)
    env.define('mod', lambda a, b: a % b)
    env.define('=', lambda a, b: a == b)
    env.define('!=', lambda a, b: a != b)
    env.define('<', lambda a, b: a < b)
    env.define('>', lambda a, b: a > b)
    env.define('<=', lambda a, b: a <= b)
    env.define('>=', lambda a, b: a >= b)
    env.define('min', min)
    env.define('max', max)
    env.define('abs', abs)

    # Math
    env.define('floor', lambda x: int(x))
    env.define('round', lambda x: round(x))

    # ============================================================
    # Boolean
    # ============================================================
    env.define('not', lambda x: not x)
    env.define('and', lambda a, b: a and b)
    env.define('or', lambda a, b: a or b)

    # ============================================================
    # Collections
    # ============================================================
    env.define('list', lambda *args: list(args))
    env.define('length', len)
    env.define('nth', lambda lst, i: lst[i])
    env.define('first', lambda lst: lst[0])
    env.define('last', lambda lst: lst[-1])
    env.define('car', lambda lst: lst[0])
    env.define('cdr', lambda lst: lst[1:])
    env.define('cons', lambda a, b: [a] + (b if isinstance(b, list) else [b]))
    env.define('append', lambda *lsts: sum((l if isinstance(l, list) else [l] for l in lsts), []))
    env.define('reverse', lambda lst: list(reversed(lst)))
    env.define('range', lambda *args: list(range(*args)))
    env.define('member?', lambda x, lst: x in lst)
    env.define('null?', lambda x: x is None or (isinstance(x, list) and len(x) == 0))
    env.define('map', lambda fn, lst: [_call(fn, x) for x in lst])
    env.define('filter', lambda fn, lst: [x for x in lst if _call(fn, x)])
    env.define('reduce', lambda fn, init, lst: functools.reduce(
        lambda a, b: _call(fn, a, b), lst, init))

    def _sort_fn(lst, key_or_cmp=None):
        if key_or_cmp is None:
            return sorted(lst)
        try:
            return sorted(lst, key=lambda x: _call(key_or_cmp, x))
        except Exception:
            return sorted(lst, key=functools.cmp_to_key(
                lambda a, b: -1 if _call(key_or_cmp, a, b) else 1))

    env.define('sort', _sort_fn)
    env.define('sort-by', lambda lst, key_fn: sorted(lst, key=lambda x: _call(key_fn, x)))

    # Unique / count / index / flatten
    env.define('unique', lambda lst: sorted(set(lst)))
    env.define('count', lambda lst, val: lst.count(val))
    env.define('index-of', lambda lst, val: lst.index(val) if val in lst else -1)
    env.define('flatten', lambda lst: [x for sub in lst for x in (sub if isinstance(sub, list) else [sub])])
    env.define('flatmap', lambda fn, lst: [x for sub in [_call(fn, item) for item in lst]
                                           for x in (sub if isinstance(sub, list) else [sub])])
    env.define('flat-map', lambda fn, lst: [x for sub in [_call(fn, item) for item in lst]
                                            for x in (sub if isinstance(sub, list) else [sub])])
    env.define('find', lambda fn, lst: next((x for x in lst if _call(fn, x)), None))

    # Pair accessors
    env.define('fst', lambda p: p[0])
    env.define('snd', lambda p: p[1])
    env.define('third', lambda p: p[2])

    # Dict ops
    env.define('dict', lambda *pairs: dict(zip(pairs[0::2], pairs[1::2])))
    env.define('dict-get', lambda d, k, default=None: d.get(k, default))
    env.define('dict-keys', lambda d: list(d.keys()))
    env.define('dict-values', lambda d: list(d.values()))

    # ============================================================
    # Type predicates
    # ============================================================
    env.define('grid?', lambda x: isinstance(x, Grid))
    env.define('shape?', lambda x: isinstance(x, Shape))
    env.define('number?', lambda x: isinstance(x, (int, float)) and not isinstance(x, bool))
    env.define('boolean?', lambda x: isinstance(x, bool))
    env.define('list?', lambda x: isinstance(x, list))
    env.define('dict?', lambda x: isinstance(x, dict))
    env.define('callable?', lambda x: callable(x) or isinstance(x, Closure))

    # ============================================================
    # Combinators
    # ============================================================
    def _compose(*fns):
        def composed(grid):
            result = grid
            for fn in reversed(fns):
                result = fn(result)
            return result
        return composed

    def _pipe(*fns):
        def piped(grid):
            result = grid
            for fn in fns:
                result = fn(result)
            return result
        return piped

    env.define('compose', _compose)
    env.define('pipe', _pipe)
    env.define('identity', lambda x: x)

    # ============================================================
    # Utility builtins
    # ============================================================
    env.define('apply', lambda fn, args: _call(fn, *args))
    env.define('min-list', lambda lst: min(lst))
    env.define('max-list', lambda lst: max(lst))
    env.define('sum-list', lambda lst: sum(lst))
    env.define('mean-list', lambda lst: sum(lst) / len(lst) if lst else 0)
    env.define('zip-lists', lambda *lsts: list(map(list, zip(*lsts))))
    env.define('enumerate-list', lambda lst: [[i, v] for i, v in enumerate(lst)])
    env.define('any?', lambda fn, lst: any(_call(fn, x) for x in lst))
    env.define('all?', lambda fn, lst: all(_call(fn, x) for x in lst))
    env.define('count-where', lambda fn, lst: sum(1 for x in lst if _call(fn, x)))
    env.define('find-first', lambda fn, lst: next((x for x in lst if _call(fn, x)), None))

    # ============================================================
    # I/O
    # ============================================================
    env.define('print', lambda *args: print(*args) or None)
    env.define('display', lambda x: str(x))
