"""Proposed public-focus reconstruction family, separate from the canonical task.

Focus parent: public ARC evaluation challenge 898e7135. Only its two visible
demonstration pairs and public query input were consulted. No test-answer source
was read. The visible-byte hash follows reviewer_support.public_challenge_bytes.
This is an inferred focus-inspired prototype, not verified ancestry or official
evaluation correctness and not approval for training.

API: SETTINGS; render_program(resolution); sample_input(seed, index);
python_expected(grid, resolution); analyze_input(grid).
The independent Python implementation is a cross-check. Exported labels must
come from executing render_program through the protected Racket bridge.

Grammar: black background; one uniquely identifiable monochrome rectangular
carrier with a complete border and three to six internal 4-connected zero holes;
detached monochrome source pieces made from uniform 2x2 or 3x3 cell blocks.
Each hole's D4 shape class has matching source multiplicity and exactly one
color. Repeated same-shape pieces are permitted only with that same color.
At least one singleton hole is required. Distractor components must be smaller
than one block. The feasible block size must be unique. Both render resolutions
must stay within ARC's 30x30 bounds. Unsupported/ambiguous inputs fail visibly.

The generator uses three to six holes, independently oriented source pieces,
random carrier and piece colors/positions, block sizes 2/3, and singleton noise.
Its bounded 29/30-cell canvases reserve separated placement slots; the parser
also admits both visible focus examples and their public query input.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import random

SETTINGS = ("piece", "template")
DEFAULT = "piece"
FOCUS_PARENT = "898e7135"
FOCUS_PUBLIC_CHALLENGE_SHA256 = "98c4b873531603b1812537135810ecd86954302f580894bb2d9ac75652e069fe"
VERSION = "focus-reconstruction-v1"
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SHAPES = {
    "unit": ((0, 0),),
    "elbow": ((0, 0), (1, 0), (1, 1)),
    "ell": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "tee": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "cross": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
}


def _setting(resolution):
    if type(resolution) is not str or resolution not in SETTINGS:
        raise ValueError(f"resolution must be one of {SETTINGS!r}")
    return resolution


def _validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid dimensions must be in 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors")


def _normalize(cells):
    low_r = min(r for r, c in cells)
    low_c = min(c for r, c in cells)
    return tuple(sorted((r - low_r, c - low_c) for r, c in cells))


def _transforms(cells):
    cells = _normalize(cells)
    variants = set()
    for mirror in (False, True):
        current = tuple((r, -c if mirror else c) for r, c in cells)
        for _ in range(4):
            current = _normalize(current)
            variants.add(current)
            current = tuple((c, -r) for r, c in current)
    return tuple(sorted(variants))


def _signature(cells):
    return min(_transforms(cells))


def _components(grid, skip=0):
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, color in enumerate(row) if color != skip}
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        stack, cells = [start], []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in _CARDINAL:
                neighbor = r + dr, c + dc
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        result.append((color, tuple(sorted(cells))))
    return result


def _carrier(grid):
    candidates = []
    for color in sorted({v for row in grid for v in row} - {0}):
        cells = [(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == color]
        r1, c1 = min(r for r, c in cells), min(c for r, c in cells)
        r2, c2 = max(r for r, c in cells), max(c for r, c in cells)
        if r2 - r1 < 2 or c2 - c1 < 2:
            continue
        crop = [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]
        if not any(0 in row for row in crop):
            continue
        if any(v not in (0, color) for row in crop for v in row):
            continue
        if (any(v != color for row in (crop[0], crop[-1]) for v in row)
                or any(row[0] != color or row[-1] != color for row in crop)):
            continue
        candidates.append((color, (r1, c1, r2, c2), crop))
    if len(candidates) != 1:
        raise ValueError(f"expected one perforated carrier, got {len(candidates)}")
    return candidates[0]


def _infer(grid):
    _validate_grid(grid)
    carrier_color, bbox, template = _carrier(grid)
    holes = [cells for color, cells in _components(template, skip=carrier_color)]
    if not 3 <= len(holes) <= 6 or not any(len(hole) == 1 for hole in holes):
        raise ValueError("expected three to six holes including a singleton")
    hole_classes = Counter(_signature(hole) for hole in holes)
    outside = [(color, cells) for color, cells in _components(grid)
               if color != carrier_color]
    fits = []
    for scale in (2, 3):
        if len(template) * scale > 30 or len(template[0]) * scale > 30:
            continue
        pieces = [(color, cells) for color, cells in outside
                  if len(cells) >= scale * scale]
        if len(pieces) != len(holes):
            continue
        by_shape = defaultdict(list)
        exact_blocks = True
        for color, cells in pieces:
            normalized = _normalize(cells)
            unit = tuple(sorted({(r // scale, c // scale) for r, c in normalized}))
            if len(cells) != len(unit) * scale * scale:
                exact_blocks = False
                break
            by_shape[_signature(unit)].append(color)
        if not exact_blocks:
            continue
        if Counter({shape: len(colors) for shape, colors in by_shape.items()}) != hole_classes:
            continue
        if any(len(set(colors)) != 1 for colors in by_shape.values()):
            continue
        output = [row[:] for row in template]
        for hole in holes:
            color = by_shape[_signature(hole)][0]
            for r, c in hole:
                output[r][c] = color
        fits.append((scale, output))
    if len(fits) != 1:
        raise ValueError(f"expected one unambiguous block reconstruction, got {len(fits)}")
    scale, output = fits[0]
    return {
        "carrier_color": carrier_color,
        "carrier_bbox": bbox,
        "carrier_shape": (len(template), len(template[0])),
        "block_scale": scale,
        "hole_count": len(holes),
        "hole_class_count": len(hole_classes),
        "template_output": output,
    }


def analyze_input(grid):
    """Return input-derived structure, without a labeled query answer."""
    result = _infer(grid)
    return {key: value for key, value in result.items() if key != "template_output"}


def python_expected(grid, resolution):
    """Independent cross-check; matching Racket remains label authority."""
    _setting(resolution)
    inferred = _infer(grid)
    scale = inferred["block_scale"] if resolution == "piece" else 1
    return [[value for value in row for _ in range(scale)]
            for row in inferred["template_output"] for _ in range(scale)]


def _put(grid, cells, color, top, left, scale=1):
    for r, c in cells:
        for dr in range(scale):
            for dc in range(scale):
                grid[top + scale * r + dr][left + scale * c + dc] = color


def sample_input(seed, index):
    """Draw a fresh lawful input; the hidden output setting is not an input."""
    if type(seed) is not int or type(index) is not int or index < 0:
        raise ValueError("seed must be an integer and index a nonnegative integer")
    digest = hashlib.sha256(f"{VERSION}:{seed}:{index}:input".encode()).digest()
    rng = random.Random(int.from_bytes(digest, "big"))
    scale = rng.choice((2, 3))
    hole_count = 3 + index % 4
    names = ["unit"] + rng.sample(["elbow", "ell", "tee", "cross"],
                                  min(hole_count - 1, 4))
    if hole_count == 6:
        names.append("unit")
    colors = rng.sample(range(1, 10), 7)
    carrier_color, noise_color = colors[:2]
    class_colors = dict(zip(_SHAPES, colors[2:]))
    carrier_h, carrier_w = rng.choice((8, 9)), rng.choice((8, 9))
    hole_layout = None
    for _ in range(120):
        used, placements = set(), []
        for name in sorted(names, key=lambda name: -len(_SHAPES[name])):
            shape = rng.choice(_transforms(_SHAPES[name]))
            sh, sw = max(r for r, c in shape) + 1, max(c for r, c in shape) + 1
            options = []
            for top in range(1, carrier_h - sh):
                for left in range(1, carrier_w - sw):
                    translated = {(r + top, c + left) for r, c in shape}
                    if not any((r + dr, c + dc) in used
                               for r, c in translated
                               for dr, dc in ((0, 0),) + _CARDINAL):
                        options.append((top, left, translated))
            if not options:
                break
            top, left, translated = rng.choice(options)
            used.update(translated)
            placements.append((name, shape, top, left))
        if len(placements) == hole_count:
            hole_layout = placements
            break
    if hole_layout is None:
        raise RuntimeError(f"bounded carrier placement exhausted for {seed=}, {index=}")
    height, width = rng.choice((29, 30)), rng.choice((29, 30))
    grid = [[0] * width for _ in range(height)]
    slots = [(r, c) for r in (0, 10, 20) for c in (0, 10, 20)]
    rng.shuffle(slots)
    cr, cc = slots.pop()
    cr += rng.randrange(10 - carrier_h)
    cc += rng.randrange(10 - carrier_w)
    for r in range(cr, cr + carrier_h):
        for c in range(cc, cc + carrier_w):
            grid[r][c] = carrier_color
    for name, shape, top, left in hole_layout:
        _put(grid, shape, 0, cr + top, cc + left)
    for name in names:
        shape = rng.choice(_transforms(_SHAPES[name]))
        sh = (max(r for r, c in shape) + 1) * scale
        sw = (max(c for r, c in shape) + 1) * scale
        top, left = slots.pop()
        top += rng.randrange(10 - sh)
        left += rng.randrange(10 - sw)
        _put(grid, shape, class_colors[name], top, left, scale)
    noise_sites = [(r, c) for r in range(height) for c in range(width)
                   if not (cr <= r < cr + carrier_h and cc <= c < cc + carrier_w)
                   and grid[r][c] == 0
                   and all(grid[rr][ccc] == 0
                           for rr in range(max(0, r - 1), min(height, r + 2))
                           for ccc in range(max(0, c - 1), min(width, c + 2)))]
    rng.shuffle(noise_sites)
    added = 0
    for r, c in noise_sites:
        if all(grid[rr][ccc] == 0
               for rr in range(max(0, r - 1), min(height, r + 2))
               for ccc in range(max(0, c - 1), min(width, c + 2))):
            grid[r][c] = noise_color
            added += 1
            if added == 8:
                break
    return grid


_RACKET_TEMPLATE = """(lambda (g)
  (let ()
    ;; Find the perforated carrier, match block-scaled pieces to its holes,
    ;; and reconstruct its colors. The episode fixes the output resolution.
    ;; D4 matching allows rotations and reflections; small fragments are noise.
    (define (shape-match? a b)
      (member (sort (normalize-cells a) cell<) (all-transforms b)))
    (define carriers
      (filter
        (lambda (item) item)
        (for/list ((color (grid-colors g 0)))
          (let* ((box (bbox-of-cells (find-color g color)))
                 (rlo (first box)) (clo (second box))
                 (rhi (third box)) (chi (fourth box)))
            (if (and (>= (- rhi rlo) 2) (>= (- chi clo) 2)
                     (> (count-color (subgrid g rlo clo rhi chi) 0) 0)
                     (for/and ((p (positions-in-rect rlo clo rhi chi)))
                       (let ((r (first p)) (c (second p)))
                         (if (or (= r rlo) (= r rhi) (= c clo) (= c chi))
                             (= (at g r c) color)
                             (or (= (at g r c) color) (= (at g r c) 0))))))
                (list color rlo clo rhi chi)
                #f)))))
    (unless (= (length carriers) 1)
      (error 'focus-reconstruction "expected one perforated carrier"))
    (define carrier (first carriers))
    (define carrier-color (first carrier))
    (define plate (subgrid g (second carrier) (third carrier)
                           (fourth carrier) (fifth carrier)))
    (define holes (objects plate carrier-color))
    (unless (and (<= 3 (length holes) 6)
                 (for/or ((hole holes)) (= (obj-size hole) 1)))
      (error 'focus-reconstruction "expected three to six holes with a singleton"))
    (define outside (filter (lambda (o) (not (= (obj-color o) carrier-color)))
                            (objects g 0)))
    (define (attempt scale)
      (let* ((area (* scale scale))
             (active (filter (lambda (o) (>= (obj-size o) area)) outside))
             (pieces
               (for/list ((o active))
                 (list (obj-color o)
                   (remove-duplicates
                     (for/list ((p (normalize-cells (obj-cells o))))
                       (list (quotient (first p) scale)
                             (quotient (second p) scale))))
                   (obj-size o)))))
        (if (and (<= (* (rows plate) scale) 30)
                 (<= (* (cols plate) scale) 30)
                 (= (length pieces) (length holes))
                 (for/and ((piece pieces))
                   (= (third piece) (* area (length (second piece)))))
                 (for/and ((hole holes))
                   (= 1 (length
                          (remove-duplicates
                            (for/list ((piece pieces)
                                       #:when (shape-match? (obj-cells hole)
                                                             (second piece)))
                              (first piece))))))
                 (for/and ((piece pieces))
                   (= (length (filter
                                (lambda (hole)
                                  (shape-match? (obj-cells hole) (second piece)))
                                holes))
                      (length (filter
                                (lambda (other)
                                  (shape-match? (second other) (second piece)))
                                pieces)))))
            (list scale
              (for/fold ((out plate)) ((hole holes))
                (let ((piece
                        (find-first
                          (lambda (candidate)
                            (shape-match? (obj-cells hole) (second candidate)))
                          pieces)))
                  (recolor-cells out (obj-cells hole) (first piece)))))
            #f)))
    (define fits (filter (lambda (item) item) (map attempt (list 2 3))))
    (unless (= (length fits) 1)
      (error 'focus-reconstruction "expected one unambiguous block reconstruction"))
    (define fit (first fits))
    (upscale (second fit) __OUTPUT_SCALE__)))"""


def render_program(resolution):
    """Materialize the exact matching Racket program for one episode setting."""
    _setting(resolution)
    expression = "(first fit)" if resolution == "piece" else "1"
    return _RACKET_TEMPLATE.replace("__OUTPUT_SCALE__", expression)
