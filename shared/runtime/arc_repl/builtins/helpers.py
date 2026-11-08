"""
Shared helpers for all builtin modules.

Provides:
  _unwrap / _wrap          — Grid <-> list-of-lists conversion
  _call / _apply_closure   — call Closures and regular functions uniformly
  _make_transform_builtin  — wrap a transform function for the REPL
  _make_feature_builtin    — wrap a feature function for the REPL
  Grid                     — re-export from _builtins_legacy (kept for compat)
"""

import inspect
import numpy as np

from ..evaluator import Closure, apply_fn, Env


# ============================================================
# Grid class — the one used by the legacy system
# ============================================================

class Grid:
    """First-class grid value in the evaluator."""
    __slots__ = ('data', 'height', 'width')

    def __init__(self, data):
        if isinstance(data, np.ndarray):
            data = data.tolist()
        self.data = data
        self.height = len(data)
        self.width = len(data[0]) if data else 0

    def __repr__(self):
        return f"Grid({self.height}x{self.width})"

    def __eq__(self, other):
        if isinstance(other, Grid):
            return self.data == other.data
        if isinstance(other, list):
            return self.data == other
        return False


# ============================================================
# Unwrap / Wrap
# ============================================================

def _unwrap(val):
    """Unwrap Grid to list-of-lists for passing to transform functions."""
    if isinstance(val, Grid):
        return val.data
    return val


def _wrap(val):
    """Wrap list-of-lists result back to Grid."""
    if isinstance(val, list) and val and isinstance(val[0], list):
        return Grid(val)
    return val


# ============================================================
# Closure application
# ============================================================

def _apply_closure(closure, args):
    """Helper for map/filter/reduce with Closure objects."""
    return apply_fn(closure, args, closure.env)


def _call_any(fn, *args):
    """Call a function or Closure — works in any module."""
    if isinstance(fn, Closure):
        return _apply_closure(fn, list(args))
    return fn(*args)


# Alias used inside register() functions
_call = _call_any


# ============================================================
# Transform / Feature wrappers
# ============================================================

def _make_transform_builtin(fn):
    """Wrap a transform function to handle Grid unwrap/wrap and currying."""
    try:
        sig = inspect.signature(fn)
        n_params = len([p for p in sig.parameters.values()
                       if p.default is inspect.Parameter.empty])
    except (ValueError, TypeError):
        n_params = 1

    def wrapper(*args):
        if len(args) < n_params:
            return lambda grid: _wrap(fn(_unwrap(grid), *[_unwrap(a) for a in args]))
        return _wrap(fn(*[_unwrap(a) for a in args]))

    wrapper.__name__ = getattr(fn, '__name__', 'transform')
    return wrapper


def _make_feature_builtin(fn, level):
    """Wrap a feature function to handle Grid unwrapping."""
    def wrapper(*args):
        return fn(*[_unwrap(a) for a in args])
    wrapper.__name__ = getattr(fn, '__name__', 'feature')
    return wrapper
