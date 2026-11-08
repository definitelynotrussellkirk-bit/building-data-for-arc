"""Matched-input parametric episodes for ARC family 3143493b7c83.

The hidden episode setting changes only the matching predicate after the marker
bitmap has been extracted:

* ``contains`` (canonical): a lattice cell matches when every key offset is 1.
* ``exact_bbox``: every position inside the key bounding box must equal the key.

Python outputs are deterministic claims. Native qualification independently
executes the exact Racket programs over every demonstration and query.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import public_challenge_bytes

TASK_ID = "3143493b7c83"
HERE = Path(__file__).resolve().parent
CANONICAL = HERE.joinpath("canonical.rkt").read_text(encoding="utf-8")
MATCH_MODES = ("contains", "exact_bbox")
PLAUSIBLE_RIVALS = (
    "exact_full_cell",
    "key_count_only",
    "contains_or_horizontal_mirror",
    "first_row_only",
    "identity",
)

_CONTAINS_BLOCK = """           (define (contains-template? rs cs)
             (all? (lambda (p)
                     (let* ((r (+ rs (first p)))
                            (c (+ cs (second p))))
                       (and (< r h) (< c w) (= (at g r c) 1))))
                   template))"""

_EXACT_BLOCK = """           (define (template-on? tr tc)
             (for/or ((p template))
                     (and (= tr (first p)) (= tc (second p)))))
           (define (contains-template? rs cs)
             (all? (lambda (p)
                     (let* ((tr (first p))
                            (tc (second p))
                            (r (+ rs tr))
                            (c (+ cs tc)))
                       (and (< r h)
                            (< c w)
                            (= (at g r c)
                               (if (template-on? tr tc) 1 0)))))
                   (flatmap (lambda (tr)
                              (map (lambda (tc) (list tr tc))
                                   (range 0 tw)))
                            (range 0 th))))"""

_TEMPLATE_BLOCK = """           (define template
             (filter (lambda (p) (block-on? (first p) (second p)))
                     (flatmap (lambda (tr)
                                (map (lambda (tc) (list tr tc)) (range 0 tw)))
                              (range 0 th))))"""

_WRONG_TEMPLATE_BLOCK = """           (define extracted-template
             (filter (lambda (p) (block-on? (first p) (second p)))
                     (flatmap (lambda (tr)
                                (map (lambda (tc) (list tr tc)) (range 0 tw)))
                              (range 0 th))))
           (define template
             (map (lambda (p)
                    (list (first p) (- (- tw 1) (second p))))
                  extracted-template))"""

_SKIP_TEMPLATE_BLOCK = """           (define template '())"""

# Profiles are separate for demonstrations and queries so changing one count
# never shifts the other stream. The fourth query deliberately reaches 30x30.
_DEMO_PROFILES = (
    (15, 19, 0),
    (19, 15, 1),
    (19, 23, 2),
    (23, 19, 0),
    (23, 27, 1),
    (27, 23, 2),
)
_QUERY_PROFILES = (
    (19, 27, 1),
    (23, 23, 0),
    (27, 27, 2),
    (30, 30, 0),
)

# Every shape spans its bounding box and is asymmetric under horizontal mirror.
_KEYS = (
    (2, 3, ((0, 0), (0, 2), (1, 0), (1, 1))),
    (3, 2, ((0, 0), (1, 1), (2, 0), (2, 1))),
    (3, 3, ((0, 0), (0, 2), (1, 0), (2, 1), (2, 2))),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings):
    if type(settings) is not dict or set(settings) != {"match_mode"}:
        raise ValueError("settings must contain exactly match_mode")
    value = settings["match_mode"]
    if type(value) is not str or value not in MATCH_MODES:
        raise ValueError("match_mode must be contains or exact_bbox")
    return value


def _replace_once(text, before, after, label):
    if text.count(before) != 1:
        raise ValueError(f"pinned canonical source no longer has exactly one {label}")
    return text.replace(before, after, 1)


def program(settings):
    """Return canonical bytes unchanged for the default and one guarded variant."""
    mode = _mode(settings)
    if mode == "contains":
        return CANONICAL
    return _replace_once(CANONICAL, _CONTAINS_BLOCK, _EXACT_BLOCK,
                         "contains-template predicate")


def wrong_intermediate_program():
    """Diagnostic program: A extracts the key, then corrupts it before B."""
    return _replace_once(CANONICAL, _TEMPLATE_BLOCK, _WRONG_TEMPLATE_BLOCK,
                         "template extraction block")


def skip_a_program():
    """Diagnostic program: skip extraction A, so B receives the empty template."""
    return _replace_once(CANONICAL, _TEMPLATE_BLOCK, _SKIP_TEMPLATE_BLOCK,
                         "template extraction block")


def _rng(seed, label):
    digest = hashlib.sha256(f"{TASK_ID}:contains-exact-v1:{seed}:{label}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _parse_template(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid height must be 1..30")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("grid cells must be exact integer colors 0..9")
    colors = sorted({v for row in grid for v in row if v not in (0, 1, 4)})
    if len(colors) != 1:
        raise ValueError("expected exactly one marker color outside {0,1,4}")
    marker = colors[0]
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == marker]
    r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
    if (r1 - r0 + 1) % 2 or (c1 - c0 + 1) % 2:
        raise ValueError("marker bounding box is not a clean 2x upscale")
    th = (r1 - r0 + 1) // 2
    tw = (c1 - c0 + 1) // 2
    template = []
    for tr in range(th):
        for tc in range(tw):
            if any(grid[r0 + 2 * tr + dr][c0 + 2 * tc + dc] == marker
                   for dr in range(2) for dc in range(2)):
                template.append((tr, tc))
    if not template:
        raise ValueError("empty marker template")
    return marker, th, tw, tuple(template)


