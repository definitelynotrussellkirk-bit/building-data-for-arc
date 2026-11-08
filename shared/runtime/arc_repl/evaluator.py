"""
S-expression evaluator for the ARC REPL — LEGACY FALLBACK.

Production rule execution goes through `arc_repl.racket_bridge`
(a Racket subprocess) — see CLAUDE.md "Racket Backend" and
`arc_repl/racket_prelude/arc-prelude.rkt`. This Python interpreter
is kept for:

  - Lint / search / quick experiments that don't need a real Racket
    cold-start.
  - Sanity-checking Racket prelude semantics.
  - REPL features that haven't been ported to the bridge path
    (auto-scan, suggest!, etc.).

Live dependents (verified 2026-07-01):
  - arc_repl/executor.py and arc_repl/builtins/* (core/filters/grid/helpers)
  - swarm/preflight.py, swarm/tests/test_evaluator_parity.py

If you add new runtime semantics, add them to the Racket prelude
first. Adding only here will quietly diverge production behavior.

Adapted from rack/core. Supports: symbols, closures, lexical scope,
lambda, let, if, define, begin, cond, map, filter, reduce, for/list.
Stripped of sympy/Fraction. Adds Grid as a self-evaluating type.
"""

from .parser import Symbol, StrLit


class EvalError(Exception):
    pass

class UnboundError(EvalError):
    pass

class ArityError(EvalError):
    pass

class CostLimitError(EvalError):
    pass


class MacroExpander:
    """S-expression macro — transforms syntax before evaluation.

    (defmacro name (params...) template)

    When (name arg1 arg2 ...) is encountered:
    1. Substitute raw (unevaluated) args into the template
    2. Evaluate the expanded expression
    """
    __slots__ = ('name', 'params', 'template', 'env')

    def __init__(self, name, params, template, env):
        self.name = name
        self.params = params  # list of Symbol
        self.template = template
        self.env = env

    def expand(self, args):
        """Substitute args into template. Returns new S-expression."""
        if len(args) != len(self.params):
            raise ArityError(
                f"macro {self.name}: expected {len(self.params)} args, got {len(args)}")
        bindings = {}
        for i, param in enumerate(self.params):
            pname = param.name if isinstance(param, Symbol) else str(param)
            bindings[pname] = args[i]
        return self._substitute(self.template, bindings)

    def _substitute(self, expr, bindings):
        """Recursively substitute symbols in bindings."""
        if isinstance(expr, Symbol):
            if expr.name in bindings:
                return bindings[expr.name]
            return expr
        if isinstance(expr, list):
            return [self._substitute(e, bindings) for e in expr]
        return expr

    def __repr__(self):
        return f"<macro {self.name}>"


class Closure:
    """Lambda with captured environment."""
    __slots__ = ('params', 'body', 'env', 'name')

    def __init__(self, params, body, env, name=None):
        self.params = params
        self.body = body
        self.env = env
        self.name = name

    def __repr__(self):
        return f"<closure {self.name or 'anonymous'} ({' '.join(str(p) for p in self.params)})>"


class Env:
    """Lexical scope environment."""

    def __init__(self, bindings=None, parent=None):
        self.bindings = dict(bindings or {})
        self.parent = parent

    def lookup(self, name):
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.lookup(name)
        raise UnboundError(f"Unbound: {name}")

    def define(self, name, value):
        self.bindings[name] = value

    def set_bang(self, name, value):
        if name in self.bindings:
            self.bindings[name] = value
            return
        if self.parent:
            self.parent.set_bang(name, value)
            return
        raise UnboundError(f"Cannot set!: {name} is unbound")

    def child(self, bindings=None):
        return Env(bindings, self)


# Max recursion/iteration guards
_MAX_RECURSION = 200
_MAX_ITER = 50000
_recursion_depth = 0


