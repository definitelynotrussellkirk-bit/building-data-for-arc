"""Selector-directed template matching with fixed or quarter-turn orientations.

The production generator and canonical authority remain unchanged. Generated
Python labels are authoring claims until independently replayed with Racket.
"""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import (load_selected_generator, public_challenge_bytes,
                              public_challenge_id)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "0083f06314c3"
BASE, BASE_PATH, BASE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
SETTINGS = ({"orientation": "fixed"}, {"orientation": "rotations"})
DEFAULT = {"orientation": "fixed"}
CANONICAL_PROGRAM = HERE.joinpath("canonical.rkt").read_text()
_LIMIT = 2**63 - 1
_CALL = "(find-matches board template 0)"
_SELECT = "(if (= color 2) t1 t2)"
_B_CODES = (1, 3, 4, 5, 6, 7, 8)


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"orientation"}
            or type(settings["orientation"]) is not str
            or settings["orientation"] not in ("fixed", "rotations")):
        raise ValueError("settings must be exactly {'orientation': 'fixed'|'rotations'}")
    return settings["orientation"]


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row)
           for row in grid):
        raise ValueError("grid must be rectangular with literal integer colors 0..9")
    return grid


def _parts(grid):
    _grid(grid)
    ranges, errors = BASE._panel_ranges(grid)
    if errors or len(ranges) != 4:
        raise ValueError("expected four nonempty panels and three single-column 9 dividers")
    dividers = [c for c in range(len(grid[0])) if all(row[c] == 9 for row in grid)]
    if len(dividers) != 3 or any(v == 9 and c not in dividers
                               for row in grid for c, v in enumerate(row)):
        raise ValueError("9 is reserved for three full-height divider columns")
    if ranges[2][0] != ranges[2][1]:
        raise ValueError("selector panel must be one column wide")
    selectors = [row[ranges[2][0]] for row in grid if row[ranges[2][0]]]
    if len(selectors) != 1:
        raise ValueError("selector panel must contain exactly one colored cell")
    templates = [BASE._crop_panel(grid, *bounds) for bounds in ranges[:2]]
    if any(not t or not any(v for row in t for v in row) for t in templates):
        raise ValueError("both template panels must be nonempty")
    board = BASE._board_from_panel(grid, ranges[3])
    return templates, selectors[0], board


def dependency_intermediate(grid):
    templates, selector, _ = _parts(grid)
    selected = 0 if selector == 2 else 1
    return {"selector_color": selector, "selected_panel": selected,
            "template": deepcopy(templates[selected]),
            "other_template": deepcopy(templates[1-selected])}