def _cell_value(grid, rs, cs, dr, dc):
    r, c = rs + dr, cs + dc
    return grid[r][c] if 0 <= r < len(grid) and 0 <= c < len(grid[0]) else None


def _matches(grid, rs, cs, th, tw, template, rule):
    key = set(template)
    if rule == "contains":
        return all(_cell_value(grid, rs, cs, dr, dc) == 1 for dr, dc in template)
    if rule == "exact_bbox":
        return all(_cell_value(grid, rs, cs, dr, dc) == (1 if (dr, dc) in key else 0)
                   for dr in range(th) for dc in range(tw))
    if rule == "exact_full_cell":
        return all(_cell_value(grid, rs, cs, dr, dc) == (1 if (dr, dc) in key else 0)
                   for dr in range(3) for dc in range(3))
    if rule == "key_count_only":
        values = [_cell_value(grid, rs, cs, dr, dc)
                  for dr in range(th) for dc in range(tw)]
        return None not in values and sum(v == 1 for v in values) == len(template)
    if rule == "contains_or_horizontal_mirror":
        mirror = {(dr, tw - 1 - dc) for dr, dc in template}
        return (all(_cell_value(grid, rs, cs, dr, dc) == 1 for dr, dc in key)
                or all(_cell_value(grid, rs, cs, dr, dc) == 1 for dr, dc in mirror))
    if rule == "first_row_only":
        first = {(dr, dc) for dr, dc in template if dr == min(r for r, _ in template)}
        return all(_cell_value(grid, rs, cs, dr, dc) == 1 for dr, dc in first)
    if rule == "identity":
        return False
    raise ValueError("unknown rule")


def _transform_with_template(grid, mode, template_override=None):
    marker, th, tw, extracted = _parse_template(grid)
    template = extracted if template_override is None else tuple(template_override)
    out = deepcopy(grid)
    if mode == "identity":
        return out
    for rs in range(0, len(grid), 4):
        for cs in range(0, len(grid[0]), 4):
            if _matches(grid, rs, cs, th, tw, template, mode):
                for dr, dc in template:
                    r, c = rs + dr, cs + dc
                    if 0 <= r < len(out) and 0 <= c < len(out[0]):
                        out[r][c] = marker
    return out


def transform(grid, settings, *, rival=None):
    mode = _mode(settings)
    return _transform_with_template(grid, mode if rival is None else rival)


def _box_touches(rs, cs, r0, c0):
    return not (rs + 2 < r0 - 1 or rs > r0 + 6 or
                cs + 2 < c0 - 1 or cs > c0 + 6)


def _stamp_box(grid, r0, c0, marker, template):
    for r in range(r0 - 1, r0 + 7):
        grid[r][c0 - 1] = 4
        grid[r][c0 + 6] = 4
    for c in range(c0 - 1, c0 + 7):
        grid[r0 - 1][c] = 4
        grid[r0 + 6][c] = 4
    for r in range(r0, r0 + 6):
        for c in range(c0, c0 + 6):
            grid[r][c] = 0
    for tr, tc in template:
        for dr in range(2):
            for dc in range(2):
                grid[r0 + 2 * tr + dr][c0 + 2 * tc + dc] = marker


