"""Native diagonal-ray family, with one boundary-derived continuation.

The two retained prototype rules are reused exactly. The additional rule first
paints main-axis rays, freezes their boundary endpoints, and only then paints
anti-axis rays from those endpoints. Painted cells never become new sources.
All ten inputs are constructed before independent count slicing.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import random

from puzzle_generators.rule_wrap import strip_rule_wrapper

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "_rays_prototype_" + hashlib.sha256(str(HERE).encode()).hexdigest()[:16],
    HERE / "prototype.py",
)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

RULES = ("both", "main_only", "one_bounce")
DEFAULT = {"ray_rule": "both"}
MAIN = ((-1, -1), (1, 1))
ANTI = ((-1, 1), (1, -1))

# All coordinates are interior, separated by >=3 in Chebyshev distance and
# pairwise non-diagonal. The fixed teaching cores survive the four symmetries
# that preserve the main axis. Later profiles add varied counts and aspect.
_PROFILES = (
    (9, 11, ((2,6),(6,3))),
    # The center is interior to both a three-marker row and column. Different
    # arm lengths avoid diagonal alignment and refute collinear-extrema rules.
    (13, 15, ((6,2),(6,7),(6,12),(2,7),(10,7))),
    (7, 9, ((3,3),)),
    (17, 15, ((3,1),(3,7),(3,13),(13,4),(13,10))),
    (25, 22, ((4,1),(4,10),(4,19),(18,4),(18,13),(18,19))),
    (30, 30, ((5,1),(5,7),(5,13),(5,19),(5,25),
              (24,4),(24,10),(24,16),(24,22),(24,28))),
    (7, 7, ((2,2),)),
    (13, 17, ((2,6),(8,3),(5,14))),
    (24, 29, ((4,2),(4,11),(4,20),(18,5),(18,14),(18,26))),
    (30, 30, ((5,1),(5,7),(5,13),(5,19),(24,4),(24,10),(24,22),(24,28))),
)

ENDPOINT_EXPRESSION = """(reduce
          (lambda (acc pos)
            (append acc
              (map (lambda (dir)
                     (reduce
                       (lambda (last d)
                         (let ((nr (+ (fst pos) (* (fst dir) d)))
                               (nc (+ (snd pos) (* (snd dir) d))))
                           (if (in-bounds? nr nc h w) (list nr nc) last)))
                       pos (range 1 (max h w))))
                   '((-1 -1) (1 1)))))
          '() sources)"""


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _rule(settings):
    if type(settings) is not dict or set(settings) != {"ray_rule"}:
        raise ValueError("settings must contain exactly ray_rule")
    rule = settings["ray_rule"]
    if type(rule) is not str or rule not in RULES:
        raise ValueError(f"ray_rule must be one of {RULES}")
    return rule


def validate_grid(grid):
    """Validate the shared native grammar, separate from production's 7..17."""
    if (type(grid) is not list or not 7 <= len(grid) <= 30
            or type(grid[0]) is not list or not 7 <= len(grid[0]) <= 30):
        raise ValueError("native grids must have dimensions 7..30")
    h, w = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != w
           or any(type(v) is not int or not 0 <= v <= 9 for v in row)
           for row in grid):
        raise ValueError("expected rectangular exact-integer color grids")
    sources = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v]
    if not 1 <= len(sources) <= 10 or len({grid[r][c] for r,c in sources}) != 1:
        raise ValueError("expected one to ten markers sharing one nonzero color")
    for i,(r,c) in enumerate(sources):
        if not (0 < r < h-1 and 0 < c < w-1):
            raise ValueError("markers must be interior")
        for rr,cc in sources[:i]:
            if max(abs(r-rr),abs(c-cc)) < 3 or abs(r-rr) == abs(c-cc):
                raise ValueError("markers must be separated and not share diagonals")
    return sources


def main_endpoints(grid):
    sources = validate_grid(grid)
    h, w = len(grid), len(grid[0])
    result = []
    for r,c in sources:
        nw = min(r,c)
        se = min(h-1-r,w-1-c)
        result.extend(((r-nw,c-nw),(r+se,c+se)))
    return result


def program(settings):
    rule = _rule(settings)
    if rule in ("both", "main_only"):
        return _prototype.program_for(rule)
    main = strip_rule_wrapper(_prototype.program_for("main_only"))
    return f"""(rule! (lambda (g)
      (let* ((h (rows g)) (w (cols g))
             (sources (filter (lambda (p) (not (zero? (at g (fst p) (snd p)))))
                              (grid-positions g)))
             (ends {ENDPOINT_EXPRESSION})
             (stage-a ({main} g))
             (color (at g (fst (first sources)) (snd (first sources)))))
        (reduce
          (lambda (acc pos)
            (reduce
              (lambda (g2 dir)
                (reduce
                  (lambda (g3 d)
                    (let ((nr (+ (fst pos) (* (fst dir) d)))
                          (nc (+ (snd pos) (* (snd dir) d))))
                      (if (and (in-bounds? nr nc h w) (zero? (at g3 nr nc)))
                          (set-cell g3 nr nc color) g3)))
                  g2 (range 1 (max h w))))
              acc '((-1 1) (1 -1))))
          stage-a ends))))"""


def apply_python(grid, rule):
    validate_grid(grid)
    _rule({"ray_rule":rule})
    if rule != "one_bounce":
        return _prototype.apply_python(grid, rule)
    result = _prototype.apply_python(grid, "main_only")
    h, w = len(grid), len(grid[0])
    color = next(v for row in grid for v in row if v)
    for r,c in main_endpoints(grid):
        for dr,dc in ANTI:
            rr,cc = r+dr,c+dc
            while 0 <= rr < h and 0 <= cc < w:
                if result[rr][cc] == 0:
                    result[rr][cc] = color
                rr,cc = rr+dr,cc+dc
    return result


def _input(seed, index):
    digest = hashlib.sha256(f"9ce2dcf587b8/native-input/v1/{seed}/{index}".encode()).digest()
    rng = random.Random(int.from_bytes(digest,"big"))
    h,w,template = _PROFILES[index]
    points = list(template)
    if rng.getrandbits(1):
        points = [(h-1-r,w-1-c) for r,c in points]
    if rng.getrandbits(1):
        h,w = w,h
        points = [(c,r) for r,c in points]
    # Keep the two geometric teaching cores and the corner-inactive query exact.
    if index not in (0,1,6):
        dr = rng.randint(1-min(r for r,c in points), h-2-max(r for r,c in points))
        dc = rng.randint(1-min(c for r,c in points), w-2-max(c for r,c in points))
        points = [(r+dr,c+dc) for r,c in points]
    color = rng.choice((1,4,7)) if index == 0 else rng.choice((2,5,8)) if index == 1 else rng.randint(1,9)
    result = [[0]*w for _ in range(h)]
    for r,c in points:
        result[r][c] = color
    validate_grid(result)
    return result


def generate(seed, settings=None, demos=3, queries=4):
    _integer(seed,"seed",0,2**63-1)
    _integer(demos,"demos",2,6)
    _integer(queries,"queries",1,4)
    if settings is None:
        index = hashlib.sha256(f"9ce2dcf587b8/native-setting/v1/{seed}".encode()).digest()[0] % len(RULES)
        settings = {"ray_rule":RULES[index]}
    rule = _rule(settings)
    bank = [_input(seed,i) for i in range(10)]
    def labeled(inputs):
        return [{"input":g,"output":apply_python(g,rule)} for g in inputs]
    return {"train":labeled(bank[:demos]),"test":labeled(bank[6:6+queries]),
            "program_solution":program(settings)}