def _rotate(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _variants(template, orientation):
    variants = [deepcopy(template)]
    if orientation != "fixed":
        for _ in range(3):
            variants.append(_rotate(variants[-1]))
    if orientation == "dihedral":
        variants.append([row[::-1] for row in template])
        for _ in range(3):
            variants.append(_rotate(variants[-1]))
    unique = []
    for variant in variants:
        if variant not in unique:
            unique.append(variant)
    return unique


def _matches(board, template, orientation, *, literal_zero=False, color_blind=False):
    matches = []
    for variant in _variants(template, orientation):
        for r0, c0 in BASE._match_positions(board, variant,
                solid_bbox=literal_zero, ignore_color=color_blind):
            cells = frozenset((r0+r, c0+c) for r, row in enumerate(variant)
                              for c, v in enumerate(row) if v)
            box = frozenset((r0+r, c0+c) for r in range(len(variant))
                            for c in range(len(variant[0])))
            matches.append((cells, box))
    return matches


def _render(board, matches, mode="union"):
    chosen = set()
    for cells, box in matches:
        if mode == "disjoint" and cells & chosen:
            continue
        if mode == "xor":
            chosen.symmetric_difference_update(cells)
        else:
            chosen.update(box if mode == "bbox" else cells)
        if mode == "first":
            break
    return [[8 if (r, c) in chosen else 0 for c in range(len(board[0]))]
            for r in range(len(board))]


def rule_mirror(grid, settings):
    orientation = _settings(settings)
    templates, selector, board = _parts(grid)
    template = templates[0 if selector == 2 else 1]
    return _render(board, _matches(board, template, orientation))


def _component_cap(grid, limit):
    """Wrong rule: retain only the first few positive 4-connected groups."""
    h, w = len(grid), len(grid[0])
    seen, kept, groups = set(), set(), 0
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            groups += 1
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                if groups <= limit:
                    kept.add((rr, cc))
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
    return [[8 if (r, c) in kept else 0 for c in range(w)] for r in range(h)]


def _replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError("canonical source no longer has the expected unique expression")
    return source.replace(old, new)


def program(settings):
    orientation = _settings(settings)
    return (CANONICAL_PROGRAM if orientation == "fixed" else
            _replace_once(CANONICAL_PROGRAM, _CALL, "(find-matches board template 1)"))


def rival_outputs(grid, settings):
    orientation = _settings(settings)
    templates, selector, board = _parts(grid)
    template = templates[0 if selector == 2 else 1]
    matches = _matches(board, template, orientation)
    other = "rotations" if orientation == "fixed" else "fixed"
    colors = [next(v for row in t for v in row if v) for t in templates]
    counts = [sum(v == color for row in board for v in row) for color in colors]
    frequency_choice = templates[0 if counts[0] >= counts[1] else 1]
    return {
        "other_setting": _render(board, _matches(board, template, other)),
        "always_a": _render(board, _matches(board, templates[0], orientation)),
        "always_b": _render(board, _matches(board, templates[1], orientation)),
        "literal_zero": _render(board, _matches(board, template, orientation, literal_zero=True)),
        "color_blind": _render(board, _matches(board, template, orientation, color_blind=True)),
        "dihedral": _render(board, _matches(board, template, "dihedral")),
        "first_match": _render(board, matches, "first"),
        "disjoint_matches": _render(board, matches, "disjoint"),
        "xor_matches": _render(board, matches, "xor"),
        "mark_all_nonzero": [[8 if v else 0 for v in row] for row in board],
        "fill_bounding_boxes": _render(board, matches, "bbox"),
        "few_groups": _component_cap(_render(board, matches), 2 if orientation == "fixed" else 3),
        "most_frequent_template": _render(board, _matches(board, frequency_choice, orientation)),
    }


def rival_programs(settings):
    """Parameter-aware Racket counterparts of the finite authoring rivals."""
    orientation = _settings(settings)
    code = program(settings)
    mode = 0 if orientation == "fixed" else 1
    call = f"(find-matches board template {mode})"
    same = "(= (at board (+ r (first p)) (+ c (second p))) tv)"
    match = "(or (= tv 0) " + same + ")"
    result = {
        "other_setting": program({"orientation": "rotations" if mode == 0 else "fixed"}),
        "always_a": _replace_once(code, _SELECT, "t1"),
        "always_b": _replace_once(code, _SELECT, "t2"),
        "literal_zero": _replace_once(code, match, same),
        "color_blind": _replace_once(code, same,
            "(not (= (at board (+ r (first p)) (+ c (second p))) 0))"),
        "dihedral": _replace_once(code, call, "(find-matches board template 2)"),
        "first_match": _replace_once(code, call,
            f"(let ((ms {call})) (if (empty? ms) ms (list (first ms))))"),
    }
    old = "(define (board-union-matches board matches (color 8)) (render-board (rows board) (cols board) (flatmap match-nonzero-cells matches) color))"
    disjoint = """(define (board-union-matches board matches (color 8))
      (let loop ((remaining (remove-duplicates matches)) (used (list)))
        (if (empty? remaining) (render-board (rows board) (cols board) used color)
          (let ((cells (match-nonzero-cells (first remaining))))
            (loop (rest remaining)
              (if (ormap (lambda (p) (member p used)) cells) used (append cells used)))))))"""
    xor = """(define (board-union-matches board matches (color 8))
      (let* ((cells (flatmap match-nonzero-cells (remove-duplicates matches)))
             (chosen (filter (lambda (p) (odd? (count (lambda (q) (equal? p q)) cells)))
                             (remove-duplicates cells))))
        (render-board (rows board) (cols board) chosen color)))"""
    bbox = """(define (board-union-matches board matches (color 8))
      (render-board (rows board) (cols board)
        (flatmap (lambda (m)
          (for*/list ((r (in-range (rows (third m)))) (c (in-range (cols (third m)))))
            (list (+ (first m) r) (+ (second m) c)))) matches) color))"""
    result["disjoint_matches"] = _replace_once(code, old, disjoint)
    result["xor_matches"] = _replace_once(code, old, xor)
    result["fill_bounding_boxes"] = _replace_once(code, old, bbox)
    final = f"(board-union-matches board {call} 8)"
    result["mark_all_nonzero"] = _replace_once(code, final,
        "(render-board (rows board) (cols board) (filter (lambda (p) (not (= (at board (first p) (second p)) 0))) (grid-positions board)) 8)")
    anchor = "(apply min (map (lambda (p) (+ (* 30 (first p)) (second p))) (obj-cells a)))"
    anchor_b = anchor.replace("(obj-cells a)", "(obj-cells b)")
    cap = 2 if mode == 0 else 3
    capped = f"""(let* ((marked {final})
        (parts (sort (objects marked 0) (lambda (a b) (< {anchor} {anchor_b}))))
        (chosen (take parts (min {cap} (length parts)))))
      (paint-cells (empty-grid (rows marked) (cols marked) 0) (flatmap obj-cells chosen) 8))"""
    result["few_groups"] = _replace_once(code, final, capped)
    frequency = """(let* ((a (first (filter (lambda (v) (not (= v 0))) (apply append t1))))
                           (b (first (filter (lambda (v) (not (= v 0))) (apply append t2))))
                           (cells (apply append board)))
       (if (>= (count (lambda (v) (= v a)) cells) (count (lambda (v) (= v b)) cells)) t1 t2))"""
    result["most_frequent_template"] = _replace_once(code, _SELECT, frequency)
    return result


def teaching_check(episode):
    """Fit the named rivals to visible demonstrations; never inspect queries."""
    settings = episode["settings"]
    _settings(settings)
    train = episode["train"]
    if type(train) is not list or not train:
        raise ValueError("nonempty demonstrations required")
    refuted, names = {}, []
    for index, pair in enumerate(train):
        _grid(pair["output"])
        if rule_mirror(pair["input"], settings) != pair["output"]:
            raise ValueError("demonstration label disagrees with selected rule")
        rivals = rival_outputs(pair["input"], settings)
        names = list(rivals)
        for name, value in rivals.items():
            if value != pair["output"]:
                refuted.setdefault(name, index)
    survivors = [name for name in names if name not in refuted]
    return {"status": "ambiguous" if survivors else "identified",
            "surviving_rivals": survivors, "refuted_by": refuted,
            "limits": "Named finite rivals only; no universal uniqueness claim."}


def _rng(seed, split, index):
    material = f"{TASK_ID}:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


@lru_cache(maxsize=32)
def _overlaps(cells):
    template = BASE._template_grid(cells, 1)
    valid = []
    for union, offsets, reserved in BASE._overlap_layouts(cells):
        h, w = BASE._dims(union)
        if h > 5 or w > 5:
            continue
        board = BASE._template_grid(union, 1)
        if all(_render(board, _matches(board, template, orientation), mode)
               != _render(board, _matches(board, template, orientation))
               for orientation in ("fixed", "rotations") for mode in ("disjoint", "xor")):
            valid.append((union, offsets, reserved))
    if not valid:
        raise ValueError("chiral template has no eligible overlap construction")
    return tuple(valid)


def _group(cells, color, filler, *, reserved=None):
    h, w = BASE._dims(cells)
    occupied = set(cells)
    boxes = set(reserved) if reserved is not None else {
        (r, c) for r in range(h) for c in range(w)}
    # Wildcard cells are visibly occupied, so a literal-zero rule is refuted.
    return [(r, c, color) for r, c in sorted(occupied)] + [
        (r, c, filler) for r, c in sorted(boxes - occupied)]


def _input(seed, split, index):
    rng = _rng(seed, split, index)
    if split == "demo":
        h, w = (30, 20) if index == 1 else (13 + index, 18 + index % 3)
    elif index == 0:
        h, w = 12, 18
    elif index == 1:
        h, w = rng.randrange(19, 28), 19
    elif index == 2:
        h, w = 16, 20
    else:
        h, w = 30, 20
    selected = index % 2 if split == "demo" else (index + seed) % 2
    b_code = _B_CODES[seed % len(_B_CODES)]
    selector = 2 if selected == 0 else b_code
    palette = [c for c in range(1, 9) if c not in (2, b_code)]
    color_a, color_b, decoy, filler = rng.sample(palette, 4)
    # L and P have different areas and both have reflection-only orientations.
    shapes = [BASE._SHAPES_BY_SIZE[4][0], BASE._SHAPES_BY_SIZE[5][3]]
    rng.shuffle(shapes)
    shapes = [rng.choice(BASE._d4_variants(shape)) for shape in shapes]
    selected_cells, unselected_cells = shapes[selected], shapes[1-selected]
    colors = [color_a, color_b]
    color = colors[selected]
    template = BASE._template_grid(selected_cells, color)
    rotations = _variants(template, "rotations")
    reflected = [v for v in _variants(template, "dihedral") if v not in rotations]
    if not reflected:
        raise RuntimeError("selected shape lost chirality")
    to_cells = lambda t: tuple((r, c) for r, row in enumerate(t) for c, v in enumerate(row) if v)
    union, _, reserved = rng.choice(_overlaps(tuple(selected_cells)))
    groups = [
        _group(union, color, filler, reserved=reserved),
        _group(to_cells(rng.choice(rotations[1:])), color, filler),
        _group(to_cells(rng.choice(reflected)), color, filler),
        _group(selected_cells, decoy, filler),
        _group(unselected_cells, colors[1-selected], filler),
        _group(selected_cells, color, filler),
    ]
    if split == "demo" and index == 0:
        # Selector choice cannot be inferred from which template color is most
        # prevalent. Twenty-five unselected cells exceed the selected maximum
        # of 24 here; the second demo reverses that frequency relationship.
        groups[4] = [(r, c, colors[1-selected]) for r in range(5) for c in range(5)]
    bands = max(2, h // 6)
    for _ in range(3 * bands - len(groups)):
        # Teach variable/unbounded-by-small-demo occurrence counts within the
        # mandatory two-demo prefix. All queries have at most this many groups.
        kind = 0 if split == "demo" and index == 1 else rng.randrange(4)
        cells = (selected_cells if kind == 0 else to_cells(rng.choice(rotations))
                 if kind == 1 else unselected_cells if kind == 2
                 else to_cells(rng.choice(reflected)))
        group_color = colors[1-selected] if kind == 2 else color
        groups.append(_group(cells, group_color, filler))
    rng.shuffle(groups)
    board = [[0] * w for _ in range(h)]
    for k, group in enumerate(groups):
        band, column = divmod(k, 3)
        r0, r1 = band * h // bands, (band + 1) * h // bands
        c0, c1 = column * w // 3, (column + 1) * w // 3
        # One blank strip between cells prevents accidental cross-group matches.
        if band < bands - 1:
            r1 -= 1
        if column < 2:
            c1 -= 1
        gh, gw = max(p[0] for p in group)+1, max(p[1] for p in group)+1
        if gh > r1-r0 or gw > c1-c0:
            raise RuntimeError("constructive group exceeds its reserved slot")
        rr = r0 if band == 0 else r1-gh if band == bands-1 else rng.randint(r0, r1-gh)
        cc = c0 if column == 0 else c1-gw if column == 2 else rng.randint(c0, c1-gw)
        for r, c, value in group:
            board[rr+r][cc+c] = value
    panels = [[[0] * 3 for _ in range(h)] for _ in range(2)]
    for i in range(2):
        BASE._place_panel_motif(panels[i], shapes[i], colors[i], rng)
    selector_panel = [[0] for _ in range(h)]
    selector_panel[rng.randrange(h)][0] = selector
    grid = BASE._assemble(panels + [selector_panel, board])
    _parts(grid)
    return grid


def generate(seed, settings, demos=3, queries=4):
    _integer("seed", seed, 0, _LIMIT)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    _settings(settings)
    def pairs(split, count):
        grids = [_input(seed, split, i) for i in range(count)]
        return [{"input": grid, "output": rule_mirror(grid, settings)} for grid in grids]
    episode = {"task_id": TASK_ID, "seed": seed, "settings": deepcopy(settings),
               "train": pairs("demo", demos), "test": pairs("query", queries),
               "program_solution": program(settings)}
    inputs = [json.dumps(pair["input"]) for pair in episode["train"] + episode["test"]]
    if len(set(inputs)) != len(inputs):
        raise RuntimeError("duplicate input in constructed episode")
    if teaching_check(episode)["surviving_rivals"]:
        raise RuntimeError("constructed demonstrations do not eliminate declared rivals")
    return episode


def public_challenge(episode, query_index=0):
    _integer("query_index", query_index, 0, len(episode["test"])-1)
    selected = {"train": episode["train"], "test": [episode["test"][query_index]]}
    return json.loads(public_challenge_bytes(selected))


def export_batch(episodes, output_dir):
    """Export first turns and separate private banks after full batch validation."""
    if type(episodes) not in (list, tuple) or not episodes:
        raise ValueError("a nonempty episode batch is required")
    pending, ids = [], set()
    for episode in episodes:
        visible = public_challenge(episode)
        identity = public_challenge_id(visible)
        if identity in ids:
            raise ValueError("duplicate visible public challenge")
        ids.add(identity)
        pending.append((identity, public_challenge_bytes(visible), deepcopy(episode)))
    serialized = []
    for identity, visible_bytes, episode in pending:
        _settings(episode["settings"])
        _integer("demos", len(episode["train"]), 2, 6)
        _integer("queries", len(episode["test"]), 1, 4)
        if episode.get("program_solution", episode.get("program")) != program(episode["settings"]):
            raise ValueError("private program differs from selected rule")
        seen = set()
        for pair in episode["train"] + episode["test"]:
            _grid(pair["input"])
            _grid(pair["output"])
            fingerprint = json.dumps(pair["input"])
            if fingerprint in seen:
                raise ValueError("duplicate demonstration/query input")
            seen.add(fingerprint)
            if rule_mirror(pair["input"], episode["settings"]) != pair["output"]:
                raise ValueError("private label disagrees with selected rule")
        if teaching_check(episode)["surviving_rivals"]:
            raise ValueError("underidentified demonstrations")
        private_bytes = (json.dumps(episode, sort_keys=True, separators=(",", ":"),
                                   allow_nan=False) + "\n").encode("utf-8")
        serialized.append((identity, visible_bytes, private_bytes))
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=False)
    (output / "public").mkdir()
    (output / "private").mkdir()
    for identity, visible_bytes, private_bytes in sorted(serialized):
        (output / "public" / (identity + ".json")).write_bytes(visible_bytes)
        (output / "private" / (identity + ".json")).write_bytes(private_bytes)
    return {"episodes": len(pending), "public_dir": str(output / "public"),
            "private_dir": str(output / "private"), "training_admitted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--orientation", choices=("fixed", "rotations", "both"), default="both")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    settings = SETTINGS if args.orientation == "both" else ({"orientation": args.orientation},)
    print(json.dumps(export_batch([generate(args.seed, s, args.demos, args.queries)
                                  for s in settings], args.out), sort_keys=True))


if __name__ == "__main__":
    main()
