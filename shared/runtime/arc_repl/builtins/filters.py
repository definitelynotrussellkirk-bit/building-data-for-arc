"""
Filter builtins — filter/target/shape composition.
"""

from ..evaluator import Closure
from .helpers import Grid, _unwrap, _call, _apply_closure


def register(env):
    """Register filter builtins into env."""
    from .. import filters as _filters

    # Core composition: filter x target x shape
    env.define('apply-filtered', lambda g, filt, tgt: Grid(
        _filters.apply_filtered(_unwrap(g),
            filt if not isinstance(filt, Closure) else (lambda r,c,v: _apply_closure(filt,[r,c,v])),
            tgt if not isinstance(tgt, Closure) else (lambda r,c,v: _apply_closure(tgt,[r,c,v])))))
    env.define('apply-in-shape', lambda g, mask, rule: Grid(
        _filters.apply_in_shape(_unwrap(g),
            mask if not isinstance(mask, Closure) else (lambda r,c: _apply_closure(mask,[r,c])),
            lambda gr: _unwrap(_call(rule, Grid(gr))))))
    env.define('apply-filtered-in-shape', lambda g, filt, tgt, mask: Grid(
        _filters.apply_filtered_in_shape(_unwrap(g),
            filt if not isinstance(filt, Closure) else (lambda r,c,v: _apply_closure(filt,[r,c,v])),
            tgt if not isinstance(tgt, Closure) else (lambda r,c,v: _apply_closure(tgt,[r,c,v])),
            mask if not isinstance(mask, Closure) else (lambda r,c: _apply_closure(mask,[r,c])))))

    # Pre-built filters
    env.define('color-filter', _filters.color_filter)
    env.define('not-color-filter', _filters.not_color_filter)
    env.define('colors-filter', _filters.colors_filter)
    env.define('position-filter', _filters.position_filter)
    env.define('row-filter', _filters.row_filter)
    env.define('col-filter', _filters.col_filter)
    env.define('border-filter', _filters.border_filter)
    env.define('nonzero-filter', _filters.nonzero_filter)
    env.define('and-filters', lambda *fs: _filters.combine_filters_and(*fs))
    env.define('or-filters', lambda *fs: _filters.combine_filters_or(*fs))
    env.define('not-filter', _filters.negate_filter)

    # Pre-built targets
    env.define('const-target', _filters.const_target)
    env.define('map-target', _filters.map_target)

    # Pre-built shape masks
    env.define('rect-mask', _filters.rect_mask)
    env.define('diamond-mask', _filters.diamond_mask)
    env.define('circle-mask', _filters.circle_mask)
    env.define('chebyshev-mask', _filters.chebyshev_mask)
    env.define('cross-mask', _filters.cross_mask)
    env.define('ring-mask', _filters.ring_mask)
    env.define('invert-mask', _filters.invert_mask)
    env.define('union-masks', lambda *ms: _filters.union_masks(*ms))
    env.define('intersect-masks', lambda *ms: _filters.intersect_masks(*ms))

    # Object-aware masks
    env.define('object-mask', _filters.object_mask)
    env.define('interior-mask', _filters.interior_mask)
    env.define('border-of-object-mask', _filters.border_of_object_mask)

    # Band-aware diamond mask
    env.define('band-diamond-mask', lambda g, r1, c1, r2, c2, bg=0:
        _filters.band_diamond_mask(_unwrap(g), r1, c1, r2, c2, bg))
