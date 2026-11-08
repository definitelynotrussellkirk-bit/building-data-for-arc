"""Native symmetry lessons with a source-preserving default and a derived axis.

The extra bbox_major_axis setting measures occupied content before choosing a
reflection of the ORIGINAL canvas. Labels are independently executed in Racket.
Three-demo lessons identify the four declared settings. Additional plausible
rivals are fitted to demonstrations only; query screening prevents a surviving
rival from disagreeing on an emitted query. This is finite conditional teaching
coverage, not a claim of universal rule uniqueness.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

from reviewer_support import (
    canonical_path, find_root, load_selected_generator,
    public_challenge_bytes, public_challenge_id,
)
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper

TASK_ID = "4b787be81422"
ROOT = Path(find_root(__file__))
GEN, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
SYMMETRY_AXES = ("left_right", "top_bottom", "rotation_180", "bbox_major_axis")
RACKET_AXIS = {"left_right": "lr", "top_bottom": "ud", "rotation_180": "180"}
PARAMETER = {
    "name": "symmetry_axis", "values": list(SYMMETRY_AXES),
    "default": "left_right",
    "input_constraints": "3..30 binary-color grids; zero background; nonempty occupied bbox",
}
STATUS = "reviewer-ready candidate; owner exact-source acceptance required"
MAX_QUERY_ATTEMPTS = 96
CORE_PROFILES = {
    "left_right": [("lr", "tall", "intrinsic"), ("lr", "wide", "offset"), ("tb", "square", "intrinsic")],
    "top_bottom": [("tb", "wide", "intrinsic"), ("tb", "tall", "offset"), ("lr", "square", "intrinsic")],
    "rotation_180": [("rot", "tall", "intrinsic"), ("lr", "tall", "offset"), ("tb", "wide", "intrinsic")],
    "bbox_major_axis": [("lr", "tall", "intrinsic"), ("lr", "wide", "offset"), ("tb", "square", "intrinsic")],
}
QUERY_PROFILES = tuple(
    (symmetry, aspect, style)
    for symmetry in ("lr", "tb", "rot", "none", "all")
    for aspect in ("tall", "wide", "square")
    for style in (("intrinsic", "offset") if symmetry in ("lr", "tb") else ("intrinsic",))
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rng(seed: int, *context: Any) -> random.Random:
    payload = json.dumps([TASK_ID, "native-v2", seed, *context], separators=(",", ":"))
    return random.Random(int(digest(payload.encode()), 16))


@lru_cache(maxsize=1)
def canonical_record() -> dict[str, Any]:
    records = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                record = json.loads(line)
                if record.get("task_id") == TASK_ID:
                    records.append(record)
    if len(records) != 1 or not isinstance(records[0].get("program_solution"), str):
        raise ValueError("expected one canonical Racket record")
    return records[0]


def _validate_seed(seed: Any) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative literal integer")


def _validate_axis(axis: Any) -> None:
    if type(axis) is not str or axis not in SYMMETRY_AXES:
        raise ValueError(f"symmetry_axis must be one of {SYMMETRY_AXES}")


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"symmetry_axis"}:
        raise ValueError("settings must contain exactly symmetry_axis")
    _validate_axis(settings["symmetry_axis"])
    return settings["symmetry_axis"]


def _count(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")
    return value


def validate_grid(grid: Any) -> None:
    if type(grid) is not list or not 3 <= len(grid) <= 30:
        raise ValueError("input must have 3..30 rows")
    if type(grid[0]) is not list or not 3 <= len(grid[0]) <= 30:
        raise ValueError("input must have 3..30 columns")
    if any(type(row) is not list or len(row) != len(grid[0]) or any(
        type(cell) is not int or not 0 <= cell <= 9 for cell in row
    ) for row in grid):
        raise ValueError("input must be rectangular with literal ARC integer cells")
    colors = {cell for row in grid for cell in row}
    if 0 not in colors or len(colors - {0}) != 1:
        raise ValueError("input needs zero background and exactly one foreground color")
    if sum(cell != 0 for row in grid for cell in row) < 2:
        raise ValueError("input needs at least two foreground cells")


def bbox_info(grid: list[list[int]]) -> dict[str, Any]:
    validate_grid(grid)
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    height, width = r1 - r0 + 1, c1 - c0 + 1
    return {"bbox": [r0, c0, r1, c1], "height": height, "width": width,
            "chosen_axis": "left_right" if height > width else "top_bottom"}


def _symmetries(grid: list[list[int]]) -> dict[str, bool]:
    rows = [list(row) for row in grid]
    return {
        "left_right": rows == [list(reversed(row)) for row in rows],
        "top_bottom": rows == list(reversed(rows)),
        "rotation_180": rows == [list(reversed(row)) for row in reversed(rows)],
    }


def python_output(symmetry_axis: str, grid: list[list[int]]) -> list[list[int]]:
    _validate_axis(symmetry_axis)
    validate_grid(grid)
    axis = bbox_info(grid)["chosen_axis"] if symmetry_axis == "bbox_major_axis" else symmetry_axis
    return [[1 if _symmetries(grid)[axis] else 7]]


def _rule(expression: str) -> str:
    return f'(rule! (lambda (g) (grid (list (list (if {expression} 1 7))))))'


def _derived(expression: str) -> str:
    return (
        '(rule! (lambda (g) (let* ([b (crop-to-content g 0)] '
        '[axis (if (> (rows b) (cols b)) "lr" "ud")]) '
        f'(grid (list (list (if {expression} 1 7)))))))'
    )


def program_for(symmetry_axis: str = "left_right") -> str:
    _validate_axis(symmetry_axis)
    canonical = canonical_record()["program_solution"]
    if symmetry_axis == "left_right":
        return canonical
    if symmetry_axis == "bbox_major_axis":
        return _derived('(symmetric? g axis)')
    source = '(symmetric? g "lr")'
    if canonical.count(source) != 1:
        raise ValueError("canonical predicate drift; review the parameterization")
    return canonical.replace(source, f'(symmetric? g "{RACKET_AXIS[symmetry_axis]}")', 1)


def choose_axis(seed: int) -> str:
    _validate_seed(seed)
    return SYMMETRY_AXES[seed % len(SYMMETRY_AXES)]


def rival_programs(axis: str) -> dict[str, str]:
    """Exact executable finite rival set, shared by teaching and evidence."""
    _validate_axis(axis)
    selected = 'axis' if axis == "bbox_major_axis" else json.dumps(RACKET_AXIS[axis])
    programs = {name: program_for(name) for name in SYMMETRY_AXES}
    programs.update({
        "always_1": _rule('#t'),
        "always_7": _rule('#f'),
        "any_symmetry": _rule('(or (symmetric? g "lr") (symmetric? g "ud") (symmetric? g "180"))'),
        "all_symmetries": _rule('(and (symmetric? g "lr") (symmetric? g "ud"))'),
        "even_foreground_count": _rule('(even? (- (* (rows g) (cols g)) (count-color g 0)))'),
        "bbox_tall_label": _derived('(> (rows b) (cols b))'),
        "canvas_major_axis": _rule('(symmetric? g (if (> (rows g) (cols g)) "lr" "ud"))'),
        "bbox_minor_axis": _derived('(symmetric? g (if (> (rows b) (cols b)) "ud" "lr"))'),
        "square_tie_left_right": _derived('(symmetric? g (if (>= (rows b) (cols b)) "lr" "ud"))'),
        "tall_and_lr": _derived('(and (> (rows b) (cols b)) (symmetric? g "lr"))'),
        "nontall_and_tb": _derived('(and (<= (rows b) (cols b)) (symmetric? g "ud"))'),
        "crop_before_classification": _derived(f'(symmetric? b {selected})'),
        "color_echo": '(rule! (lambda (g) (grid (list (list (first (grid-colors g 0)))))))',
    })
    bbox = '(bbox-of-cells (filter (lambda (p) (not (= (at g (first p) (second p)) 0))) (grid-positions g)))'
    if axis == "rotation_180":
        aligned = '(and (= (+ (first bb) (third bb)) (- (rows g) 1)) (= (+ (second bb) (fourth bb)) (- (cols g) 1)))'
    else:
        aligned = f'(if (equal? {selected} "lr") (= (+ (second bb) (fourth bb)) (- (cols g) 1)) (= (+ (first bb) (third bb)) (- (rows g) 1)))'
    programs["bbox_alignment_only"] = _derived(f'(let ([bb {bbox}]) {aligned})')
    for name, r, c in (
        ("top_left", '0', '0'), ("top_right", '0', '(- (cols g) 1)'),
        ("bottom_left", '(- (rows g) 1)', '0'),
        ("bottom_right", '(- (rows g) 1)', '(- (cols g) 1)'),
        ("center", '(quotient (rows g) 2)', '(quotient (cols g) 2)'),
    ):
        programs[name + "_foreground"] = _rule(f'(not (= (at g {r} {c}) 0))')
    if axis in RACKET_AXIS:
        others = [RACKET_AXIS[x] for x in RACKET_AXIS if x != axis]
        programs["complement_of_other_axes"] = _rule(
            f'(not (or (symmetric? g "{others[0]}") (symmetric? g "{others[1]}")))'
        )
    return programs


def rival_outputs(axis: str, grid: list[list[int]]) -> dict[str, list[list[int]]]:
    info, sym = bbox_info(grid), _symmetries(grid)
    h, w = len(grid), len(grid[0])
    r0, c0, r1, c1 = info["bbox"]
    tall = info["height"] > info["width"]
    chosen = info["chosen_axis"] if axis == "bbox_major_axis" else axis
    crop = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    crop_sym = _symmetries(crop)
    bits = {**sym, "bbox_major_axis": sym[info["chosen_axis"]],
        "always_1": True, "always_7": False,
        "any_symmetry": any(sym.values()), "all_symmetries": all(sym.values()),
        "even_foreground_count": sum(v != 0 for row in grid for v in row) % 2 == 0,
        "bbox_tall_label": tall,
        "canvas_major_axis": sym["left_right" if h > w else "top_bottom"],
        "bbox_minor_axis": sym["top_bottom" if tall else "left_right"],
        "square_tie_left_right": sym["left_right" if info["height"] >= info["width"] else "top_bottom"],
        "tall_and_lr": tall and sym["left_right"],
        "nontall_and_tb": not tall and sym["top_bottom"],
        "crop_before_classification": crop_sym[chosen],
        "bbox_alignment_only": ((c0 + c1 == w - 1) if chosen == "left_right" else
            (r0 + r1 == h - 1) if chosen == "top_bottom" else
            (c0 + c1 == w - 1 and r0 + r1 == h - 1)),
        "top_left_foreground": bool(grid[0][0]),
        "top_right_foreground": bool(grid[0][-1]),
        "bottom_left_foreground": bool(grid[-1][0]),
        "bottom_right_foreground": bool(grid[-1][-1]),
        "center_foreground": bool(grid[h // 2][w // 2]),
    }
    if axis in RACKET_AXIS:
        bits["complement_of_other_axes"] = not any(v for a, v in sym.items() if a != axis)
    result = {name: [[1 if value else 7]] for name, value in bits.items()}
    result["color_echo"] = [[next(v for row in grid for v in row if v)]]
    return result


def teaching_report(axis: str, demos: list[dict], queries: list[dict]) -> dict[str, Any]:
    names = tuple(rival_programs(axis))
    demo_predictions = [rival_outputs(axis, pair["input"]) for pair in demos]
    query_predictions = [rival_outputs(axis, pair["input"]) for pair in queries]
    rows = {}
    for name in names:
        different = [i for i, pair in enumerate(demos) if demo_predictions[i][name] != pair["output"]]
        disagreements = [i for i, pair in enumerate(queries) if query_predictions[i][name] != pair["output"]]
        rows[name] = {"matches_all_demonstrations": not different,
                      "distinguishing_demo_indices": different,
                      "query_disagreement_indices": disagreements}
    survivors = [name for name in SYMMETRY_AXES if rows[name]["matches_all_demonstrations"]]
    viable = [name for name, row in rows.items() if row["matches_all_demonstrations"]]
    return {"passed": survivors == [axis] and all(not rows[name]["query_disagreement_indices"] for name in viable),
            "selected_axis": axis, "declared_survivors": survivors, "rivals": rows,
            "viable_rivals": viable,
            "limitations": "Only these finite rivals and these emitted queries; some extra rivals may remain demonstration-consistent."}


def _orbit(h: int, w: int, r: int, c: int, symmetry: str) -> frozenset[tuple[int, int]]:
    cells = {(r, c)}
    if symmetry in ("lr", "all"):
        cells |= {(r, w - 1 - c)}
    if symmetry in ("tb", "all"):
        cells |= {(h - 1 - r, c)}
    if symmetry in ("rot", "all"):
        cells |= {(h - 1 - r, w - 1 - c)}
    return frozenset(cells)


def _mask(rng: random.Random, h: int, w: int, symmetry: str, count: int) -> list[list[int]]:
    orbits = sorted({_orbit(h, w, r, c, symmetry) for r in range(h) for c in range(w)},
                    key=lambda cells: tuple(sorted(cells)))
    expected = {"lr": {"left_right"}, "tb": {"top_bottom"}, "rot": {"rotation_180"},
                "none": set(), "all": set(RACKET_AXIS)}[symmetry]
    for _ in range(128):
        top = (0, rng.randrange(1, w - 1))
        left = (rng.randrange(1, h - 1), 0)
        required = [top, left]
        if symmetry in ("lr", "none"):
            required.append((h - 1, rng.randrange(1, w - 1)))
        if symmetry in ("tb", "none"):
            required.append((rng.randrange(1, h - 1), w - 1))
        selected = set().union(*(_orbit(h, w, r, c, symmetry) for r, c in required))
        if len(selected) > count:
            continue
        candidates = [o for o in orbits if o.isdisjoint(selected) and len(o) > 1]
        if symmetry == "none":
            candidates = [o for o in orbits if o.isdisjoint(selected)]
        rng.shuffle(candidates)
        candidates.sort(key=len, reverse=True)
        for orbit in candidates:
            if len(orbit) <= count - len(selected):
                selected.update(orbit)
            if len(selected) == count:
                break
        if len(selected) != count:
            continue
        grid = [[int((r, c) in selected) for c in range(w)] for r in range(h)]
        if {a for a, yes in _symmetries(grid).items() if yes} == expected:
            return grid
    raise RuntimeError(f"bounded orbit construction failed: {h}x{w}, {symmetry}, count={count}")


def _scene(seed: int, key: Any, profile: tuple[str, str, str], height: int, width: int,
           *, demo: bool = False, count: int | None = None, color: int = 2) -> tuple[list[list[int]], dict]:
    rng = _rng(seed, "profile", key, profile, height, width)
    symmetry, aspect, style = profile
    dims = []
    for bh in range(3, height + 1):
        for bw in range(3, width + 1):
            if (height - bh) % 2 or (width - bw) % 2:
                continue
            if ("tall" if bh > bw else "wide" if bw > bh else "square") != aspect:
                continue
            if style == "offset" and ((symmetry == "lr" and height - bh < 2) or
                                      (symmetry == "tb" and width - bw < 2)):
                continue
            if demo and (height - bh < 2 or width - bw < 2):
                continue
            if bh * bw >= (count or 8) + 4:
                dims.append((bh, bw))
    if not dims:
        raise ValueError(f"unsupported scene profile {profile} at {height}x{width}")
    dims.sort(key=lambda d: d[0] * d[1], reverse=True)
    bh, bw = rng.choice(dims[:min(4, len(dims))])
    target_count = count if count is not None else max(8, 4 * int(rng.uniform(.24, .55) * bh * bw / 4))
    target_count = min(target_count, 4 * ((bh * bw - 4) // 4))
    local_symmetry = "all" if style == "offset" else symmetry
    mask = _mask(rng, bh, bw, local_symmetry, target_count)
    r0, c0 = (height - bh) // 2, (width - bw) // 2
    if style == "offset":
        if symmetry == "lr":
            r0 = rng.choice([v for v in range(height - bh + 1) if v != r0])
        else:
            c0 = rng.choice([v for v in range(width - bw + 1) if v != c0])
    grid = [[0] * width for _ in range(height)]
    for r, row in enumerate(mask):
        for c, value in enumerate(row):
            if value:
                grid[r0 + r][c0 + c] = color
    validate_grid(grid)
    expected = {"lr": {"left_right"}, "tb": {"top_bottom"}, "rot": {"rotation_180"},
                "none": set(), "all": set(RACKET_AXIS)}[symmetry]
    if {a for a, yes in _symmetries(grid).items() if yes} != expected:
        raise AssertionError("scene placement changed requested symmetry")
    return grid, {"profile": list(profile), "height": height, "width": width,
                  "foreground_count": target_count, **bbox_info(grid)}


def _input_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def build_input_plan(seed: int, *, symmetry_axis: str | None = None,
                     demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _validate_seed(seed)
    axis = choose_axis(seed) if symmetry_axis is None else symmetry_axis
    _validate_axis(axis)
    _count(demos, 3, 6, "demos")
    _count(queries, 1, 4, "queries")
    rng = _rng(seed, "lesson")
    canvas = rng.choice((9, 11, 13))
    count = rng.choice((8, 12))
    palette = rng.sample([2, 3, 4, 5, 6, 8, 9], 2)
    profiles = [*CORE_PROFILES[axis], ("none", "tall", "intrinsic"),
                ("all", "square", "intrinsic"), ("none", "wide", "intrinsic")][:demos]
    demo_inputs, demo_meta = [], []
    for i, profile in enumerate(profiles):
        grid, meta = _scene(seed, ("demo", i), profile, canvas, canvas,
                            demo=True, count=count, color=palette[0])
        demo_inputs.append(grid)
        demo_meta.append(meta)
    # Vary color, but keep a positive/negative pair at the same color/count/size.
    labels = [python_output(axis, grid) for grid in demo_inputs]
    same_color = {0, next(i for i in range(1, demos) if labels[i] != labels[0])}
    for i in range(demos):
        if i not in same_color:
            demo_inputs[i] = [[palette[1] if v else 0 for v in row] for row in demo_inputs[i]]
    order = list(range(demos))
    rng.shuffle(order)
    demo_inputs = [demo_inputs[i] for i in order]
    demo_meta = [demo_meta[i] for i in order]
    train = [{"input": g, "output": python_output(axis, g)} for g in demo_inputs]
    initial = teaching_report(axis, train, [])
    if initial["declared_survivors"] != [axis]:
        raise AssertionError(f"core demonstrations underidentify {axis}: {initial['declared_survivors']}")
    viable = initial["viable_rivals"]
    seen = {_input_key(g) for g in demo_inputs}
    if len(seen) != demos:
        raise AssertionError("duplicate demonstrations")
    query_inputs, query_meta = [], []
    desired = [1, 1, 7, 7]
    sizes = [(7, 9), (13, 17), (23, 27), (30, 30)]
    query_rng = _rng(seed, "query-order")
    query_rng.shuffle(desired)
    query_rng.shuffle(sizes)
    rejected = {"wrong_label": 0, "viable_rival": 0, "duplicate": 0, "construction": 0}
    for index in range(queries):
        height, width = sizes[index]
        candidates = list(QUERY_PROFILES)
        _rng(seed, "query-profile-order", index).shuffle(candidates)
        for attempt in range(MAX_QUERY_ATTEMPTS):
            profile = candidates[attempt % len(candidates)]
            color = _rng(seed, "query-color", index, attempt).choice([2, 3, 4, 5, 6, 8, 9])
            try:
                grid, meta = _scene(seed, ("query", index, attempt), profile, height, width, color=color)
            except (ValueError, RuntimeError):
                rejected["construction"] += 1
                continue
            expected = python_output(axis, grid)
            if expected != [[desired[index]]]:
                rejected["wrong_label"] += 1
                continue
            predictions = rival_outputs(axis, grid)
            if any(predictions[name] != expected for name in viable):
                rejected["viable_rival"] += 1
                continue
            if _input_key(grid) in seen:
                rejected["duplicate"] += 1
                continue
            seen.add(_input_key(grid))
            query_inputs.append(grid)
            query_meta.append({**meta, "attempts": attempt + 1})
            break
        else:
            raise RuntimeError(f"query {index} exhausted {MAX_QUERY_ATTEMPTS} attempts for {axis}; {rejected}")
    return {"seed": seed, "symmetry_axis": axis, "demo_inputs": demo_inputs,
            "query_inputs": query_inputs,
            "profile_metadata": {"demonstrations": demo_meta, "queries": query_meta,
                                 "rejections": rejected, "viable_demo_rivals": viable},
            "input_sampling": "profile RNG excludes private setting; curriculum and rival-screened selection are setting-dependent"}


def generate_native(seed: int, settings: dict, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    axis = validate_settings(settings)
    plan = build_input_plan(seed, symmetry_axis=axis, demos=demos, queries=queries)
    train = [{"input": g, "output": python_output(axis, g)} for g in plan["demo_inputs"]]
    test = [{"input": g, "output": python_output(axis, g)} for g in plan["query_inputs"]]
    report = teaching_report(axis, train, test)
    if not report["passed"]:
        raise AssertionError("emitted query disagrees with a demonstration-consistent tested rival")
    return {"train": train, "test": test, "program_solution": program_for(axis)}


def _verified_runtime(bridge) -> dict:
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise ValueError("labels require the live protected Racket backend")
    return identity


def _execute_in_verified_session(bridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    validate_grid(grid)
    callable_rule = strip_rule_wrapper(strip_line_comments(program))
    literal = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
    value = bridge.eval_text(f'({callable_rule} {literal})')
    if type(value) is not list or type(value[0]) is not list or any(type(v) is not int for row in value for v in row):
        raise TypeError("Racket returned a non-integer grid")
    return value


def execute(bridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    _verified_runtime(bridge)
    return _execute_in_verified_session(bridge, program, grid)


def generate_episode(seed: int, bridge, *, symmetry_axis: str | None = None,
                     demos: int = 3, queries: int = 4) -> tuple[dict, dict]:
    plan = build_input_plan(seed, symmetry_axis=symmetry_axis, demos=demos, queries=queries)
    axis = plan["symmetry_axis"]
    grids = [*plan["demo_inputs"], *plan["query_inputs"]]
    programs = rival_programs(axis)
    # Runtime identity hashes the executable and prelude. Verify it once for
    # this session, as the native worker does, rather than rehashing per label.
    identity = _verified_runtime(bridge)
    executed = {name: [_execute_in_verified_session(bridge, program, grid) for grid in grids]
                for name, program in programs.items()}
    parity = all(executed[name][i] == rival_outputs(axis, grid)[name]
                 for name in programs for i, grid in enumerate(grids))
    if not parity:
        raise AssertionError("Racket and Python rival/label implementations differ")
    outputs = executed[axis]
    labeled = {"train": [{"input": g, "output": outputs[i]} for i, g in enumerate(plan["demo_inputs"])],
               "test": [{"input": g, "output": outputs[demos + i]} for i, g in enumerate(plan["query_inputs"])]}
    public = json.loads(public_challenge_bytes(labeled))
    teaching = teaching_report(axis, labeled["train"], labeled["test"])
    single = generate_native(seed, {"symmetry_axis": axis}, demos=demos, queries=1)
    first_turn = {"train": public["train"], "test": [public["test"][0]]}
    single_turn = json.loads(public_challenge_bytes(single))
    checks = {"all_labels_from_live_racket": True, "python_mirror_parity": parity,
              "canonical_default_parity": all(executed["left_right"][i] == python_output("left_right", g)
                                              for i, g in enumerate(grids)),
              "sequential_first_turn_equal": public_challenge_bytes(first_turn) == public_challenge_bytes(single_turn),
              "teaching_passed": teaching["passed"],
              "distinct_inputs": len({_input_key(g) for g in grids}) == len(grids)}
    if not all(checks.values()):
        raise AssertionError(f"episode failed checks: {checks}")
    private = {"schema": "4b787be81422-native-symmetry-evidence-v2", "status": STATUS,
               "seed": seed, "parameter": {"symmetry_axis": axis}, "program": programs[axis],
               "program_sha256": digest(programs[axis].encode()), "query_answers": outputs[demos:],
               "profile_metadata": plan["profile_metadata"], "input_sampling": plan["input_sampling"],
               "rival_programs": programs, "racket_outputs": executed, "teaching": teaching, "checks": checks,
               "public_id": public_challenge_id(public), "generator_sha256": GENERATOR_SHA256,
               "runtime_identity": identity}
    return public, private


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_evidence(out_dir: str | Path, *, seeds: Iterable[int] = (0, 17),
                   demos: int = 3, queries: int = 4) -> dict[str, Any]:
    from arc_repl.racket_bridge import RacketBridge
    seed_values = list(seeds)
    if not seed_values or len(set(seed_values)) != len(seed_values):
        raise ValueError("provide distinct evidence seeds")
    for seed in seed_values:
        _validate_seed(seed)
    _count(demos, 3, 6, "demos")
    _count(queries, 1, 4, "queries")
    out = Path(out_dir)
    if out.exists():
        raise FileExistsError(f"evidence output already exists: {out}")
    out.mkdir(parents=True)
    episodes = []
    with RacketBridge(timeout=30, max_calls_before_restart=2048) as bridge:
        identity = bridge.runtime_identity
        canonical_checks = []
        for i, pair in enumerate([*canonical_record()["train"], *canonical_record()["test"]]):
            actual = execute(bridge, program_for(), pair["input"])
            canonical_checks.append({"pair_index": i, "actual": actual, "expected": pair["output"],
                                     "passed": actual == pair["output"]})
        if not all(row["passed"] for row in canonical_checks):
            raise AssertionError("canonical default lost official-pair parity")
        for seed in seed_values:
            for axis in SYMMETRY_AXES:
                public, private = generate_episode(seed, bridge, symmetry_axis=axis, demos=demos, queries=queries)
                identifier = public_challenge_id(public)
                public_path = out / "public" / f"{identifier}.json"
                public_path.parent.mkdir(parents=True, exist_ok=True)
                if public_path.exists():
                    raise ValueError("duplicate public challenge")
                public_path.write_bytes(public_challenge_bytes(public))
                private_path = out / "private" / f"{identifier}.json"
                _write_json(private_path, private)
                episodes.append({"seed": seed, "symmetry_axis": axis,
                                 "public": str(public_path.relative_to(out)),
                                 "public_sha256": digest(public_path.read_bytes()),
                                 "private": str(private_path.relative_to(out)),
                                 "private_sha256": digest(private_path.read_bytes()),
                                 "checks": private["checks"]})
    _write_json(out / "private" / "canonical-default-parity.json", canonical_checks)
    manifest = {"schema": "4b787be81422-native-symmetry-checks-v2", "task_id": TASK_ID,
                "status": STATUS, "parameter": PARAMETER, "demos": demos, "queries": queries,
                "episodes": episodes, "canonical_pair_count": len(canonical_checks),
                "generator_sha256": GENERATOR_SHA256,
                "prototype_sha256": digest(Path(__file__).read_bytes()), "runtime_identity": identity,
                "passed": all(all(row["checks"].values()) for row in episodes),
                "limitations": ["Finite declared and extra rivals only; viable extras are retained with their safe-query restriction.",
                    "Canonical generator.py is unchanged and still has its inherited corner shortcut.",
                    "bbox_major_axis adds contextual gating, not iterative state simulation.",
                    "Native qualification and owner exact-source acceptance are separate from these authoring checks."]}
    _write_json(out / "checks.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 17])
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args(argv)
    result = write_evidence(args.out, seeds=args.seeds, demos=args.demos, queries=args.queries)
    print(json.dumps({"passed": result["passed"], "episodes": len(result["episodes"]),
                      "canonical_pairs": result["canonical_pair_count"], "out": args.out}, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
