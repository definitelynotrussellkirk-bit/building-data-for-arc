"""Native, episode-fixed overlay policies with input-dependent selectors.

The retained lower/upper programs remain exact. The two count selectors also
admit equal panels of height 5..14 and a one/two-row separator. Their global
count comparison supplies the overlap winner; ties always select the lower.
Generation emits deterministic claims; protected Racket verification is external.
"""
from __future__ import annotations

from copy import deepcopy
from functools import cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random

TASK_ID = "0ae119475d57"
VERSION = "native-overlap-selectors-v1"
SETTINGS = ("lower_wins", "upper_wins", "denser_wins", "sparser_wins")
MIN_DEMOS, MAX_DEMOS, MAX_QUERIES = 4, 6, 4
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"overlap_precedence"}:
        raise ValueError("settings must contain only overlap_precedence")
    name = settings["overlap_precedence"]
    if type(name) is not str or name not in SETTINGS:
        raise ValueError("unknown overlap_precedence")
    return name


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")
    return value


def _grid(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must contain nonempty list rows")
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        raise ValueError("grid exceeds 30x30")
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("grid cells must be literal integer ARC colors")
    return grid


def _parts(grid, settings=None):
    _grid(grid)
    height, width = len(grid), len(grid[0])
    if not 11 <= height <= 30 or not 4 <= width <= 30:
        raise ValueError("input shape must be 11..30 by 4..30")
    panel_height = (height - 1) // 2
    separator_height = height - 2 * panel_height
    if settings is not None and _setting(settings) in SETTINGS[:2] and height != 11:
        raise ValueError("fixed lower/upper policies require 5+1+5 rows")
    top, bottom = grid[:panel_height], grid[-panel_height:]
    separator = grid[panel_height:height-panel_height]
    separators = {v for row in separator for v in row}
    if len(separators) != 1 or 0 in separators:
        raise ValueError("separator band must be uniform and nonzero")
    top_colors = {v for row in top for v in row if v}
    bottom_colors = {v for row in bottom for v in row if v}
    if len(top_colors) != 1 or len(bottom_colors) != 1:
        raise ValueError("each panel must use exactly one nonzero color")
    top_color, bottom_color, separator_color = next(iter(top_colors)), next(iter(bottom_colors)), next(iter(separators))
    if len({top_color, bottom_color, separator_color}) != 3:
        raise ValueError("panel and separator colors must be distinct")
    if any(all(row) for row in top + bottom):
        raise ValueError("panel rows must retain a zero, preserving a unique separator band")
    return top, bottom, panel_height, width, separator_height, separator_color


def make_input(top, bottom, separator_color=5, separator_height=1):
    """Build and validate a separate-family scene from two monochrome panels."""
    _grid(top)
    _grid(bottom)
    _integer(separator_color, 1, 9, "separator_color")
    _integer(separator_height, 1, 2, "separator_height")
    if (len(top), len(top[0])) != (len(bottom), len(bottom[0])):
        raise ValueError("panels must have equal dimensions")
    result = deepcopy(top) + [[separator_color] * len(top[0]) for _ in range(separator_height)] + deepcopy(bottom)
    _parts(result)
    return result


def describe(grid, settings):
    name = _setting(settings)
    top, bottom, ph, width, gap, sep = _parts(grid, settings)
    top_count = sum(bool(v) for row in top for v in row)
    bottom_count = sum(bool(v) for row in bottom for v in row)
    upper = (name == "upper_wins" or
             name == "denser_wins" and top_count > bottom_count or
             name == "sparser_wins" and top_count < bottom_count)
    counts = dict(blank=0, top_only=0, bottom_only=0, overlap=0)
    for arow, brow in zip(top, bottom):
        for a, b in zip(arow, brow):
            counts["overlap" if a and b else "top_only" if a else "bottom_only" if b else "blank"] += 1
    return {"input_shape": [len(grid), width], "output_shape": [ph, width],
            "panel_shape": [ph, width], "separator_height": gap,
            "top_count": top_count, "bottom_count": bottom_count,
            "branch_counts": counts, "selected_winner": "upper" if upper else "lower",
            "overlap_precedence": name, "separator_color": sep}


def apply_claim(grid, settings):
    info = describe(grid, settings)
    top, bottom, *_ = _parts(grid, settings)
    upper = info["selected_winner"] == "upper"
    return [[(a if a else b) if upper else (b if b else a)
             for a, b in zip(arow, brow)] for arow, brow in zip(top, bottom)]


@cache
def _legacy():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_retained_overlay_0ae119475d57", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _racket_rule(upper="(> tn bn)", cell=None, fixed=False, score_top=None, score_bottom=None):
    """Complete private rule text; shared by selectors and finite audit rivals."""
    ph = "5" if fixed else "(quotient (- (rows g) 1) 2)"
    off = "6" if fixed else "(- (rows g) ph)"
    score_top = score_top or "(for*/sum ((r (range 0 ph)) (c (range 0 w))) (if (= (at g r c) 0) 0 1))"
    score_bottom = score_bottom or "(for*/sum ((r (range 0 ph)) (c (range 0 w))) (if (= (at g (+ off r) c) 0) 0 1))"
    cell = cell or "(if choose-top (if (!= top 0) top bot) (if (!= bot 0) bot top))"
    return f"""(rule! (lambda (g)
 (let* ((ph {ph}) (w (cols g)) (off {off})
        (tn {score_top}) (bn {score_bottom})
        (choose-top {upper}))
  (build-grid ph w (r c)
   (let ((top (at g r c)) (bot (at g (+ off r) c)))
    {cell})))))"""


@cache
def _programs():
    old = _legacy()
    return {"lower_wins": old.materialize_rule("lower_wins", root=ROOT),
            "upper_wins": old.materialize_rule("upper_wins", root=ROOT),
            "denser_wins": _racket_rule("(> tn bn)"),
            "sparser_wins": _racket_rule("(< tn bn)")}


def program(settings):
    return _programs()[_setting(settings)]


def _rng(seed, split, slot, attempt=0):
    digest = hashlib.sha256(f"{VERSION}:{seed}:{split}:{slot}:{attempt}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _palette(rng):
    a, b, sep = rng.sample(range(1, 10), 3)
    return a, b, sep


def _masks(ph, width, overlap, top_only, bottom_only, rng, stress=False):
    # One blank pair in every row makes the separator unique constructively.
    anchors = {(0, 0), (0, width-1), (ph-1, 0), (ph-1, width-1)} if stress else set()
    blanks = {(r, rng.choice([c for c in range(width) if (r, c) not in anchors])) for r in range(ph)}
    free = [(r, c) for r in range(ph) for c in range(width) if (r, c) not in blanks | anchors]
    rng.shuffle(free)
    if overlap < len(anchors) or overlap + top_only + bottom_only > len(free) + len(anchors):
        raise ValueError("mask counts exceed constructive row-blank capacity")
    both = set(anchors) | set(free[:overlap-len(anchors)])
    cursor = overlap-len(anchors)
    upper = both | set(free[cursor:cursor+top_only])
    cursor += top_only
    lower = both | set(free[cursor:cursor+bottom_only])
    return upper, lower


def _paint(ph, width, masks, palette, gap=1):
    top_color, bottom_color, sep = palette
    upper, lower = masks
    top = [[top_color if (r, c) in upper else 0 for c in range(width)] for r in range(ph)]
    bottom = [[bottom_color if (r, c) in lower else 0 for c in range(width)] for r in range(ph)]
    return make_input(top, bottom, sep, gap)


def _compact_vs_spread(width, rng):
    # Compact panel: ten cells in two rows. Spread panel: four overlaps and
    # three exclusive cells, reaching all rows and more columns/bbox area.
    start_r, start_c = rng.randrange(4), rng.randrange(1, width-5)
    compact = {(r, c) for r in (start_r, start_r+1) for c in range(start_c, start_c+5)}
    columns = rng.sample(range(start_c, start_c+5), 4)
    spread = {(start_r + i//2, c) for i, c in enumerate(columns)}
    remaining_rows = [r for r in range(5) if r not in (start_r, start_r+1)]
    rng.shuffle(remaining_rows)
    missing_col = next(iter(set(range(start_c, start_c+5))-set(columns)))
    spread.update(zip(remaining_rows, (0, width-1, missing_col)))
    return compact, spread


def _small_tie_masks(width, rng):
    # Opposite local imbalances at two overlaps, despite a global 5/5 tie.
    # Both row-local selector shortcuts therefore fail on this one input.
    ra, rb, rc = rng.sample(range(5), 3)
    a0, a1, a2 = rng.sample(range(width), 3)
    b0, b1, b2 = rng.sample(range(width), 3)
    c0, c1 = rng.sample(range(width), 2)
    upper = {(ra, a0), (ra, a1), (ra, a2), (rb, b0), (rc, c0)}
    lower = {(ra, a0), (rb, b0), (rb, b1), (rb, b2), (rc, c1)}
    return upper, lower


def _demo(seed, slot, rng):
    a, b, sep = _palette(_rng(seed, "teaching-palette", 0))
    lo, hi = sorted((a, b))
    if slot in (0, 1):
        width = rng.randint(9, 14)
        compact, spread = _compact_vs_spread(width, rng)
        masks = (compact, spread) if slot == 0 else (spread, compact)
        return _paint(5, width, masks, (lo, hi, sep))
    if slot == 2:
        width = rng.randint(8, 12)
        return _paint(5, width, _small_tie_masks(width, rng), (hi, lo, sep))
    if slot == 3:
        width = rng.randint(12, 16)
        return _paint(5, width, _masks(5, width, 10, 10, 10, rng), (lo, hi, sep))
    width = rng.randint(4, 20)
    mode = ("upper", "lower", "tie")[rng.randrange(3)]
    return _random_scene(5, width, mode, rng)


def _random_scene(ph, width, mode, rng, gap=1, stress=False):
    n = ph * width
    if stress:
        overlap, small, large = n*28//100, n*16//100, n*34//100
        equal = n*22//100
    else:
        overlap, small, large = max(1, n//6), max(1, n//10), max(2, n//3)
        equal = max(1, n//5)
    top_only, bottom_only = ((large, small) if mode == "upper" else
                             (small, large) if mode == "lower" else (equal, equal))
    return _paint(ph, width, _masks(ph, width, overlap, top_only, bottom_only, rng, stress), _palette(rng), gap)


def _query(seed, slot, dynamic, rng):
    if slot == 0:
        return _random_scene(5, 4, "upper" if seed % 2 == 0 else "lower", rng)
    if slot == 1:
        return _random_scene(5, rng.randint(9, 16), "lower" if seed % 2 == 0 else "upper", rng)
    if slot == 2:
        return _random_scene(9 if dynamic else 5, 22, "tie", rng, stress=True)
    return _random_scene(14 if dynamic else 5, 30,
                         "lower" if seed % 2 == 0 else "upper", rng,
                         gap=2 if dynamic else 1, stress=True)


def generate(seed, settings, demos, queries):
    _integer(seed, 0, 2**63-1, "seed")
    name = _setting(settings)
    _integer(demos, MIN_DEMOS, MAX_DEMOS, "demos")
    _integer(queries, 1, MAX_QUERIES, "queries")
    seen, batches = set(), {}
    for split, count in (("train", MAX_DEMOS), ("test", MAX_QUERIES)):
        rows = []
        for slot in range(count):
            for attempt in range(64):
                rng = _rng(seed, split, slot, attempt)
                grid = _demo(seed, slot, rng) if split == "train" else _query(seed, slot, name in SETTINGS[2:], rng)
                key = json.dumps(grid, separators=(",", ":"))
                if key not in seen:
                    seen.add(key)
                    rows.append({"input": grid, "output": apply_claim(grid, settings)})
                    break
            else:
                raise RuntimeError(f"no distinct {split} input for slot {slot} in 64 attempts")
        batches[split] = rows
    return {"train": batches["train"][:demos], "test": batches["test"][:queries],
            "program_solution": program(settings)}


def public_turn(episode, index):
    """Only visible demos and one current query; returned grids never alias."""
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must have train/test lists")
    _integer(index, 0, len(episode["test"])-1, "index")
    train = []
    for pair in episode["train"]:
        if type(pair) is not dict or not {"input", "output"} <= pair.keys():
            raise ValueError("demonstration needs input and output")
        train.append({"input": deepcopy(_grid(pair["input"])), "output": deepcopy(_grid(pair["output"]))})
    query = episode["test"][index]
    if type(query) is not dict or "input" not in query:
        raise ValueError("query needs input")
    return {"train": train, "test": [{"input": deepcopy(_grid(query["input"]))}]}


def rivals(settings):
    """Finite semantic alternatives; equivalent exclusive-count rules omitted."""
    name = _setting(settings)
    fixed = name in SETTINGS[:2]
    selected = {"lower_wins": "#f", "upper_wins": "#t", "denser_wins": "(> tn bn)", "sparser_wins": "(< tn bn)"}[name]
    def rule(upper=selected, cell=None, **kwargs):
        return _racket_rule(upper, cell, fixed=fixed, **kwargs)
    found = {
        "copy_upper": rule(cell="top"), "copy_lower": rule(cell="bot"),
        "numeric_maximum": rule(cell="(max top bot)"),
        "nonzero_minimum": rule(cell="(if (= top 0) bot (if (= bot 0) top (min top bot)))"),
        "erase_overlap": rule(cell="(if (and (!= top 0) (!= bot 0)) 0 (if (!= top 0) top bot))"),
        "blank_is_separator": rule(cell="(if (and (= top 0) (= bot 0)) (at g ph 0) (if choose-top (if (!= top 0) top bot) (if (!= bot 0) bot top)))"),
        "upper_if_top_above_7": rule(upper="(> tn 7)"),
        "upper_if_bottom_above_7": rule(upper="(> bn 7)"),
        "upper_if_top_at_most_7": rule(upper="(<= tn 7)"),
        "upper_if_bottom_at_most_7": rule(upper="(<= bn 7)"),
        "reverse_columns_lower": rule(cell="(let ((shifted (at g (+ off r) (- w 1 c)))) (if choose-top (if (!= top 0) top shifted) (if (!= shifted 0) shifted top)))"),
        "reverse_rows_lower": rule(cell="(let ((shifted (at g (+ off (- ph 1 r)) c))) (if choose-top (if (!= top 0) top shifted) (if (!= shifted 0) shifted top)))"),
    }
    if not fixed:
        comparator = ">" if name == "denser_wins" else "<"
        found["tie_upper"] = rule(upper=f"({comparator}= tn bn)")
        found["count_after_lower_overlay"] = rule(
            score_top="(for*/sum ((r (range 0 ph)) (c (range 0 w))) (if (and (!= (at g r c) 0) (= (at g (+ off r) c) 0)) 1 0))")
        found["count_after_upper_overlay"] = rule(
            score_bottom="(for*/sum ((r (range 0 ph)) (c (range 0 w))) (if (and (!= (at g (+ off r) c) 0) (= (at g r c) 0)) 1 0))")
        for feature in ("color_sum", "occupied_rows", "occupied_columns", "bbox_area"):
            def score(offset):
                at = f"(at g (+ {offset} r) c)"
                if feature == "color_sum":
                    return f"(for*/sum ((r (range 0 ph)) (c (range 0 w))) {at})"
                if feature == "occupied_rows":
                    return f"(count-if (lambda (r) (for/or ((c (range 0 w))) (!= {at} 0))) (range 0 ph))"
                if feature == "occupied_columns":
                    return f"(count-if (lambda (c) (for/or ((r (range 0 ph))) (!= {at} 0))) (range 0 w))"
                return f"(let* ((rs (filter (lambda (r) (for/or ((c (range 0 w))) (!= {at} 0))) (range 0 ph))) (cs (filter (lambda (c) (for/or ((r (range 0 ph))) (!= {at} 0))) (range 0 w)))) (* (+ 1 (- (apply max rs) (apply min rs))) (+ 1 (- (apply max cs) (apply min cs)))))"
            found[feature] = rule(score_top=score("0"), score_bottom=score("off"))
        # Same overlap cell can have a different answer because distant rows
        # change the selected winner; row-local scoring loses that dependency.
        row_compare = f"({comparator} (count-if (lambda (cc) (!= (at g r cc) 0)) (range 0 w)) (count-if (lambda (cc) (!= (at g (+ off r) cc) 0)) (range 0 w)))"
        found["row_local_counts"] = rule(cell=f"(if {row_compare} (if (!= top 0) top bot) (if (!= bot 0) bot top))")
    return found
