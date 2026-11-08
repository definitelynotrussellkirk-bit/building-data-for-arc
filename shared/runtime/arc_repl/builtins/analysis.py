"""
Analysis builtins — high-level pattern detection.
"""

from .helpers import Grid, _unwrap, _call


def register(env):
    """Register analysis builtins into env."""
    from .. import analysis as _analysis

    env.define('detect-frames', lambda g, wc=None, bg=0: _analysis.detect_frames(_unwrap(g), wc, bg))
    env.define('fill-frame-interiors', lambda g, fc, wc=None, bg=0: Grid(_analysis.fill_frame_interiors(_unwrap(g), fc, wc, bg)))
    env.define('detect-lines', lambda g, bg=0: _analysis.detect_lines(_unwrap(g), bg))
    env.define('find-scattered', lambda g, bg=0: _analysis.find_scattered_pixels(_unwrap(g), bg))
    env.define('detect-regularity', lambda g, bg=0: _analysis.detect_regularity(_unwrap(g), bg))
    env.define('detect-motion', lambda g1, g2, bg=0: _analysis.detect_motion(_unwrap(g1), _unwrap(g2), bg))
    env.define('characterize-cells', lambda g, cells, bg=0: _analysis.characterize_cells(_unwrap(g), cells, bg))

    # Internal separators & cell grid
    env.define('internal-separators', lambda g, bg=0: _analysis.internal_separators(_unwrap(g), bg))
    env.define('internal-sep-rows', lambda g, bg=0: _analysis.internal_separators(_unwrap(g), bg)['rows'])
    env.define('internal-sep-cols', lambda g, bg=0: _analysis.internal_separators(_unwrap(g), bg)['cols'])
    env.define('band-distance', lambda g, r, c, rr, rc, bg=0: _analysis.band_distance(_unwrap(g), r, c, rr, rc, bg))
    env.define('cell-grid', lambda g, bg=0: _analysis.cell_grid(_unwrap(g), bg))

    # Projection & mask application
    env.define('project-through-bands', lambda g, r1, c1, r2, c2, fn, bg=0:
        _analysis.project_through_bands(
            _unwrap(g), r1, c1, r2, c2,
            lambda d_rb, d_cb: _call(fn, d_rb, d_cb), bg))
    env.define('apply-to-mask', lambda g, mask, fn:
        Grid(_analysis.apply_to_mask_region(
            _unwrap(g), mask,
            lambda r, c, v: _call(fn, r, c, v))))
    env.define('apply-rule-in-shape', lambda g, fn, shape_mask:
        Grid(_analysis.apply_rule_in_shape(
            _unwrap(g),
            lambda r, c, v: _call(fn, r, c, v),
            shape_mask)))

    # Enclosure detection
    env.define('detect-enclosing-objects', lambda g, wc=None, bg=0: _analysis.detect_object_with_enclosure(_unwrap(g), wc, bg))
