"""Task-local parametric family for vertical-gap filling.

The canonical setting is byte-for-byte the selected authority. The alternate
setting first performs that canonical fill (stage A), counts the newly activated
red centers by column (input-dependent intermediate), then recolors green cells
in the uniquely busiest activated column blue (stage B).
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "1409f5f7af2e"
DEFAULT = {"endpoint_treatment": "preserve"}
PARAMETERS = {"endpoint_treatment": ["preserve", "highlight_busiest"]}
SETTINGS = [
    {"endpoint_treatment": "preserve"},
    {"endpoint_treatment": "highlight_busiest"},
]
_PROGRAM_FILES = {
    "preserve": HERE / "canonical.rkt",
    "highlight_busiest": HERE / "highlight_busiest.rkt",
}

if str(REPO / "shared/runtime") not in sys.path:
    sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import public_challenge_bytes, public_challenge_id

# height, width, winner target count, decoy target counts, legacy fixed-column lure
_DEMO_PROFILES = (
    (9, 9, 2, (1,), 5),
    (10, 12, 3, (2,), 1),
    (12, 10, 3, (1, 1), 8),
    (15, 16, 4, (1,), 7),
    (18, 20, 4, (1, 1), 2),
    (24, 24, 3, (2, 1), 21),
)
_QUERY_PROFILES = (
    (8, 11, 2, (1,), 1),
    (14, 17, 3, (2,), 8),
    (21, 25, 4, (1, 1), 23),
    (30, 30, 3, (2, 1), 0),
)


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"endpoint_treatment"}:
        raise ValueError("settings must name exactly endpoint_treatment")
    value = settings["endpoint_treatment"]
    if type(value) is not str or value not in PARAMETERS["endpoint_treatment"]:
        raise ValueError("endpoint_treatment must be preserve or highlight_busiest")
    return {"endpoint_treatment": value}


def program(settings: object) -> str:
    chosen = _settings(settings)
    return _PROGRAM_FILES[chosen["endpoint_treatment"]].read_text()


def _grid(value: object) -> list[list[int]]:
    if type(value) is not list or not 3 <= len(value) <= 30:
        raise ValueError("grid must have 3..30 rows")
    if type(value[0]) is not list or not 3 <= len(value[0]) <= 30:
        raise ValueError("grid must have 3..30 columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact ARC integers 0..9")
    return value


def _targets(grid: list[list[int]]) -> list[tuple[int, int]]:
    _grid(grid)
    return [
        (row, col)
        for row in range(1, len(grid) - 1)
        for col in range(len(grid[0]))
        if grid[row][col] == 0
        and grid[row - 1][col] == 3
        and grid[row + 1][col] == 3
    ]


def stage_a(grid: list[list[int]]) -> list[list[int]]:
    """Canonical vertical-gap fill; this is the alternate rule's intermediate."""
    output = copy.deepcopy(_grid(grid))
    for row, col in _targets(grid):
        output[row][col] = 2
    return output