def _pattern_exact(th, tw, key, rng):
    pattern = [[0] * 3 for _ in range(3)]
    for r, c in key:
        pattern[r][c] = 1
    outside = [(r, c) for r in range(3) for c in range(3)
               if not (r < th and c < tw)]
    if outside:
        r, c = rng.choice(outside)
        pattern[r][c] = 1  # exact-bbox but not exact-full-cell
    return pattern


def _pattern_super(th, tw, key, rng):
    pattern = _pattern_exact(th, tw, key, rng)
    extras = [(r, c) for r in range(th) for c in range(tw) if (r, c) not in key]
    r, c = rng.choice(extras)
    pattern[r][c] = 1
    return pattern


def _pattern_count_decoy(th, tw, key, rng):
    positions = [(r, c) for r in range(th) for c in range(tw)]
    for _ in range(100):
        chosen = set(rng.sample(positions, len(key)))
        if chosen != set(key) and not set(key) <= chosen:
            pattern = [[0] * 3 for _ in range(3)]
            for r, c in chosen:
                pattern[r][c] = 1
            return pattern
    raise RuntimeError("could not construct count decoy")


def _pattern_mirror(th, tw, key):
    mirrored = {(r, tw - 1 - c) for r, c in key}
    if mirrored == set(key):
        raise RuntimeError("key unexpectedly mirror-symmetric")
    pattern = [[0] * 3 for _ in range(3)]
    for r, c in mirrored:
        pattern[r][c] = 1
    return pattern


def _pattern_first_row_decoy(th, tw, key):
    top = min(r for r, _ in key)
    pattern = [[0] * 3 for _ in range(3)]
    for r, c in key:
        if r == top:
            pattern[r][c] = 1
    return pattern


def _write_pattern(grid, start, pattern):
    rs, cs = start
    for dr in range(3):
        for dc in range(3):
            grid[rs + dr][cs + dc] = pattern[dr][dc]


def _spread_order(candidates, rng):
    shuffled = list(candidates)
    rng.shuffle(shuffled)
    if not shuffled:
        return []
    chosen = [shuffled.pop(0)]
    while shuffled:
        nxt = max(shuffled, key=lambda p: (min(abs(p[0] - q[0]) + abs(p[1] - q[1])
                                                 for q in chosen), rng.random()))
        shuffled.remove(nxt)
        chosen.append(nxt)
    return chosen


def _sample_input(seed, label, profile):
    height, width, key_index = profile
    rng = _rng(seed, label)
    th, tw, key_tuple = _KEYS[key_index]
    key = set(key_tuple)
    marker = rng.choice((2, 3, 5, 6, 7, 8, 9))
    grid = [[0] * width for _ in range(height)]
    for r in range(3, height, 4):
        grid[r] = [4] * width
    for c in range(3, width, 4):
        for r in range(height):
            grid[r][c] = 4

    corners = ((1, 1), (1, width - 7), (height - 7, 1), (height - 7, width - 7))
    r0, c0 = corners[rng.randrange(len(corners))]
    starts = [(r, c) for r in range(0, height, 4) for c in range(0, width, 4)
              if r + 2 < height and c + 2 < width and not _box_touches(r, c, r0, c0)]
    ordered = _spread_order(starts, rng)
    stress = (height, width) == (30, 30)
    n_exact = 3 if stress else 2
    n_super = 3 if stress else 2
    required = n_exact + n_super + 3
    if len(ordered) < required:
        raise RuntimeError("profile has too few cells outside marker box")

    # Start with varied distractor noise, always clearing one key cell so no
    # accidental canonical match survives outside the explicitly planted cells.
    for start in starts:
        pattern = [[1 if rng.random() < 0.32 else 0 for _ in range(3)] for _ in range(3)]
        if all(pattern[r][c] == 1 for r, c in key):
            r, c = next(iter(key))
            pattern[r][c] = 0
        _write_pattern(grid, start, pattern)

    cursor = 0
    for _ in range(n_exact):
        _write_pattern(grid, ordered[cursor], _pattern_exact(th, tw, key, rng)); cursor += 1
    for _ in range(n_super):
        _write_pattern(grid, ordered[cursor], _pattern_super(th, tw, key, rng)); cursor += 1
    _write_pattern(grid, ordered[cursor], _pattern_count_decoy(th, tw, key, rng)); cursor += 1
    _write_pattern(grid, ordered[cursor], _pattern_mirror(th, tw, key)); cursor += 1
    _write_pattern(grid, ordered[cursor], _pattern_first_row_decoy(th, tw, key)); cursor += 1

    _stamp_box(grid, r0, c0, marker, key)
    # Contract checks local to the generator. Both settings must differ and all
    # finite rivals must disagree with each selected setting on this input.
    contains = _transform_with_template(grid, "contains")
    exact = _transform_with_template(grid, "exact_bbox")
    if contains == exact:
        raise RuntimeError("constructed input failed to distinguish settings")
    return grid


