"""Authoring implementation for the d833a288bd7d source-cue family."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable


TASK_ID = "d833a288bd7d"
SOURCE_CUES = ("yellow_marker", "minority_centroid")
DEFAULT_SOURCE_CUE = "yellow_marker"
CANONICAL_PROGRAM_SHA256 = (
    "4f1476e0a09bb89804dc679485b5b6c8e14562ea16130d6a4f2b9091cd9dea5d"
)

_HERE = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (_HERE / "canonical.rkt").read_text(encoding="utf-8")
if hashlib.sha256(CANONICAL_PROGRAM.encode()).hexdigest() != CANONICAL_PROGRAM_SHA256:
    raise RuntimeError("canonical program bytes drifted")

_CANONICAL_SOURCE_BINDINGS = """                  (source-diag 0)
                  (dummy1 (for ((y yellows))
                            (for ((c corners))
                              (when
                                (and (= (first y) (first c)) (= (second y) (second c)))
                                (set! source-diag (third c))))))"""
_MINORITY_SOURCE_BINDINGS = """                  (count1 (for/sum ((p shape-cells))
                            (if (= (at g (first p) (second p)) 1) 1 0)))
                  (count8 (for/sum ((p shape-cells))
                            (if (= (at g (first p) (second p)) 8) 1 0)))
                  (minority-color (if (< count1 count8) 1 8))
                  (minority-cells (filter (lambda (p)
                                            (= (at g (first p) (second p)) minority-color))
                                          shape-cells))
                  (mmr (quotient (for/sum ((p minority-cells)) (first p))
                                 (length minority-cells)))
                  (mmc (quotient (for/sum ((p minority-cells)) (second p))
                                 (length minority-cells)))
                  (shape-center-r (quotient (+ sr1 sr2) 2))
                  (shape-center-c (quotient (+ sc1 sc2) 2))
                  (source-diag (cond
                                 ((and (<= mmr shape-center-r) (<= mmc shape-center-c)) 0)
                                 ((and (<= mmr shape-center-r) (> mmc shape-center-c)) 1)
                                 ((and (> mmr shape-center-r) (> mmc shape-center-c)) 2)
                                 (else 3)))"""
if CANONICAL_PROGRAM.count(_CANONICAL_SOURCE_BINDINGS) != 1:
    raise RuntimeError("canonical source binding fragment is not unique")
MINORITY_CENTROID_PROGRAM = CANONICAL_PROGRAM.replace(
    _CANONICAL_SOURCE_BINDINGS, _MINORITY_SOURCE_BINDINGS
)


def _validate_source_cue(value: Any) -> str:
    if type(value) is not str or value not in SOURCE_CUES:
        raise ValueError(f"source_cue must be one of {SOURCE_CUES}, got {value!r}")
    return value


def program_for(source_cue: str) -> str:
    source_cue = _validate_source_cue(source_cue)
    return (
        CANONICAL_PROGRAM
        if source_cue == "yellow_marker"
        else MINORITY_CENTROID_PROGRAM
    )

DEMO_PROFILES = (
    # h, w, dim, top, left, yellow source, target, minority centroid
    (13, 13, 4, 4, 4, 0, 1, 3),
    (14, 14, 5, 5, 4, 3, 2, 1),
    (16, 15, 6, 5, 5, 1, 3, 0),
    (18, 18, 7, 6, 6, 2, 0, 3),
    (20, 19, 8, 6, 5, 0, 2, 1),
    (22, 22, 10, 6, 6, 3, 1, 2),
)
QUERY_PROFILES = (
    (17, 19, 6, 5, 6, 2, 3, 0),
    (21, 20, 8, 6, 6, 1, 2, 3),
    (24, 26, 11, 7, 7, 0, 3, 2),
    (30, 30, 16, 7, 7, 3, 1, 0),
)


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    return seed


def _validate_count(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _digest_int(seed: int, split: str, index: int, salt: str) -> int:
    payload = f"{TASK_ID}|{seed}|{split}|{index}|{salt}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _expanded_corners(top: int, left: int, dim: int) -> tuple[tuple[int, int], ...]:
    bottom = top + dim - 1
    right = left + dim - 1
    return (
        (top - 1, left - 1),
        (top - 1, right + 1),
        (bottom + 1, right + 1),
        (bottom + 1, left - 1),
    )


def _diag(cell: tuple[int, int], center_r: int, center_c: int) -> int:
    row, col = cell
    if row <= center_r and col <= center_c:
        return 0
    if row <= center_r and col > center_c:
        return 1
    if row > center_r and col > center_c:
        return 2
    return 3


def _quadrant_positions(dim: int, diag: int) -> list[tuple[int, int]]:
    center = (dim - 1) // 2
    rows = range(0, center + 1) if diag in (0, 1) else range(center + 1, dim)
    cols = range(0, center + 1) if diag in (0, 3) else range(center + 1, dim)
    return [(row, col) for row in rows for col in cols]


def _minority_shape(
    seed: int, split: str, index: int, dim: int, minority_diag: int
) -> list[list[int]]:
    minority_color = 1 if _digest_int(seed, split, index, "minority-color") % 2 == 0 else 8
    majority_color = 8 if minority_color == 1 else 1
    candidates = _quadrant_positions(dim, minority_diag)
    anchor = {
        0: (0, 0),
        1: (0, dim - 1),
        2: (dim - 1, dim - 1),
        3: (dim - 1, 0),
    }[minority_diag]
    ranked = sorted(
        (cell for cell in candidates if cell != anchor),
        key=lambda cell: _digest_int(
            seed, split, index, f"minority-cell|{cell[0]}|{cell[1]}"
        ),
    )
    extra_span = max(1, min(len(candidates) - 1, dim // 2))
    count = min(
        len(candidates),
        max(3, dim // 2 + _digest_int(seed, split, index, "minority-count") % extra_span),
    )
    selected = {anchor, *ranked[: max(0, count - 1)]}
    if len(selected) * 2 >= dim * dim:
        raise AssertionError("minority construction is not a strict minority")
    return [
        [minority_color if (row, col) in selected else majority_color for col in range(dim)]
        for row in range(dim)
    ]


def _target_cluster(
    seed: int, split: str, index: int, top: int, left: int, dim: int, target: int
) -> tuple[tuple[int, int], ...]:
    if target == 0:
        rows, cols = (top - 4, top - 2), (left - 4, left - 2)
    elif target == 1:
        rows, cols = (top - 4, top - 2), (left + dim + 1, left + dim + 3)
    elif target == 2:
        rows, cols = (top + dim + 1, top + dim + 3), (left + dim + 1, left + dim + 3)
    else:
        rows, cols = (top + dim + 1, top + dim + 3), (left - 4, left - 2)
    scaffold = (
        (rows[0], cols[0]),
        (rows[0], cols[1]),
        (rows[1], cols[0]),
        (rows[1], cols[1]),
    )
    missing = _digest_int(seed, split, index, "cluster-missing") % 4
    return tuple(cell for position, cell in enumerate(scaffold) if position != missing)


def make_input(seed: int, *, split: str, index: int) -> list[list[int]]:
    seed = _validate_seed(seed)
    if split not in {"demo", "query"}:
        raise ValueError("split must be 'demo' or 'query'")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative exact integer")
    profiles = DEMO_PROFILES if split == "demo" else QUERY_PROFILES
    if index >= len(profiles):
        raise ValueError(f"{split} index {index} exceeds supported profiles")
    height, width, dim, top, left, marker, target, minority = profiles[index]
    shape = _minority_shape(seed, split, index, dim, minority)
    cluster = _target_cluster(seed, split, index, top, left, dim, target)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for d_row, row in enumerate(shape):
        for d_col, value in enumerate(row):
            grid[top + d_row][left + d_col] = value
    marker_row, marker_col = _expanded_corners(top, left, dim)[marker]
    grid[marker_row][marker_col] = 4
    for row, col in cluster:
        grid[row][col] = 4
    facts = analyze_input(grid)
    expected = {
        "yellow_source_diag": marker,
        "target_diag": target,
        "minority_diag": minority,
        "shape_dim": dim,
    }
    for key, value in expected.items():
        if facts[key] != value:
            raise AssertionError(f"constructed {key}={facts[key]} instead of {value}")
    return grid


def analyze_input(grid: Any) -> dict[str, Any]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or cell not in {0, 1, 4, 8} for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact colors 0,1,4,8")
    height = len(grid)
    shape_cells = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] in {1, 8}
    ]
    if not shape_cells:
        raise ValueError("input needs a nonempty color-1/8 shape")
    min_row = min(row for row, _, _ in shape_cells)
    max_row = max(row for row, _, _ in shape_cells)
    min_col = min(col for _, col, _ in shape_cells)
    max_col = max(col for _, col, _ in shape_cells)
    dim = max_row - min_row + 1
    if dim != max_col - min_col + 1:
        raise ValueError("shape bounding box must be square")
    if len(shape_cells) != dim * dim:
        raise ValueError("shape must densely fill its square bounding box")
    counts = {color: sum(value == color for _, _, value in shape_cells) for color in (1, 8)}
    if 0 in counts.values() or counts[1] == counts[8]:
        raise ValueError("shape colors must be present with a strict minority")
    minority_color = min(counts, key=counts.get)
    majority_color = 8 if minority_color == 1 else 1
    minority_cells = [
        (row, col) for row, col, value in shape_cells if value == minority_color
    ]
    minority_mean = (
        sum(row for row, _ in minority_cells) // len(minority_cells),
        sum(col for _, col in minority_cells) // len(minority_cells),
    )
    center_r = (min_row + max_row) // 2
    center_c = (min_col + max_col) // 2
    minority_diag = _diag(minority_mean, center_r, center_c)

    yellows = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 4
    ]
    if len(yellows) != 4:
        raise ValueError("input needs exactly four yellow cells")
    corners = _expanded_corners(min_row, min_col, dim)
    source_matches = [index for index, corner in enumerate(corners) if corner in yellows]
    if len(source_matches) != 1:
        raise ValueError("exactly one yellow must occupy an expanded shape corner")
    cluster = [cell for cell in yellows if cell not in corners]
    if len(cluster) != 3:
        raise ValueError("target cluster needs exactly three non-corner yellows")
    target_mean = (
        sum(row for row, _ in cluster) // len(cluster),
        sum(col for _, col in cluster) // len(cluster),
    )
    target_diag = _diag(target_mean, center_r, center_c)
    if any(_diag(cell, center_r, center_c) != target_diag for cell in cluster):
        raise ValueError("target cluster must occupy one shape-relative quadrant")
    return {
        "height": height,
        "width": width,
        "shape": [
            [grid[row][col] for col in range(min_col, max_col + 1)]
            for row in range(min_row, max_row + 1)
        ],
        "shape_top": min_row,
        "shape_left": min_col,
        "shape_dim": dim,
        "shape_size": dim * dim,
        "nonzero_count": len(shape_cells) + len(yellows),
        "corners": corners,
        "yellow_source_diag": source_matches[0],
        "target_diag": target_diag,
        "cluster": tuple(sorted(cluster)),
        "minority_color": minority_color,
        "majority_color": majority_color,
        "minority_count": counts[minority_color],
        "majority_count": counts[majority_color],
        "minority_mean": minority_mean,
        "minority_diag": minority_diag,
    }


def _rotate_shape(shape: list[list[int]], turns: int) -> list[list[int]]:
    result = [row[:] for row in shape]
    for _ in range(turns % 4):
        result = [list(row) for row in zip(*result[::-1], strict=True)]
    return result


def intermediate_source_diag(grid: list[list[int]], source_cue: str) -> int:
    source_cue = _validate_source_cue(source_cue)
    facts = analyze_input(grid)
    return (
        facts["yellow_source_diag"]
        if source_cue == "yellow_marker"
        else facts["minority_diag"]
    )


def apply_python(grid: list[list[int]], source_cue: str) -> list[list[int]]:
    source_diag = intermediate_source_diag(grid, source_cue)
    facts = analyze_input(grid)
    turns = (facts["target_diag"] - source_diag) % 4
    rotated = _rotate_shape(facts["shape"], turns)
    output = [[0 for _ in range(facts["width"])] for _ in range(facts["height"])]
    for d_row, row in enumerate(rotated):
        for d_col, value in enumerate(row):
            output[facts["shape_top"] + d_row][facts["shape_left"] + d_col] = value
    marker_row, marker_col = facts["corners"][facts["target_diag"]]
    output[marker_row][marker_col] = 4
    return output


def generate_episode(
    seed: int,
    *,
    source_cue: str,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    seed = _validate_seed(seed)
    source_cue = _validate_source_cue(source_cue)
    demos = _validate_count(demos, 2, 6, "demos")
    queries = _validate_count(queries, 1, 4, "queries")
    train = []
    for index in range(demos):
        grid = make_input(seed, split="demo", index=index)
        train.append({"input": grid, "output": apply_python(grid, source_cue)})
    test = []
    for index in range(queries):
        grid = make_input(seed, split="query", index=index)
        test.append({"input": grid, "output": apply_python(grid, source_cue)})
    identities = [
        hashlib.sha256(repr(pair["input"]).encode()).hexdigest()
        for pair in train + test
    ]
    if len(identities) != len(set(identities)):
        raise AssertionError("episode contains duplicate inputs")
    episode = {
        "schema": "d833a288bd7d-parametric-episode-v1",
        "train": train,
        "test": test,
        "program_solution": program_for(source_cue),
        "settings": {"source_cue": source_cue},
        "seed": seed,
    }
    certificate = teaching_certificate(episode, source_cue)
    if certificate["declared_setting_survivors"] != [source_cue]:
        raise AssertionError("demonstrations do not uniquely identify the source cue")
    if certificate["surviving_rivals"]:
        raise AssertionError(
            "a named shortcut survives the demonstrations: "
            + ", ".join(certificate["surviving_rivals"])
        )
    episode["teaching_certificate"] = certificate
    return episode



def _apply_with_source_diag(grid: list[list[int]], source_diag: int) -> list[list[int]]:
    if type(source_diag) is not int or source_diag not in range(4):
        raise ValueError("source_diag must be an exact integer in 0..3")
    facts = analyze_input(grid)
    turns = (facts["target_diag"] - source_diag) % 4
    rotated = _rotate_shape(facts["shape"], turns)
    output = [[0 for _ in range(facts["width"])] for _ in range(facts["height"])]
    for d_row, row in enumerate(rotated):
        for d_col, value in enumerate(row):
            output[facts["shape_top"] + d_row][facts["shape_left"] + d_col] = value
    marker_row, marker_col = facts["corners"][facts["target_diag"]]
    output[marker_row][marker_col] = 4
    return output


def _majority_source_diag(grid: list[list[int]]) -> int:
    facts = analyze_input(grid)
    cells = [
        (row, col)
        for row, values in enumerate(facts["shape"])
        for col, value in enumerate(values)
        if value == facts["majority_color"]
    ]
    mean = (
        sum(row for row, _ in cells) // len(cells),
        sum(col for _, col in cells) // len(cells),
    )
    center = (facts["shape_dim"] - 1) // 2
    return _diag(mean, center, center)


def _apply_reverse(grid: list[list[int]], source_cue: str) -> list[list[int]]:
    source_diag = intermediate_source_diag(grid, source_cue)
    facts = analyze_input(grid)
    turns = (source_diag - facts["target_diag"]) % 4
    rotated = _rotate_shape(facts["shape"], turns)
    output = [[0 for _ in range(facts["width"])] for _ in range(facts["height"])]
    for d_row, row in enumerate(rotated):
        for d_col, value in enumerate(row):
            output[facts["shape_top"] + d_row][facts["shape_left"] + d_col] = value
    marker_row, marker_col = facts["corners"][facts["target_diag"]]
    output[marker_row][marker_col] = 4
    return output


def _apply_fixed_turn(grid: list[list[int]], turns: int) -> list[list[int]]:
    facts = analyze_input(grid)
    rotated = _rotate_shape(facts["shape"], turns)
    output = [[0 for _ in range(facts["width"])] for _ in range(facts["height"])]
    for d_row, row in enumerate(rotated):
        for d_col, value in enumerate(row):
            output[facts["shape_top"] + d_row][facts["shape_left"] + d_col] = value
    marker_row, marker_col = facts["corners"][facts["target_diag"]]
    output[marker_row][marker_col] = 4
    return output


def _rivals(source_cue: str) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    source_cue = _validate_source_cue(source_cue)
    other = next(value for value in SOURCE_CUES if value != source_cue)
    rivals: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
        f"declared_setting:{other}": lambda grid: apply_python(grid, other),
        "reverse_direction": lambda grid: _apply_reverse(grid, source_cue),
        "majority_centroid": lambda grid: _apply_with_source_diag(
            grid, _majority_source_diag(grid)
        ),
    }
    for turns in range(4):
        rivals[f"fixed_turn:{turns}"] = (
            lambda grid, turns=turns: _apply_fixed_turn(grid, turns)
        )
    for source_diag in range(4):
        rivals[f"fixed_source:{source_diag}"] = (
            lambda grid, source_diag=source_diag: _apply_with_source_diag(
                grid, source_diag
            )
        )
    return rivals


def teaching_certificate(
    episode: dict[str, Any], source_cue: str
) -> dict[str, Any]:
    source_cue = _validate_source_cue(source_cue)
    demos = episode.get("train")
    queries = episode.get("test")
    if type(demos) is not list or type(queries) is not list or not demos or not queries:
        raise ValueError("episode must contain nonempty train/test lists")
    declared_setting_survivors = [
        setting
        for setting in SOURCE_CUES
        if all(
            apply_python(pair["input"], setting) == pair["output"]
            for pair in demos
        )
    ]
    surviving_rivals: list[str] = []
    query_changing_survivors: list[str] = []
    refutations: dict[str, list[int]] = {}
    for name, rival in _rivals(source_cue).items():
        mismatches = [
            index
            for index, pair in enumerate(demos)
            if rival(pair["input"]) != pair["output"]
        ]
        refutations[name] = mismatches
        if not mismatches:
            surviving_rivals.append(name)
            if any(rival(pair["input"]) != pair["output"] for pair in queries):
                query_changing_survivors.append(name)
    return {
        "declared_setting_survivors": declared_setting_survivors,
        "surviving_rivals": surviving_rivals,
        "query_changing_survivors": query_changing_survivors,
        "demo_refutation_indices": refutations,
        "demos_checked": len(demos),
        "queries_checked": len(queries),
        "scope": "Finite declared settings and named shortcut rivals only.",
    }
