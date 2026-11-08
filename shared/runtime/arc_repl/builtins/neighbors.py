"""
Neighbor / position builtins — direction system, spatial queries, rays.
"""

from .helpers import _unwrap


def register(env):
    """Register neighbor/position builtins into env."""

    # Direction constants
    _DIRS_4 = [[-1,0],[1,0],[0,-1],[0,1]]
    _DIRS_8 = [[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]]
    _DIRS_DIAG = [[-1,-1],[-1,1],[1,-1],[1,1]]
    env.define('dirs-4', _DIRS_4)
    env.define('dirs-8', _DIRS_8)
    env.define('dirs-diag', _DIRS_DIAG)
    env.define('dirs-up', [[-1,0]])
    env.define('dirs-down', [[1,0]])
    env.define('dirs-left', [[0,-1]])
    env.define('dirs-right', [[0,1]])

    # Position helpers
    env.define('pos', lambda r, c: [r, c])
    env.define('pos-r', lambda p: p[0])
    env.define('pos-c', lambda p: p[1])
    env.define('pos-add', lambda p, d: [p[0]+d[0], p[1]+d[1]])
    env.define('pos-sub', lambda p1, p2: [p1[0]-p2[0], p1[1]-p2[1]])
    env.define('pos-eq?', lambda p1, p2: p1[0]==p2[0] and p1[1]==p2[1])
    env.define('pos-in-bounds?', lambda p, h, w: 0 <= p[0] < h and 0 <= p[1] < w)
    env.define('manhattan', lambda p1, p2: abs(p1[0]-p2[0]) + abs(p1[1]-p2[1]))
    env.define('chebyshev-dist', lambda p1, p2: max(abs(p1[0]-p2[0]), abs(p1[1]-p2[1])))

    # Cell-at with position
    env.define('cell-at-pos', lambda g, p: _unwrap(g)[p[0]][p[1]])

    # Neighbor queries — the core spatial primitives
    def _neighbors(g, r, c, dirs, h=None, w=None):
        """Return list of [nr, nc, value] for valid neighbors."""
        gd = _unwrap(g)
        if h is None: h = len(gd)
        if w is None: w = len(gd[0]) if gd else 0
        result = []
        for d in dirs:
            nr, nc = r + d[0], c + d[1]
            if 0 <= nr < h and 0 <= nc < w:
                result.append([nr, nc, gd[nr][nc]])
        return result

    def _neighbor_positions(g, r, c, dirs):
        """Return list of [nr, nc] for valid neighbors (no values)."""
        gd = _unwrap(g)
        h = len(gd)
        w = len(gd[0]) if gd else 0
        return [[r+d[0], c+d[1]] for d in dirs
                if 0 <= r+d[0] < h and 0 <= c+d[1] < w]

    def _neighbor_values(g, r, c, dirs):
        """Return list of values at valid neighbor positions."""
        gd = _unwrap(g)
        h = len(gd)
        w = len(gd[0]) if gd else 0
        return [gd[r+d[0]][c+d[1]] for d in dirs
                if 0 <= r+d[0] < h and 0 <= c+d[1] < w]

    def _neighbor_count(g, r, c, color, dirs):
        """Count neighbors matching a color."""
        return sum(1 for v in _neighbor_values(g, r, c, dirs) if v == color)

    def _has_neighbor(g, r, c, color, dirs):
        """Check if any neighbor matches color."""
        return any(v == color for v in _neighbor_values(g, r, c, dirs))

    # Register all neighbor functions
    env.define('neighbors', _neighbors)
    env.define('neighbors-4', lambda g, r, c: _neighbors(g, r, c, _DIRS_4))
    env.define('neighbors-8', lambda g, r, c: _neighbors(g, r, c, _DIRS_8))
    env.define('neighbor-positions', _neighbor_positions)
    env.define('neighbor-values', _neighbor_values)
    env.define('neighbor-count', _neighbor_count)
    env.define('neighbor-count-4', lambda g, r, c, color: _neighbor_count(g, r, c, color, _DIRS_4))
    env.define('neighbor-count-8', lambda g, r, c, color: _neighbor_count(g, r, c, color, _DIRS_8))
    env.define('has-neighbor?', _has_neighbor)
    env.define('has-neighbor-4?', lambda g, r, c, color: _has_neighbor(g, r, c, color, _DIRS_4))
    env.define('has-neighbor-8?', lambda g, r, c, color: _has_neighbor(g, r, c, color, _DIRS_8))

    # Count of non-bg neighbors
    env.define('nonzero-neighbor-count-4', lambda g, r, c, bg=0:
        sum(1 for v in _neighbor_values(g, r, c, _DIRS_4) if v != bg))
    env.define('nonzero-neighbor-count-8', lambda g, r, c, bg=0:
        sum(1 for v in _neighbor_values(g, r, c, _DIRS_8) if v != bg))

    # Neighbor-based filters
    env.define('isolated-filter', lambda dirs=_DIRS_8: (
        lambda r, c, v: v != 0 and not any(True for _ in [])))  # placeholder

    def _make_isolated_filter(g, connectivity=8):
        """Filter that matches isolated pixels (no same-color neighbors)."""
        gd = _unwrap(g)
        h, w = len(gd), len(gd[0]) if gd else 0
        dirs = _DIRS_8 if connectivity == 8 else _DIRS_4
        def filt(r, c, v):
            if v == 0: return False
            return not any(gd[r+d[0]][c+d[1]] == v
                          for d in dirs
                          if 0 <= r+d[0] < h and 0 <= c+d[1] < w)
        return filt

    env.define('make-isolated-filter', _make_isolated_filter)

    # Walk/ray: extend in a direction until hitting something
    def _ray(g, r, c, dr, dc, bg=0):
        """Walk from (r,c) in direction (dr,dc) until hitting non-bg or edge."""
        gd = _unwrap(g)
        h, w = len(gd), len(gd[0]) if gd else 0
        path = []
        nr, nc = r + dr, c + dc
        while 0 <= nr < h and 0 <= nc < w and gd[nr][nc] == bg:
            path.append([nr, nc])
            nr += dr
            nc += dc
        return path

    def _ray_until(g, r, c, dr, dc, stop_color=None):
        """Walk from (r,c) until hitting stop_color or edge."""
        gd = _unwrap(g)
        h, w = len(gd), len(gd[0]) if gd else 0
        path = []
        nr, nc = r + dr, c + dc
        while 0 <= nr < h and 0 <= nc < w:
            val = gd[nr][nc]
            path.append([nr, nc, val])
            if stop_color is not None and val == stop_color:
                break
            nr += dr
            nc += dc
        return path

    env.define('ray', _ray)
    env.define('ray-until', _ray_until)
