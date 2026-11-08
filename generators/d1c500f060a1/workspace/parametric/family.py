"""Transform first, then optionally order pieces by the transformed accent."""
from __future__ import annotations

from collections import Counter, deque
from pathlib import Path

PACK_ORDERS = ("as_found", "accent_scan")
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
if not CANONICAL.startswith("(rule! ") or not CANONICAL.endswith(")"):
    raise ValueError("canonical.rkt must contain the exact selected rule expression")


def parse_settings(settings):
    if (type(settings) is not dict or set(settings) != {"pack_order"}
            or type(settings["pack_order"]) is not str
            or settings["pack_order"] not in PACK_ORDERS):
        raise ValueError("settings must be exactly pack_order=as_found or accent_scan")
    return {"pack_order": settings["pack_order"]}


def rotate_cw(grid): return [list(row) for row in zip(*grid[::-1])]
def rotate_180(grid): return rotate_cw(rotate_cw(grid))
def rotate_ccw(grid): return rotate_cw(rotate_180(grid))
def flip_lr(grid): return [list(reversed(row)) for row in grid]
def flip_ud(grid): return [list(row) for row in reversed(grid)]


def transform(grid, code):
    return {1: rotate_cw, 2: rotate_180, 3: rotate_ccw,
            4: flip_lr, 5: flip_ud}[code](grid)


def _connected(cells):
    cells = set(cells)
    if not cells: return False
    seen = {next(iter(cells))}; queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in cells and point not in seen:
                seen.add(point); queue.append(point)
    return seen == cells


def analyze(grid):
    if (type(grid) is not list or not 5 <= len(grid) <= 30
            or type(grid[0]) is not list or not 5 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a rectangular 5..30 ARC grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be exact integer ARC colors 0..9")
    codes = [value for value in grid[0] if value]
    if not 4 <= len(codes) <= 5 or len(set(codes)) != len(codes) or any(v not in range(1, 6) for v in codes):
        raise ValueError("row 0 needs four or five distinct codes from 1..5")
    if any(grid[1]): raise ValueError("row 1 must be blank")
    cells = [(r, c) for r, row in enumerate(grid[2:], start=2)
             for c, value in enumerate(row) if value]
    if len(cells) < 5 or not _connected(cells):
        raise ValueError("body needs one connected motif of at least five cells")
    counts = Counter(grid[r][c] for r, c in cells)
    singletons = [color for color, count in counts.items() if count == 1]
    if len(counts) != 2 or len(singletons) != 1:
        raise ValueError("motif needs exactly two colors and one singleton accent")
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    r1, c1 = max(r for r, _ in cells), max(c for _, c in cells)
    crop = [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]
    if len(crop) == len(crop[0]):
        raise ValueError("motif crop must be non-square so transform keys stay distinct")
    accent = singletons[0]
    cue = next((r, c) for r, row in enumerate(crop) for c, value in enumerate(row) if value == accent)
    if cue not in {(0, 0), (0, len(crop[0]) - 1), (len(crop) - 1, 0),
                   (len(crop) - 1, len(crop[0]) - 1)}:
        raise ValueError("singleton accent must occupy a motif-crop corner")
    return {"codes": codes, "crop": crop, "accent_color": accent,
            "bbox": (r0, c0, r1, c1), "accent": cue}


def accent_key(piece, accent_color):
    r, c = next((r, c) for r, row in enumerate(piece) for c, value in enumerate(row)
                if value == accent_color)
    return r, c, len(piece), len(piece[0])


def transformed_pieces(info):
    return [transform(info["crop"], code) for code in info["codes"]]


def transformed_keys(info):
    return [accent_key(piece, info["accent_color"]) for piece in transformed_pieces(info)]


def pack(pieces):
    out_h = max(len(piece) for piece in pieces)
    out_w = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    if out_h > 30 or out_w > 30:
        raise ValueError("packed output exceeds ARC dimensions")
    out = [[0] * out_w for _ in range(out_h)]
    c0 = 0
    for piece in pieces:
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value: out[r][c0 + c] = value
        c0 += len(piece[0]) + 1
    return out


def apply(grid, settings):
    order = parse_settings(settings)["pack_order"]
    info = analyze(grid)
    pieces = transformed_pieces(info)
    if order == "accent_scan":
        pieces = [pieces[index] for index in sorted(range(len(pieces)),
                  key=lambda index: accent_key(pieces[index], info["accent_color"]))]
    return pack(pieces)


ALTERNATE = r'''(rule! (let ((dummy 0))
  (define (crop-nz grid) (crop-to-content grid 0))
  (define (transform-code grid code)
    (cond ((= code 1) (rotate-cw grid))
          ((= code 2) (rotate-180 grid))
          ((= code 3) (rotate-ccw grid))
          ((= code 4) (flip-lr grid))
          ((= code 5) (flip-ud grid))
          (else grid)))
  (define (shape-place out crop top left)
    (for*/fold ((acc out)) ((r (in-range (rows crop))) (c (in-range (cols crop))))
      (let ((v (at crop r c)))
        (if (= v 0) acc (set-cell acc (+ top r) (+ left c) v)))))
  (define (key-less? a b)
    (cond ((< (first a) (first b)) #t)
          ((> (first a) (first b)) #f)
          ((< (second a) (second b)) #t)
          ((> (second a) (second b)) #f)
          ((< (third a) (third b)) #t)
          ((> (third a) (third b)) #f)
          (else (< (fourth a) (fourth b)))))
  (define (insert-item item xs)
    (cond ((empty? xs) (list item))
          ((key-less? (second item) (second (first xs))) (cons item xs))
          (else (cons (first xs) (insert-item item (rest xs))))))
  (define (sort-items xs)
    (if (empty? xs) '()
        (insert-item (first xs) (sort-items (rest xs)))))
  (define codes (filter (lambda (v) (not (= v 0))) (row g 0)))
  (define base (crop-nz (subgrid g 2 0 (- (rows g) 1) (- (cols g) 1))))
  (define values
    (map (lambda (p) (at base (first p) (second p)))
         (filter (lambda (p) (not (= (at base (first p) (second p)) 0)))
                 (grid-positions base))))
  (define accent-color
    (first (filter (lambda (v)
             (= 1 (length (filter (lambda (x) (= x v)) values))))
           values)))
  (define (accent-key piece)
    (let ((p (first (find-color piece accent-color))))
      (list (first p) (second p) (rows piece) (cols piece))))
  (define pieces (map (lambda (code) (transform-code base code)) codes))
  (define items (map (lambda (piece) (list piece (accent-key piece))) pieces))
  (define ordered-pieces (map first (sort-items items)))
  (define out-h (apply max (map rows ordered-pieces)))
  (define out-w (+ (apply + (map cols ordered-pieces))
                     (max 0 (- (length ordered-pieces) 1))))
  (let pack ((remaining ordered-pieces) (c0 0)
             (out (empty-grid out-h out-w 0)))
    (if (empty? remaining) out
        (let ((piece (first remaining)))
          (pack (rest remaining) (+ c0 (cols piece) 1)
                (shape-place out piece 0 c0)))))))'''


def program(settings):
    return CANONICAL if parse_settings(settings)["pack_order"] == "as_found" else ALTERNATE


def counterfactual_program():
    return CANONICAL