def teaching_certificate(episode):
    """Fit only visible demonstrations; queries are deliberately ignored."""
    train = episode.get("train") if isinstance(episode, dict) else None
    if not isinstance(train, list) or not train:
        raise ValueError("nonempty train demonstrations required")
    setting_survivors = []
    for mode in MATCH_MODES:
        settings = {"match_mode": mode}
        if all(transform(pair["input"], settings) == pair["output"] for pair in train):
            setting_survivors.append(mode)
    rival_survivors = []
    for rival in PLAUSIBLE_RIVALS:
        # Rival outputs are defined from the canonical extraction but not from
        # the chosen hidden setting.
        if all(_transform_with_template(pair["input"], rival) == pair["output"]
               for pair in train):
            rival_survivors.append(rival)
    return {
        "setting_survivors": setting_survivors,
        "plausible_rival_survivors": rival_survivors,
        "demonstrations_checked": len(train),
    }


def visible_turn(episode, query_index):
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return public_challenge_bytes({"train": episode["train"],
                                   "test": [episode["test"][query_index]]})


def generate(seed, settings, demos, queries):
    _integer(seed, 0, 2**63 - 1, "seed")
    mode = _mode(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train = []
    for index in range(demos):
        grid = _sample_input(seed, f"demo:{index}", _DEMO_PROFILES[index])
        train.append({"input": grid, "output": transform(grid, {"match_mode": mode})})
    test = []
    for index in range(queries):
        grid = _sample_input(seed, f"query:{index}", _QUERY_PROFILES[index])
        test.append({"input": grid, "output": transform(grid, {"match_mode": mode})})
    episode = {"train": train, "test": test,
               "program_solution": program({"match_mode": mode})}
    certificate = teaching_certificate(episode)
    if certificate["setting_survivors"] != [mode] or certificate["plausible_rival_survivors"]:
        raise RuntimeError("demonstrations failed finite teaching certificate: " + json.dumps(certificate))
    inputs = [json.dumps(pair["input"], separators=(",", ":"))
              for split in (train, test) for pair in split]
    if len(inputs) != len(set(inputs)):
        raise RuntimeError("episode inputs must be distinct")
    return episode


def dependency_witness():
    grid = _sample_input(3143493, "dependency-witness", (23, 23, 0))
    _, _, tw, template = _parse_template(grid)
    wrong = tuple((r, tw - 1 - c) for r, c in template)
    correct = _transform_with_template(grid, "contains", template)
    wrong_output = _transform_with_template(grid, "contains", wrong)
    skipped = _transform_with_template(grid, "contains", ())
    if correct == wrong_output or correct == skipped:
        raise RuntimeError("dependency witness did not change final output")
    return {
        "schema": "3143493b7c83-sequential-dependency-witness-v1",
        "setting": {"match_mode": "contains"},
        "step_a": "extract the 2x-upscaled marker bitmap",
        "intermediate": "ordered key offsets inside the marker bounding box",
        "step_b": "scan 4-aligned lattice cells using those offsets, then recolor the matched offsets",
        "why_b_depends_on_a": "B cannot choose either its match predicate or painted coordinates before A reveals the input-specific key offsets.",
        "input": grid,
        "correct_intermediate": [list(p) for p in template],
        "wrong_intermediate": [list(p) for p in wrong],
        "correct_output": correct,
        "wrong_intermediate_output": wrong_output,
        "skip_a_output": skipped,
        "correct_program": CANONICAL,
        "wrong_intermediate_program": wrong_intermediate_program(),
        "skip_a_program": skip_a_program(),
    }
