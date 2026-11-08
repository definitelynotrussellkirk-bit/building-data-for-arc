"""
LayeredGrid builtins — 10-layer representation + collision handling.
"""

from .helpers import Grid, _unwrap, _apply_closure
from ..parser import StrLit as _StrLit


def _str(x):
    """Convert StrLit to str."""
    return x.value if isinstance(x, _StrLit) else str(x) if not isinstance(x, str) else x


def register(env):
    """Register LayeredGrid builtins into env."""
    from ..layered_grid import LayeredGrid, LayerMask

    env.define('grid->layered', lambda g: LayeredGrid.from_grid(_unwrap(g)))
    env.define('layered->grid', lambda lg, priority="highest": Grid(lg.to_grid(priority)))

    # Layer access
    env.define('layer', lambda lg, c: lg.layer(c).tolist())
    env.define('set-layer', lambda lg, c, mask: lg.set_layer(c, mask))
    env.define('clear-layer', lambda lg, c: lg.clear_layer(c))
    env.define('swap-layers', lambda lg, c1, c2: lg.swap_layers(c1, c2))

    # Color operations on layers
    env.define('recolor-layer', lambda lg, src, dst: lg.recolor(src, dst))
    env.define('recolor-layers', lambda lg, mapping: lg.recolor_map(mapping))

    # Spatial operations on layers
    env.define('shift-layer', lambda lg, c, dr, dc: lg.shift_layer(c, dr, dc))
    env.define('rotate-layer', lambda lg, c, k=1: lg.rotate_layer(c, k))
    env.define('flip-layer', lambda lg, c, axis="lr": lg.flip_layer(c, axis))
    env.define('apply-to-layer', lambda lg, c, fn:
        lg.apply_to_layer(c, fn if callable(fn) else (lambda m: _apply_closure(fn, [m]))))

    # Movement with collision
    env.define('move-layer', lambda lg, c, dr, dc, collision="overwrite", blocker=None:
        lg.move_layer(c, dr, dc, _str(collision), blocker))
    env.define('gravity-layer', lambda lg, c, direction="down", collision="block", blocker=None:
        lg.gravity_layer(c, _str(direction), _str(collision), blocker))

    # Boolean layer ops
    env.define('layer-and', lambda lg, c1, c2: lg.layer_and(c1, c2).tolist())
    env.define('layer-or', lambda lg, c1, c2: lg.layer_or(c1, c2).tolist())
    env.define('layer-not', lambda lg, c: lg.layer_not(c).tolist())
    env.define('any-color-mask', lambda lg: lg.any_color_mask().tolist())
    env.define('no-color-mask', lambda lg: lg.no_color_mask().tolist())

    # LayerMask selection
    env.define('select-colors', lambda lg, *colors: lg.select(list(colors)))
    env.define('select-all-colors', lambda lg: lg.select_all())
    env.define('selection-move', lambda sel, dr, dc, collision="block": Grid(sel.move(dr, dc, collision).to_grid()))
    env.define('selection-recolor', lambda sel, new_c: Grid(sel.recolor(new_c).to_grid()))
    env.define('selection-remove', lambda sel: Grid(sel.remove().to_grid()))
    env.define('selection-positions', lambda sel: sel.positions())
    env.define('selection-bbox', lambda sel: sel.bbox())
    env.define('selection-count', lambda sel: sel.count())
    env.define('selection-mask', lambda sel: sel.to_mask())

    # LayeredGrid arithmetic
    env.define('lg+', lambda a, b: a + b)
    env.define('lg-', lambda a, b: a - b)
    env.define('lg*', lambda a, b: a * b)
    env.define('lg-colors', lambda lg: sorted(lg.colors_present()))
    env.define('lg-color-count', lambda lg, c: lg.color_count(c))

    # Convenience: do a layered operation and return flat Grid in one step
    env.define('with-layers', lambda g, fn:
        Grid((fn if callable(fn) else (lambda lg: _apply_closure(fn, [lg])))(
            LayeredGrid.from_grid(_unwrap(g))).to_grid()))