def busiest_activated_column(stage: list[list[int]]) -> int:
    stage = _grid(stage)
    counts = [sum(row[col] == 2 for row in stage) for col in range(len(stage[0]))]
    best = max(counts)
    if best <= 0:
        raise ValueError("stage A must activate at least one center")
    return counts.index(best)


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    chosen = _settings(settings)
    intermediate = stage_a(grid)
    if chosen["endpoint_treatment"] == "preserve":
        return intermediate
    winner = busiest_activated_column(intermediate)
    output = copy.deepcopy(intermediate)
    for row in range(len(output)):
        if output[row][winner] == 3:
            output[row][winner] = 1
    return output


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = json.dumps([TASK_ID, seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _paint_chain(grid: list[list[int]], col: int, count: int, start: int) -> None:
    if start < 0 or start + 2 * count >= len(grid):
        raise ValueError("chain does not fit")
    for offset in range(count + 1):
        row = start + 2 * offset
        if grid[row][col] != 0:
            raise ValueError("chain collision")
        grid[row][col] = 3


def _try_pattern(grid: list[list[int]], cells: list[tuple[int, int, int]], expected_targets: set[tuple[int, int]]) -> bool:
    if any(not (0 <= r < len(grid) and 0 <= c < len(grid[0])) or grid[r][c] != 0 for r, c, _ in cells):
        return False
    for row, col, value in cells:
        grid[row][col] = value
    if set(_targets(grid)) == expected_targets:
        return True
    for row, col, _ in cells:
        grid[row][col] = 0
    return False


def _place_long_gap_control(
    grid: list[list[int]],
    expected_targets: set[tuple[int, int]],
    rng: random.Random,
) -> None:
    candidates = [
        (row, col)
        for row in range(len(grid) - 4)
        for col in range(len(grid[0]))
    ]
    rng.shuffle(candidates)
    for row, col in candidates:
        if not all(grid[row + offset][col] == 0 for offset in range(5)):
            continue
        if _try_pattern(
            grid,
            [(row, col, 3), (row + 4, col, 3)],
            expected_targets,
        ):
            return
    raise ValueError("could not place nonlocal-vertical control")


def _place_diagonal_control(
    grid: list[list[int]],
    expected_targets: set[tuple[int, int]],
    rng: random.Random,
) -> None:
    candidates = [
        (row, col)
        for row in range(1, len(grid) - 1)
        for col in range(1, len(grid[0]) - 1)
    ]
    rng.shuffle(candidates)
    for row, col in candidates:
        cells = ((row - 1, col - 1), (row, col), (row + 1, col + 1))
        if not all(grid[r][c] == 0 for r, c in cells):
            continue
        if _try_pattern(
            grid,
            [(row - 1, col - 1, 3), (row + 1, col + 1, 3)],
            expected_targets,
        ):
            return
    raise ValueError("could not place diagonal-connectivity control")


def _build_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    if split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    _integer(index, 0, len(profiles) - 1, "index")
    height, width, winner_count, decoy_counts, legacy_col = profiles[index]
    rng = _rng(seed, split, index)
    grid = [[0 for _ in range(width)] for _ in range(height)]

    # Size and query position are public, so they must not encode the selector.
    # Keep the rightmost nuisance run stable, but move the true busiest column
    # across seeds and explicitly avoid both column zero and the legacy profile
    # column that an earlier version accidentally exposed as a lookup table.
    nuisance_col = width - 1
    winner_candidates = [
        col for col in range(width - 1) if col not in {0, legacy_col}
    ]
    if split == "train" and index == 0:
        winner_candidates = [col for col in winner_candidates if col >= 2]
    elif split == "train" and index == 1:
        winner_candidates = [col for col in winner_candidates if col <= width - 3]
    winner_col = rng.choice(winner_candidates)

    available = [c for c in range(width) if c not in {winner_col, nuisance_col}]
    if split == "train" and index == 0:
        # A smaller chain to the left and above defeats leftmost/first-scan
        # selectors while the winner still has the greater activation count.
        first_decoy = rng.choice([col for col in available if col < winner_col])
        remainder = [col for col in available if col != first_decoy]
        rng.shuffle(remainder)
        decoy_cols = [first_decoy, *remainder[: len(decoy_counts) - 1]]
    elif split == "train" and index == 1:
        # A smaller chain to the right and below defeats rightmost/last-scan
        # selectors. Together the first two demonstrations cross all rank cues.
        first_decoy = rng.choice([col for col in available if col > winner_col])
        remainder = [col for col in available if col != first_decoy]
        rng.shuffle(remainder)
        decoy_cols = [first_decoy, *remainder[: len(decoy_counts) - 1]]
    else:
        rng.shuffle(available)
        decoy_cols = available[: len(decoy_counts)]

    if split == "train" and index == 0:
        winner_start = rng.randrange(2, height - 2 * winner_count)
    elif split == "train" and index == 1:
        winner_start = 0
    elif split == "test" and index == 3:
        winner_start = 0
    else:
        winner_start = rng.randrange(height - 2 * winner_count)
    _paint_chain(grid, winner_col, winner_count, winner_start)
    for decoy_index, (col, count) in enumerate(zip(decoy_cols, decoy_counts)):
        if split == "train" and index == 0 and decoy_index == 0:
            start = 0
        elif split == "train" and index == 1 and decoy_index == 0:
            start = height - (2 * count + 1)
        elif split == "test" and index == 3 and decoy_index == 0:
            start = height - (2 * count + 1)
        else:
            start = rng.randrange(height - 2 * count)
        _paint_chain(grid, col, count, start)

    expected_targets = set(_targets(grid))
    if len(expected_targets) != winner_count + sum(decoy_counts):
        raise AssertionError("target chain construction drifted")

    # A raw-green-frequency confound: this column has more green cells than the
    # winning target column, but consecutive greens create no activated centers.
    run = height
    run_start = 0
    for row in range(run_start, run_start + run):
        grid[row][nuisance_col] = 3
    if set(_targets(grid)) != expected_targets:
        raise AssertionError("nuisance run created an accidental target")

    # Explicit wrong-connectivity controls keep the two-demo minimum from relying
    # on random clutter to distinguish immediate vertical adjacency.
    _place_long_gap_control(grid, expected_targets, rng)
    _place_diagonal_control(grid, expected_targets, rng)

    # Horizontal, blocked, and wrong-color controls; add only when they preserve
    # the exact target set. Larger profiles receive more spread across the canvas.
    horizontal_wanted = 2 if height < 15 else 4 if height < 25 else 8
    blocked_wanted = 1 if height < 15 else 2 if height < 25 else 4
    wrong_color_wanted = 1 if height < 15 else 2 if height < 25 else 4
    for kind, wanted in (("horizontal", horizontal_wanted), ("blocked", blocked_wanted), ("other", wrong_color_wanted)):
        placed = 0
        for attempt in range(600):
            if placed >= wanted:
                break
            if kind == "horizontal":
                row = rng.randrange(height)
                col = rng.randrange(width - 2)
                cells = [(row, col, 3), (row, col + 2, 3)]
            elif kind == "blocked":
                row = rng.randrange(height - 2)
                col = rng.randrange(width)
                cells = [(row, col, 3), (row + 1, col, 5), (row + 2, col, 3)]
            else:
                row = rng.randrange(height - 2)
                col = rng.randrange(width)
                cells = [(row, col, 4), (row + 2, col, 4)]
            if _try_pattern(grid, cells, expected_targets):
                placed += 1
        if placed != wanted:
            raise ValueError(f"could not place {wanted} {kind} controls")

    # Harmless scattered greens and colored decoys increase content spread while
    # preserving the target intermediate. For the 30x30 stress case, force both
    # bottom and right boundaries to be occupied.
    harmless_wanted = 2 if height < 15 else 5 if height < 25 else 10
    candidates = [(r, c) for r in range(height) for c in range(width)]
    rng.shuffle(candidates)
    placed = 0
    for row, col in candidates:
        if placed >= harmless_wanted:
            break
        if _try_pattern(grid, [(row, col, 3)], expected_targets):
            placed += 1
    if placed != harmless_wanted:
        raise ValueError("could not place harmless green spread")

    # Every early lesson must visibly refute a fixed-column-zero endpoint rule.
    # If column zero is otherwise empty, add one harmless green there without
    # changing the stage-A target set.
    if not any(row[0] == 3 for row in grid):
        for row in [0, height - 1, height // 2, 1, max(0, height - 2)]:
            if _try_pattern(grid, [(row, 0, 3)], expected_targets):
                break
        else:
            raise ValueError("could not place fixed-column control")

    # Retain a visible lure in the old size-indexed column, so the historical
    # dimension-lookup rival changes an output and is directly testable.
    if not any(row[legacy_col] == 3 for row in grid):
        for row in [0, height - 1, height // 2, 1, max(0, height - 2)]:
            if _try_pattern(grid, [(row, legacy_col, 3)], expected_targets):
                break
        else:
            raise ValueError("could not place legacy-column control")

    # Stage B colors every green in the selected column, not only the greens
    # that are endpoints of activated gaps. Guarantee an off-chain witness in
    # every scene so that partial endpoint-only execution cannot fit the lesson.
    winner_endpoints = {
        endpoint
        for row, col in expected_targets
        if col == winner_col
        for endpoint in ((row - 1, col), (row + 1, col))
    }
    if not any(
        grid[row][winner_col] == 3 and (row, winner_col) not in winner_endpoints
        for row in range(height)
    ):
        candidate_rows = [0, height - 1, height // 2, 1, max(0, height - 2)]
        candidate_rows.extend(row for row in range(height) if row not in candidate_rows)
        for row in candidate_rows:
            if _try_pattern(grid, [(row, winner_col, 3)], expected_targets):
                break
        else:
            raise ValueError("could not place off-chain winner-column control")

    targets = _targets(grid)
    counts = [sum(col == c for _, col in targets) for c in range(width)]
    if counts[winner_col] != winner_count or any(count >= winner_count for c, count in enumerate(counts) if c != winner_col):
        raise AssertionError("winner must be unique")
    green_counts = [sum(row[c] == 3 for row in grid) for c in range(width)]
    if max(range(width), key=lambda c: green_counts[c]) == winner_col:
        raise AssertionError("raw-green confound failed")
    if any(value in {1, 2} for row in grid for value in row):
        raise AssertionError("blue and red are output-only")
    return grid


def _endpoint_usage(grid: list[list[int]]) -> dict[tuple[int, int], int]:
    usage: dict[tuple[int, int], int] = {}
    for row, col in _targets(grid):
        for endpoint in ((row - 1, col), (row + 1, col)):
            usage[endpoint] = usage.get(endpoint, 0) + 1
    return usage


def _shortcut(name: str, grid: list[list[int]], chosen: dict[str, str]) -> list[list[int]]:
    if name in {"nonlocal_vertical", "vertical_or_diagonal"}:
        stage = copy.deepcopy(grid)
        height, width = len(grid), len(grid[0])
        for row in range(height):
            for col in range(width):
                if grid[row][col] != 0:
                    continue
                if name == "nonlocal_vertical":
                    matched = (
                        any(grid[above][col] == 3 for above in range(row))
                        and any(grid[below][col] == 3 for below in range(row + 1, height))
                    )
                else:
                    matched = (
                        0 < row < height - 1
                        and grid[row - 1][col] == 3
                        and grid[row + 1][col] == 3
                    )
                    if 0 < row < height - 1 and 0 < col < width - 1:
                        matched = matched or (
                            grid[row - 1][col - 1] == 3
                            and grid[row + 1][col + 1] == 3
                        ) or (
                            grid[row - 1][col + 1] == 3
                            and grid[row + 1][col - 1] == 3
                        )
                if matched:
                    stage[row][col] = 2
        if chosen["endpoint_treatment"] == "preserve":
            return stage
        winner = busiest_activated_column(stage)
        output = copy.deepcopy(stage)
        for row in range(height):
            if output[row][winner] == 3:
                output[row][winner] = 1
        return output

    if name == "horizontal_gaps":
        output = copy.deepcopy(grid)
        for row in range(len(grid)):
            for col in range(1, len(grid[0]) - 1):
                if grid[row][col] == 0 and grid[row][col - 1] == 3 and grid[row][col + 1] == 3:
                    output[row][col] = 2
        return output
    if name == "isolated_targets_only":
        output = copy.deepcopy(grid)
        usage = _endpoint_usage(grid)
        for row, col in _targets(grid):
            if usage[(row - 1, col)] == usage[(row + 1, col)] == 1:
                output[row][col] = 2
        if chosen["endpoint_treatment"] == "highlight_busiest" and any(2 in row for row in output):
            winner = busiest_activated_column(output)
            for row in range(len(output)):
                if output[row][winner] == 3:
                    output[row][winner] = 1
        return output

    intermediate = stage_a(grid)
    targets = _targets(grid)
    if name == "fixed_column_zero":
        columns = [0]
    elif name == "dimension_lookup":
        legacy_by_shape = {
            (height, width): legacy
            for height, width, _, _, legacy in (*_DEMO_PROFILES, *_QUERY_PROFILES)
        }
        columns = [legacy_by_shape[(len(grid), len(grid[0]))]]
    elif name == "most_raw_green_column":
        green_counts = [sum(row[c] == 3 for row in grid) for c in range(len(grid[0]))]
        columns = [max(range(len(green_counts)), key=lambda c: green_counts[c])]
    elif name == "all_target_columns":
        columns = sorted({col for _, col in targets})
    elif name == "winner_endpoints_only":
        counts = [sum(col == candidate for _, col in targets) for candidate in range(len(grid[0]))]
        winner = counts.index(max(counts))
        endpoints = {
            endpoint
            for row, col in targets
            if col == winner
            for endpoint in ((row - 1, col), (row + 1, col))
        }
        output = copy.deepcopy(intermediate)
        for row, col in endpoints:
            if output[row][col] == 3:
                output[row][col] = 1
        return output
    elif name == "leftmost_target_column":
        columns = [min(col for _, col in targets)]
    elif name == "rightmost_target_column":
        columns = [max(col for _, col in targets)]
    elif name == "first_scan_target_column":
        columns = [targets[0][1]]
    elif name == "last_scan_target_column":
        columns = [targets[-1][1]]
    else:
        raise KeyError(name)
    output = copy.deepcopy(intermediate)
    for row in range(len(output)):
        for col in columns:
            if output[row][col] == 3:
                output[row][col] = 1
    return output


SHORTCUTS = (
    "horizontal_gaps",
    "nonlocal_vertical",
    "vertical_or_diagonal",
    "isolated_targets_only",
    "fixed_column_zero",
    "dimension_lookup",
    "most_raw_green_column",
    "all_target_columns",
    "winner_endpoints_only",
    "leftmost_target_column",
    "rightmost_target_column",
    "first_scan_target_column",
    "last_scan_target_column",
)


def certify(episode: dict, execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None) -> dict:
    chosen = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program does not match fixed episode settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train/test lists")
    _integer(len(train), 2, 6, "demos")
    if len(test) != 4:
        raise ValueError("queries must contain exactly four pairs")
    pairs = train + test
    if len({digest(pair.get("input")) for pair in pairs}) != len(pairs):
        raise ValueError("all demonstration and query inputs must be distinct")
    apply = execute or (lambda text, grid: transform(
        grid, next(setting for setting in SETTINGS if program(setting) == text)
    ))
    for pair in pairs:
        _grid(pair.get("input"))
        _grid(pair.get("output"))

    records = []
    for setting in SETTINGS:
        disagreements = [
            index
            for index, pair in enumerate(train)
            if apply(program(setting), pair["input"]) != pair["output"]
        ]
        records.append({"settings": setting, "disagreeing_demo_indices": disagreements})
    survivors = [dict(row["settings"]) for row in records if not row["disagreeing_demo_indices"]]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify selected setting: {survivors}")

    shortcut_refutations: dict[str, list[int]] = {}
    shortcut_survivors = []
    for name in SHORTCUTS:
        disagreements = [
            index
            for index, pair in enumerate(train)
            if _shortcut(name, pair["input"], chosen) != pair["output"]
        ]
        shortcut_refutations[name] = disagreements
        if not disagreements:
            shortcut_survivors.append(name)
    if shortcut_survivors:
        raise ValueError(f"named shortcuts survive: {shortcut_survivors}")

    queries = []
    for pair in test:
        got = apply(program(chosen), pair["input"])
        if got != pair["output"]:
            raise ValueError("query label disagrees with selected setting")
        queries.append({
            "input_sha256": digest(pair["input"]),
            "output_sha256": digest(pair["output"]),
            "survivors": survivors,
        })
    return {
        "scope": f"two endpoint-treatment settings plus {len(SHORTCUTS)} finite shortcuts",
        "racket_checked": execute is not None,
        "survivors": survivors,
        "shortcut_survivors": shortcut_survivors,
        "demo_refutations": records,
        "shortcut_refutations": shortcut_refutations,
        "queries": queries,
    }


def generate(seed: int, settings: object = None, demos: int = 3, queries: int = 4) -> dict:
    _integer(seed, -(2**63), 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")
    chosen = _settings(DEFAULT if settings is None else settings)
    train = []
    for index in range(demos):
        grid = _build_input(seed, "train", index)
        train.append({"input": grid, "output": transform(grid, chosen)})
    test = []
    for index in range(4):
        grid = _build_input(seed, "test", index)
        test.append({"input": grid, "output": transform(grid, chosen)})
    episode = {
        "schema": "1409-busiest-column-parametric-proposal-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": program(chosen),
        "program_sha256": hashlib.sha256(program(chosen).encode()).hexdigest(),
    }
    episode["certificate"] = certify(episode)
    return episode


def public_turn(episode: dict, index: int) -> dict:
    _integer(index, 0, 3, "query index")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != 4:
        raise ValueError("episode must retain four controller-side queries")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[index]["input"])}],
    }


class RacketRunner:
    """One live protected bridge for bounded evidence; never a Python fallback."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule

        _grid(grid)
        if source not in self.cache:
            self.cache[source] = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({self.cache[source]} {literal})")

    def __exit__(self, *exc):
        self.bridge.close()
