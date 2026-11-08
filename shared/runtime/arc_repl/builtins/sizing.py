"""
Sizing builtins — operations that change grid dimensions.

Covers: upscale, downscale, self-tile, crop-object, extract-largest,
split-at-separator, count-blocks, encode-bar, draw-diagonal,
assemble-at, find-color-pairs.
"""

from collections import deque
from .helpers import Grid, _unwrap, _call


def _find_components(data, bg=0, same_color=True):
    """Find 4-connected components of non-bg cells. If same_color, only connect same-colored cells."""
    H, W = len(data), len(data[0])
    visited = [[False]*W for _ in range(H)]
    components = []
    for r in range(H):
        for c in range(W):
            if visited[r][c] or data[r][c] == bg:
                continue
            color = data[r][c]
            comp = []
            queue = deque([(r, c)])
            visited[r][c] = True
            while queue:
                cr, cc = queue.popleft()
                comp.append((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0 <= nr < H and 0 <= nc < W and not visited[nr][nc] and data[nr][nc] != bg:
                        if not same_color or data[nr][nc] == color:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
            components.append({'cells': comp, 'color': color, 'size': len(comp)})
    return components


def register(env):
    """Register sizing builtins into env."""

    # ============================================================
    # Grid Scaling
    # ============================================================

    def _upscale(g, factor):
        """Scale every cell to a factor×factor block."""
        data = _unwrap(g)
        H, W = len(data), len(data[0])
        return Grid([[data[r // factor][c // factor]
                       for c in range(W * factor)]
                      for r in range(H * factor)])

    env.define('upscale', _upscale)

    def _downscale(g, factor, fn=None):
        """Reduce grid by factor. fn(block) → value. Default: most common non-bg."""
        data = _unwrap(g)
        H, W = len(data), len(data[0])
        out = []
        for br in range(H // factor):
            row = []
            for bc in range(W // factor):
                block = []
                for dr in range(factor):
                    for dc in range(factor):
                        block.append(data[br*factor+dr][bc*factor+dc])
                if fn:
                    row.append(_call(fn, block))
                else:
                    # Default: most common non-zero, or 0
                    non_zero = [v for v in block if v != 0]
                    if non_zero:
                        from collections import Counter
                        row.append(Counter(non_zero).most_common(1)[0][0])
                    else:
                        row.append(0)
            out.append(row)
        return Grid(out)

    env.define('downscale', _downscale)

    def _self_tile(g, pred=None):
        """Each cell where pred(val) is true → copy of grid. Others → bg block.
        Default pred: non-zero. Output size = N*H × N*W where N = max(H,W)...
        actually output = H*H × W*W (each cell becomes an H×W block)."""
        data = _unwrap(g)
        H, W = len(data), len(data[0])
        OH, OW = H * H, W * W
        out = [[0]*OW for _ in range(OH)]
        for br in range(H):
            for bc in range(W):
                val = data[br][bc]
                include = False
                if pred:
                    include = _call(pred, val)
                    # Handle Scheme truthiness
                    include = include is not False and include is not None
                else:
                    include = val != 0
                if include:
                    for r in range(H):
                        for c in range(W):
                            out[br*H+r][bc*W+c] = data[r][c]
        return Grid(out)

    env.define('self-tile', _self_tile)

    # ============================================================
    # Object Extraction & Cropping
    # ============================================================

    def _crop_object(g, obj):
        """Extract an object to its own grid, cropped to bounding box."""
        data = _unwrap(g)
        cells = obj['cells'] if isinstance(obj, dict) else obj
        cell_set = set((r, c) if isinstance((r, c), tuple) else (r[0], r[1]) for r, c in cells) if not isinstance(cells[0], tuple) else set(cells)
        # Normalize cells
        cell_set = set()
        for cell in cells:
            if isinstance(cell, (list, tuple)):
                cell_set.add((cell[0], cell[1]))
        min_r = min(r for r, c in cell_set)
        max_r = max(r for r, c in cell_set)
        min_c = min(c for r, c in cell_set)
        max_c = max(c for r, c in cell_set)
        out = [[0]*(max_c-min_c+1) for _ in range(max_r-min_r+1)]
        for r, c in cell_set:
            out[r-min_r][c-min_c] = data[r][c]
        return Grid(out)

    env.define('crop-object', _crop_object)

    def _largest_object(g, bg=0):
        """Return the connected component with the most cells (as proper object dict)."""
        data = _unwrap(g)
        comps = _find_components(data, bg, same_color=True)
        if not comps:
            return None
        best = max(comps, key=lambda c: c['size'])
        # Add bbox for compatibility with obj-bbox
        cells = best['cells']
        min_r = min(r for r, c in cells)
        max_r = max(r for r, c in cells)
        min_c = min(c for r, c in cells)
        max_c = max(c for r, c in cells)
        best['bbox'] = [min_r, min_c, max_r, max_c]
        best['center_r'] = (min_r + max_r) / 2
        best['center_c'] = (min_c + max_c) / 2
        return best

    env.define('largest-object', _largest_object)

    def _extract_largest(g, bg=0):
        """Find largest component, crop to bounding box."""
        data = _unwrap(g)
        obj = _largest_object(g, bg)
        if obj is None:
            return g
        return _crop_object(g, obj)

    env.define('extract-largest', _extract_largest)

    def _split_at_separator(g, bg=0):
        """Split grid into sections by separator rows/columns.
        A separator = full row/col of one color not appearing elsewhere.
        Falls back to any full row/col of uniform non-bg color."""
        data = _unwrap(g)
        H, W = len(data), len(data[0])

        # Find candidate separator rows (uniform non-bg)
        row_candidates = []
        for r in range(H):
            vals = set(data[r])
            if len(vals) == 1 and list(vals)[0] != bg:
                row_candidates.append((r, list(vals)[0]))

        # Find candidate separator cols
        col_candidates = []
        for c in range(W):
            vals = set(data[r][c] for r in range(H))
            if len(vals) == 1 and list(vals)[0] != bg:
                col_candidates.append((c, list(vals)[0]))

        # Prefer separators with a color unique to separator rows
        def filter_unique(candidates, is_row=True):
            if not candidates:
                return []
            cand_set = set(r for r, v in candidates)
            non_cand_colors = set()
            for r in range(H):
                for c in range(W):
                    if is_row and r in cand_set:
                        continue
                    if not is_row and c in cand_set:
                        continue
                    non_cand_colors.add(data[r][c])
            # Keep candidates whose color doesn't appear elsewhere
            unique = [(r, v) for r, v in candidates if v not in non_cand_colors]
            return [r for r, v in unique] if unique else [r for r, v in candidates]

        sep_rows = filter_unique(row_candidates, is_row=True)
        sep_cols = filter_unique(col_candidates, is_row=False)

        # Split by rows
        if sep_rows:
            sections = []
            prev = 0
            for sr in sep_rows:
                if sr > prev:
                    section = [list(data[r]) for r in range(prev, sr)]
                    sections.append(Grid(section))
                prev = sr + 1
            if prev < H:
                sections.append(Grid([list(data[r]) for r in range(prev, H)]))
            return sections

        # Split by cols
        if sep_cols:
            sections = []
            prev = 0
            for sc in sep_cols:
                if sc > prev:
                    section = [[data[r][c] for c in range(prev, sc)] for r in range(H)]
                    sections.append(Grid(section))
                prev = sc + 1
            if prev < W:
                sections.append(Grid([[data[r][c] for c in range(prev, W)] for r in range(H)]))
            return sections

        return [g]

    env.define('split-at-separator', _split_at_separator)

    # ============================================================
    # Counting & Encoding
    # ============================================================

    def _count_blocks(g, color, size):
        """Count non-overlapping size×size solid blocks of color."""
        data = _unwrap(g)
        H, W = len(data), len(data[0])
        used = set()
        count = 0
        for r in range(H - size + 1):
            for c in range(W - size + 1):
                if (r, c) in used:
                    continue
                all_match = True
                for dr in range(size):
                    for dc in range(size):
                        if data[r+dr][c+dc] != color:
                            all_match = False
                            break
                    if not all_match:
                        break
                if all_match:
                    count += 1
                    for dr in range(size):
                        for dc in range(size):
                            used.add((r+dr, c+dc))
        return count

    env.define('count-blocks', _count_blocks)

    def _encode_bar(count, max_len, on_color=1, off_color=0):
        """Create 1×max_len grid: count cells of on_color, rest off_color."""
        return Grid([[on_color]*count + [off_color]*(max_len - count)])

    env.define('encode-bar', _encode_bar)

    # ============================================================
    # Drawing
    # ============================================================

    def _draw_diagonal(g, offset, color, direction='down-right'):
        """Draw a 45° diagonal: row = col + offset (down-right) or row = -col + offset (down-left).
        Only draws on bg (0) cells."""
        data = _unwrap(g)
        H, W = len(data), len(data[0])
        out = [list(row) for row in data]
        for r in range(H):
            if direction == 'down-right':
                c = r - offset
            else:
                c = offset - r
            if 0 <= c < W and out[r][c] == 0:
                out[r][c] = color
        return Grid(out)

    env.define('draw-diagonal', _draw_diagonal)

    # ============================================================
    # Assembly
    # ============================================================

    def _assemble_at(g, anchor_color, size):
        """Find all anchor_color cells. For each, collect nearby non-bg, non-anchor cells
        and their offsets. Place at those offsets in a size×size output centered on anchor."""
        data = _unwrap(g)
        H, W = len(data), len(data[0])
        center = size // 2
        out = [[0]*size for _ in range(size)]
        out[center][center] = anchor_color

        anchors = [(r, c) for r in range(H) for c in range(W) if data[r][c] == anchor_color]

        for ar, ac in anchors:
            for dr in range(-size, size+1):
                for dc in range(-size, size+1):
                    nr, nc = ar+dr, ac+dc
                    if 0 <= nr < H and 0 <= nc < W:
                        val = data[nr][nc]
                        if val != 0 and val != anchor_color:
                            or_ = center + dr
                            oc = center + dc
                            if 0 <= or_ < size and 0 <= oc < size:
                                out[or_][oc] = val

        return Grid(out)

    env.define('assemble-at', _assemble_at)

    def _find_color_pairs(g, bg=0):
        """Find isolated 2-cell horizontal pairs not part of larger objects.
        Returns dict mapping old_color → new_color (pair = (new, old))."""
        data = _unwrap(g)
        H, W = len(data), len(data[0])

        # Find the largest object to exclude
        comps = _find_components(data, bg)
        if not comps:
            return {}
        largest_size = max(c['size'] for c in comps)
        large_cells = set()
        for comp in comps:
            if comp['size'] >= largest_size * 0.5:  # exclude large objects
                for cell in comp['cells']:
                    large_cells.add(tuple(cell))

        mapping = {}
        for r in range(H):
            for c in range(W - 1):
                a, b = data[r][c], data[r][c+1]
                if a != bg and b != bg and (r, c) not in large_cells and (r, c+1) not in large_cells:
                    # Check it's isolated (not part of bigger cluster)
                    neighbors_a = sum(1 for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
                                      if 0 <= r+dr < H and 0 <= c+dc < W and data[r+dr][c+dc] != bg
                                      and (r+dr, c+dc) != (r, c+1))
                    neighbors_b = sum(1 for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
                                       if 0 <= r+dr < H and 0 <= c+1+dc < W and data[r+dr][c+1+dc] != bg
                                       and (r+dr, c+1+dc) != (r, c))
                    if neighbors_a == 0 and neighbors_b == 0:
                        mapping[b] = a  # b → a (first replaces second)

        return mapping

    env.define('find-color-pairs', _find_color_pairs)

    # ============================================================
    # Reflection & Symmetry
    # ============================================================

    def _kaleidoscope(g):
        """4-fold reflection: output = 2H × 2W with all 4 reflections.
        Bottom-right = original, bottom-left = flip-H, top-right = flip-V, top-left = 180°."""
        data = _unwrap(g)
        H, W = len(data), len(data[0])
        out = [[0]*(W*2) for _ in range(H*2)]
        for r in range(H):
            for c in range(W):
                v = data[r][c]
                out[H+r][W+c] = v          # bottom-right: original
                out[H+r][W-1-c] = v        # bottom-left: flip-H
                out[H-1-r][W+c] = v        # top-right: flip-V
                out[H-1-r][W-1-c] = v      # top-left: 180°
        return Grid(out)

    env.define('kaleidoscope', _kaleidoscope)

    def _symmetric(g, axis='lr'):
        """Check if grid is symmetric. axis: 'lr' (left-right), 'ud' (up-down),
        '180' (180° rotation), 'diag' (main diagonal)."""
        data = _unwrap(g)
        H, W = len(data), len(data[0])
        # Unwrap StrLit
        axis = axis.value if hasattr(axis, 'value') else str(axis)
        if axis == 'lr':
            return all(data[r][c] == data[r][W-1-c] for r in range(H) for c in range(W))
        elif axis == 'ud':
            return all(data[r][c] == data[H-1-r][c] for r in range(H) for c in range(W))
        elif axis == '180':
            return all(data[r][c] == data[H-1-r][W-1-c] for r in range(H) for c in range(W))
        elif axis == 'diag':
            if H != W:
                return False
            return all(data[r][c] == data[c][r] for r in range(H) for c in range(W))
        return False

    env.define('symmetric?', _symmetric)

    # ============================================================
    # Generalized Scaling
    # ============================================================

    def _scale_map(g, row_scales, col_scales):
        """Non-uniform upscale. row_scales and col_scales are lists of integers
        specifying how many output rows/cols each input row/col expands to.
        E.g. (scale-map grid (list 2 1 2) (list 2 1 2)) for 3×3 → 5×5."""
        data = _unwrap(g)
        H, W = len(data), len(data[0])

        # Build row mapping: output row → input row
        row_map = []
        for i, s in enumerate(row_scales):
            row_map.extend([i] * s)

        # Build col mapping
        col_map = []
        for i, s in enumerate(col_scales):
            col_map.extend([i] * s)

        OH, OW = len(row_map), len(col_map)
        return Grid([[data[row_map[r]][col_map[c]] for c in range(OW)] for r in range(OH)])

    env.define('scale-map', _scale_map)

    def _stamp_grid(pattern, stamp, bg=0, pred=None):
        """Use pattern (HxW) as layout map, stamp (SxT) as thing to tile.
        Output = (H*S)×(W*T). For each cell in pattern, if pred(val) is true
        (default: != bg), place a copy of stamp at that block position."""
        pat = _unwrap(pattern)
        st = _unwrap(stamp)
        PH, PW = len(pat), len(pat[0])
        SH, SW = len(st), len(st[0])
        OH, OW = PH * SH, PW * SW
        out = [[bg] * OW for _ in range(OH)]
        for br in range(PH):
            for bc in range(PW):
                val = pat[br][bc]
                include = False
                if pred:
                    include = _call(pred, val)
                    include = include is not False and include is not None
                else:
                    include = val != bg
                if include:
                    for r in range(SH):
                        for c in range(SW):
                            out[br*SH+r][bc*SW+c] = st[r][c]
        return Grid(out)

    env.define('stamp-grid', _stamp_grid)

    # ============================================================
    # Statistics
    # ============================================================

    def _grid_mode(g, bg=None):
        """Most common value in grid. If bg given, exclude it."""
        data = _unwrap(g)
        from collections import Counter
        counts = Counter(v for row in data for v in row if bg is None or v != bg)
        return counts.most_common(1)[0][0] if counts else 0

    env.define('mode', _grid_mode)

    def _grid_minority(g, bg=0):
        """Least common non-bg value in grid."""
        data = _unwrap(g)
        from collections import Counter
        counts = Counter(v for row in data for v in row if v != bg)
        return counts.most_common()[-1][0] if counts else 0

    env.define('minority', _grid_minority)

    # ============================================================
    # Half-grid operations
    # ============================================================

    def _zip_halves(g, fn, sep_color=None):
        """Split grid by separator row/col, apply fn(val_top, val_bot) element-wise.
        Returns a grid the size of one half."""
        data = _unwrap(g)
        H, W = len(data), len(data[0])
        # Unwrap StrLit
        if sep_color is not None and hasattr(sep_color, 'value'):
            sep_color = sep_color.value

        # Find separator row — prefer one that creates equal-sized halves,
        # or one with a unique color not seen elsewhere
        sep = None
        sep_candidates = []
        for r in range(H):
            vals = set(data[r])
            if len(vals) == 1:
                v = list(vals)[0]
                if v != 0 and (sep_color is None or v == sep_color):
                    sep_candidates.append((r, v))

        if sep_candidates:
            # Prefer separator with unique color (not appearing in non-separator rows)
            non_sep_colors = set()
            sep_rows_set = set(r for r, v in sep_candidates)
            for r in range(H):
                if r not in sep_rows_set:
                    for c in range(W):
                        non_sep_colors.add(data[r][c])

            for r, v in sep_candidates:
                if v not in non_sep_colors:
                    sep = r
                    break

            # Fallback: pick the one closest to center
            if sep is None:
                sep = min(sep_candidates, key=lambda x: abs(x[0] - H/2))[0]

        if sep is not None:
            top = [data[r] for r in range(sep)]
            bot = [data[r] for r in range(sep+1, H)]
            min_h = min(len(top), len(bot))
            return Grid([[_call(fn, top[r][c], bot[r][c]) for c in range(W)] for r in range(min_h)])

        # Try separator col
        for c in range(W):
            vals = set(data[r][c] for r in range(H))
            if len(vals) == 1 and (sep_color is None or list(vals)[0] == sep_color):
                if list(vals)[0] != 0:
                    sep = c
                    break

        if sep is not None:
            left = [[data[r][c] for c in range(sep)] for r in range(H)]
            right = [[data[r][c] for c in range(sep+1, W)] for r in range(H)]
            min_w = min(len(left[0]), len(right[0]))
            return Grid([[_call(fn, left[r][c], right[r][c]) for c in range(min_w)] for r in range(H)])

        return g

    env.define('zip-halves', _zip_halves)

    # ============================================================
    # Output size inference (from training examples)
    # ============================================================

    def _infer_output_size(task_dict):
        """From a task dict, infer the output dimensions.
        Returns [height, width] based on training examples.
        Useful for unequal-size tasks."""
        train = task_dict.get('train', [])
        if not train:
            return None
        # Check if output size is constant
        sizes = [(len(p['output']), len(p['output'][0])) for p in train]
        if len(set(sizes)) == 1:
            return list(sizes[0])
        # Check if output is a function of input
        ratios = [(len(p['output'])/len(p['input']), len(p['output'][0])/len(p['input'][0])) for p in train]
        if len(set(ratios)) == 1:
            return list(ratios[0])  # return ratio, caller multiplies
        return None

    env.define('infer-output-size', _infer_output_size)
