"""
Builtins package — organized by domain.

Each module registers its builtins via register(env).
make_global_env() assembles them all + loads the prelude.
"""

import sys
from pathlib import Path

# Ensure imports work
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Re-export the key types and helpers for backward compatibility
from .helpers import Grid, _unwrap, _wrap, _call_any, _apply_closure


def make_global_env():
    """Create the global environment with all builtins."""
    from ..evaluator import Env

    env = Env()

    # Import and register each module
    from .core import register as reg_core
    from .grid import register as reg_grid
    from .layers import register as reg_layers
    from .neighbors import register as reg_neighbors
    from .shapes import register as reg_shapes
    from .objects import register as reg_objects
    from .analysis import register as reg_analysis
    from .filters import register as reg_filters
    from .conditions import register as reg_conditions
    from .features import register as reg_features
    from .sizing import register as reg_sizing

    reg_core(env)
    reg_grid(env)
    reg_layers(env)
    reg_neighbors(env)
    reg_shapes(env)
    reg_objects(env)
    reg_analysis(env)
    reg_filters(env)
    reg_conditions(env)
    reg_features(env)
    reg_sizing(env)

    # Load Racket prelude — defines derived ops from primitives
    _load_prelude(env)

    return env


def _load_prelude(env):
    """Load .rkt prelude files in dependency order."""
    import os
    from ..parser import parse_all
    from ..evaluator import evaluate

    prelude_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prelude')
    if not os.path.isdir(prelude_dir):
        return

    load_order = ['macros.rkt', 'core.rkt', 'grid.rkt', 'transforms.rkt', 'conditions.rkt']

    for filename in load_order:
        filepath = os.path.join(prelude_dir, filename)
        if not os.path.exists(filepath):
            continue
        try:
            with open(filepath) as f:
                source = f.read()
            # Strip comments (lines starting with ;)
            lines = [l for l in source.split('\n') if not l.strip().startswith(';')]
            clean = '\n'.join(lines)
            if not clean.strip():
                continue
            exprs = parse_all(clean)
            for expr in exprs:
                evaluate(expr, env)
        except Exception as e:
            print(f"Warning: prelude {filename}: {e}")


# Cached global env
_global_env = None


def get_global_env():
    """Get or create the cached global environment."""
    global _global_env
    if _global_env is None:
        _global_env = make_global_env()
    return _global_env


__all__ = ['Grid', '_unwrap', '_wrap', '_call_any', '_apply_closure',
           'make_global_env', 'get_global_env']