def evaluate(expr, env):
    """Evaluate an S-expression in an environment."""
    global _recursion_depth

    # Self-evaluating types
    if isinstance(expr, (int, float, bool, StrLit, dict)):
        return expr
    if isinstance(expr, str):
        return expr
    if expr is None:
        return None

    # Grid objects are self-evaluating (added for ARC)
    if hasattr(expr, 'data') and hasattr(expr, 'height'):
        return expr

    # Symbol lookup
    if isinstance(expr, Symbol):
        return env.lookup(expr.name)

    # List = function call or special form
    if not isinstance(expr, list) or len(expr) == 0:
        return expr

    head = expr[0]

    # Raw data list — if head is not a Symbol or Closure-producing list,
    # and all elements are plain data, return as-is.
    # This handles [1 0 0] and [[1 0] [0 1]] grid literals from [...] parser.
    def _is_data(x):
        if isinstance(x, (int, float, bool, str, StrLit, dict)):
            return True
        if isinstance(x, list):
            return all(_is_data(e) for e in x)
        return False

    if _is_data(expr):
        return expr

    # ============================================================
    # Special forms
    # ============================================================

    if isinstance(head, Symbol):
        name = head.name

        if name == 'quote':
            return expr[1]

        if name == 'if':
            test = evaluate(expr[1], env)
            # Scheme semantics: only #f (False) and None are falsy.
            # 0, empty list, empty string are all TRUTHY.
            if test is not False and test is not None:
                return evaluate(expr[2], env)
            elif len(expr) > 3:
                return evaluate(expr[3], env)
            return None

        if name == 'cond':
            for clause in expr[1:]:
                if isinstance(clause[0], Symbol) and clause[0].name == 'else':
                    return evaluate(clause[1], env)
                val = evaluate(clause[0], env)
                if val is not False and val is not None:
                    return evaluate(clause[1], env)
            return None

        if name == 'and':
            result = True
            for e in expr[1:]:
                result = evaluate(e, env)
                if result is False or result is None:
                    return result
            return result

        if name == 'or':
            for e in expr[1:]:
                result = evaluate(e, env)
                if result is not False and result is not None:
                    return result
            return False

        if name == 'not':
            return not evaluate(expr[1], env)

        if name == 'define':
            if isinstance(expr[1], list):
                # (define (f x y) body) sugar
                fname = expr[1][0].name if isinstance(expr[1][0], Symbol) else str(expr[1][0])
                params = expr[1][1:]
                body = expr[2]
                closure = Closure(params, body, env, name=fname)
                env.define(fname, closure)
                return closure
            else:
                sym = expr[1].name if isinstance(expr[1], Symbol) else str(expr[1])
                val = evaluate(expr[2], env)
                env.define(sym, val)
                return val

        if name == 'set!':
            sym = expr[1].name if isinstance(expr[1], Symbol) else str(expr[1])
            val = evaluate(expr[2], env)
            env.set_bang(sym, val)
            return val

        if name == 'defmacro':
            # (defmacro name (params...) template)
            mname = expr[1].name if isinstance(expr[1], Symbol) else str(expr[1])
            mparams = expr[2]  # list of Symbols
            mtemplate = expr[3]
            macro = MacroExpander(mname, mparams, mtemplate, env)
            env.define(mname, macro)
            return macro

        if name == 'lambda':
            params = expr[1]
            body = expr[2] if len(expr) == 3 else [Symbol('begin')] + expr[2:]
            return Closure(params, body, env)

        if name == 'let':
            bindings = {}
            for binding in expr[1]:
                bname = binding[0].name if isinstance(binding[0], Symbol) else str(binding[0])
                bval = evaluate(binding[1], env)
                bindings[bname] = bval
            new_env = env.child(bindings)
            return evaluate(expr[2], new_env)

        if name == 'let*':
            new_env = env.child()
            for binding in expr[1]:
                bname = binding[0].name if isinstance(binding[0], Symbol) else str(binding[0])
                bval = evaluate(binding[1], new_env)
                new_env.define(bname, bval)
            return evaluate(expr[2], new_env)

        if name == 'begin':
            result = None
            for e in expr[1:]:
                result = evaluate(e, env)
            return result

        # ============================================================
        # Comprehensions
        # ============================================================

        if name == 'for/list':
            return _eval_for(expr, env, 'list')
        if name == 'for/sum':
            return _eval_for(expr, env, 'sum')
        if name == 'for/count':
            return _eval_for(expr, env, 'count')
        if name == 'for/and':
            return _eval_for(expr, env, 'and')
        if name == 'for/or':
            return _eval_for(expr, env, 'or')
        if name == 'for/min':
            return _eval_for(expr, env, 'min')
        if name == 'for/max':
            return _eval_for(expr, env, 'max')
        if name == 'for/first':
            return _eval_for(expr, env, 'first')

    # ============================================================
    # Function application (with macro expansion)
    # ============================================================

    fn = evaluate(head, env)

    # Macro expansion: expand before evaluating args
    if isinstance(fn, MacroExpander):
        expanded = fn.expand(expr[1:])  # raw, unevaluated args
        return evaluate(expanded, env)
    args = [evaluate(a, env) for a in expr[1:]]
    return apply_fn(fn, args, env)


def apply_fn(fn, args, env):
    """Apply a function to arguments."""
    global _recursion_depth

    if isinstance(fn, Closure):
        _recursion_depth += 1
        if _recursion_depth > _MAX_RECURSION:
            _recursion_depth -= 1
            raise CostLimitError(f"Max recursion depth ({_MAX_RECURSION}) exceeded")
        try:
            if len(args) < len(fn.params):
                raise ArityError(
                    f"{fn.name or 'lambda'}: expected {len(fn.params)} args, got {len(args)}")
            bindings = {}
            for i, param in enumerate(fn.params):
                pname = param.name if isinstance(param, Symbol) else str(param)
                bindings[pname] = args[i]
            call_env = fn.env.child(bindings)
            if fn.name:
                call_env.define(fn.name, fn)
            return evaluate(fn.body, call_env)
        finally:
            _recursion_depth -= 1

    if callable(fn):
        try:
            return fn(*args)
        except TypeError as e:
            raise ArityError(f"{fn}: {e}")

    raise EvalError(f"Not callable: {fn} (type {type(fn).__name__})")


def _eval_for(expr, env, mode):
    """Evaluate (for/X (var coll) body)."""
    binding = expr[1]
    var = binding[0]
    var_name = var.name if isinstance(var, Symbol) else str(var)
    coll = evaluate(binding[1], env)
    body = expr[2]

    if not hasattr(coll, '__iter__'):
        raise EvalError(f"for/{mode}: collection is not iterable: {type(coll)}")

    result = [] if mode == 'list' else (0 if mode in ('sum', 'count') else None)
    count = 0

    for item in coll:
        count += 1
        if count > _MAX_ITER:
            raise CostLimitError(f"for/{mode}: exceeded max iterations ({_MAX_ITER})")

        inner_env = env.child({var_name: item})
        val = evaluate(body, inner_env)

        if mode == 'list':
            result.append(val)
        elif mode == 'sum':
            result += val
        elif mode == 'count':
            if val is not False and val is not None:
                result += 1
        elif mode == 'and':
            if val is False or val is None:
                return False
        elif mode == 'or':
            if val is not False and val is not None:
                return True
        elif mode == 'first':
            if val is not False and val is not None:
                return val
        elif mode == 'min':
            result = val if result is None else min(result, val)
        elif mode == 'max':
            result = val if result is None else max(result, val)

    if mode == 'and':
        return True
    if mode == 'or':
        return False
    if mode == 'first':
        return None
    return result
