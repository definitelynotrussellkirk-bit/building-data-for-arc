"""
Condition builtins — predicates, selectors, pathfinding.
"""

from .helpers import Grid, _unwrap


def register(env):
    """Register condition builtins into env."""
    from .. import conditions as cond

    env.define('same-color?', cond.same_color)
    env.define('same-shape?', cond.same_shape)
    env.define('same-size?', cond.same_size)
    env.define('on-same-row?', cond.on_same_row)
    env.define('on-same-col?', cond.on_same_col)
    env.define('are-adjacent?', cond.are_adjacent)
    env.define('obj-is-color?', cond.obj_is_color)
    env.define('obj-is-dot?', cond.obj_is_dot)
    env.define('obj-is-line?', cond.obj_is_line)
    env.define('obj-is-rectangular?', cond.obj_is_rectangular)
    env.define('has-enclosed?', cond.has_enclosed_regions)
    env.define('has-color?', cond.has_color)
    env.define('objects-where', lambda g, fn: cond.objects_where(_unwrap(g), fn))
    env.define('cells-where', lambda g, fn: cond.cells_where(_unwrap(g), fn))
    env.define('shortest-path', lambda g, *a: cond.shortest_path(_unwrap(g), *a))
    env.define('connect-all-same-color', lambda g, *a: Grid(cond.connect_all_same_color(_unwrap(g), *a)))
    env.define('connect-on-same-axis', lambda g, *a: Grid(cond.connect_on_same_axis(_unwrap(g), *a)))
