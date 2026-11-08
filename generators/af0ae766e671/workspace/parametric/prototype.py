"""Native global-selection family for af0ae766e671.

The canonical setting paints every XOR occupancy cell.  The nearby setting first
counts the occupied cells in the two input panels, derives which panel is sparser,
and then paints only positions exclusively occupied in that selected panel.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "af0ae766e671"
SELECTIONS = ("xor", "sparser_panel_only")
SETTINGS = tuple({"selection": value} for value in SELECTIONS)
HERE = Path(__file__).resolve().parent
CANONICAL_PATH = HERE / "canonical.rkt"
SPARSER_PATH = HERE / "sparser_panel_only.rkt"
DENSER_PATH = HERE / "denser_panel_only.rkt"

DEMO_DIMS = ((8, 5), (10, 6), (12, 8), (14, 9), (16, 11), (18, 12))
QUERY_DIMS = ((12, 15), (18, 20), (24, 27), (30, 30))
# Counts are (00, lower-only, upper-only, both); each row sums to half_h * width.
DEMO_COUNTS = (
    (9, 6, 2, 3),   # upper is sparser
    (13, 2, 10, 5), # lower is sparser
    (20, 18, 9, 1),
    (23, 7, 21, 12),
    (31, 35, 16, 6),
    (37, 14, 36, 21),
)
QUERY_COUNTS = (
    (20, 30, 15, 25),
    (40, 25, 50, 65),
    (60, 100, 60, 104),
    (70, 80, 140, 160),
)


def _plain_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a plain Python int in [{low}, {high}]")
    return value


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"selection"}:
        raise ValueError("settings must contain exactly selection")
    selection = settings["selection"]
    if type(selection) is not str or selection not in SELECTIONS:
        raise ValueError(f"selection must be one of {SELECTIONS}")
    return {"selection": selection}


def program(settings: Any) -> str:
    selection = _settings(settings)["selection"]
    return (CANONICAL_PATH if selection == "xor" else SPARSER_PATH).read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}|sparser-panel-v1|{seed}|{split}|{index}".encode()).digest()
    return random.Random(int.from_bytes(raw[:16], "big"))


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    height, width = len(grid), len(grid[0])
    if height % 2 or height > 30 or width > 30:
        raise ValueError("grid must have even height and fit within 30x30")
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be plain integer ARC colors")
    return height // 2, width


def occupancy_states(grid: Any) -> list[int]:
    half, width = _validate_grid(grid)
    return [
        2 * int(grid[r][c] != 0) + int(grid[half + r][c] != 0)
        for r in range(half)
        for c in range(width)
    ]


def occupancy_stats(grid: Any) -> dict[str, Any]:
    states = occupancy_states(grid)
    counts = Counter(states)
    for state in range(4):
        counts.setdefault(state, 0)
    upper = counts[2] + counts[3]
    lower = counts[1] + counts[3]
    if upper == lower:
        raise ValueError("panels must have unequal occupied-cell counts")
    return {
        "state_counts": {state: counts[state] for state in range(4)},
        "upper_count": upper,
        "lower_count": lower,
        "sparser": "upper" if upper < lower else "lower",
    }


def _solve_selection(grid: Any, selection: str) -> list[list[int]]:
    half, width = _validate_grid(grid)
    stats = occupancy_stats(grid)
    output = [[0] * width for _ in range(half)]
    for r in range(half):
        for c in range(width):
            upper = grid[r][c] != 0
            lower = grid[half + r][c] != 0
            if selection == "xor":
                chosen = upper != lower
            elif selection == "sparser_panel_only":
                chosen = upper and not lower if stats["sparser"] == "upper" else lower and not upper
            elif selection == "denser_panel_only":
                chosen = lower and not upper if stats["sparser"] == "upper" else upper and not lower
            elif selection == "upper_only":
                chosen = upper and not lower
            elif selection == "lower_only":
                chosen = lower and not upper
            elif selection == "and":
                chosen = upper and lower
            elif selection == "or":
                chosen = upper or lower
            elif selection == "xnor":
                chosen = upper == lower
            elif selection == "sparser_including_overlap":
                chosen = upper if stats["sparser"] == "upper" else lower
            elif selection == "denser_including_overlap":
                chosen = lower if stats["sparser"] == "upper" else upper
            else:
                raise ValueError("unknown selection")
            output[r][c] = 6 if chosen else 0
    return output


def solve(grid: Any, settings: Any) -> list[list[int]]:
    return _solve_selection(grid, _settings(settings)["selection"])


def _counts_for(seed: int, split: str, index: int, half: int, width: int) -> tuple[int, int, int, int]:
    base = list((DEMO_COUNTS if split == "train" else QUERY_COUNTS)[index])
    total = half * width
    if sum(base) != total:
        raise RuntimeError("count schedule does not match dimensions")
    # Seed-dependent, balance-preserving perturbations diversify state frequencies
    # while retaining the scheduled sparser-panel direction and all four states.
    rng = _rng(seed, split + "-counts", index)
    for _ in range(3):
        source = rng.randrange(4)
        target = rng.randrange(4)
        if source == target or base[source] <= 2:
            continue
        candidate = base.copy()
        candidate[source] -= 1
        candidate[target] += 1
        upper = candidate[2] + candidate[3]
        lower = candidate[1] + candidate[3]
        scheduled_upper_sparse = base[2] < base[1]
        if upper != lower and (upper < lower) == scheduled_upper_sparse:
            base = candidate
    return tuple(base)  # type: ignore[return-value]


def _state_layout(seed: int, split: str, index: int, half: int, width: int, counts: tuple[int, int, int, int]) -> list[int]:
    rng = _rng(seed, split + "-layout", index)
    positions = [(r, c) for r in range(half) for c in range(width)]
    corner_order = ((0, 0), (0, width - 1), (half - 1, 0), (half - 1, width - 1))
    forced = set(corner_order[: min(counts[3], len(corner_order))])
    assigned = {position: 3 for position in forced}
    remaining = list(counts)
    remaining[3] -= len(forced)
    pool = [state for state, count in enumerate(remaining) for _ in range(count)]
    rng.shuffle(pool)
    open_positions = [position for position in positions if position not in forced]
    # Sort by a seed-dependent geometric key after shuffling so states are spread
    # across the panel rather than appearing as count-sized contiguous blocks.
    rng.shuffle(open_positions)
    open_positions.sort(key=lambda p: ((7 * p[0] + 11 * p[1] + rng.randrange(17)) % 23, p[0], p[1]))
    if len(pool) != len(open_positions):
        raise RuntimeError("state pool length mismatch")
    for position, state in zip(open_positions, pool):
        assigned[position] = state
    return [assigned[(r, c)] for r in range(half) for c in range(width)]


def scene(seed: int, split: str, index: int) -> list[list[int]]:
    if split == "train":
        height, width = DEMO_DIMS[index]
    elif split == "test":
        height, width = QUERY_DIMS[index]
    else:
        raise ValueError("split must be train or test")
    half = height // 2
    counts = _counts_for(seed, split, index, half, width)
    states = _state_layout(seed, split, index, half, width, counts)
    rng = _rng(seed, split + "-palette", index)
    top_color, bottom_color = rng.sample(range(1, 10), 2)
    grid = [[0] * width for _ in range(height)]
    for position, state in enumerate(states):
        r, c = divmod(position, width)
        if state & 2:
            grid[r][c] = top_color
        if state & 1:
            grid[half + r][c] = bottom_color
    stats = occupancy_stats(grid)
    if set(stats["state_counts"]) != {0, 1, 2, 3} or min(stats["state_counts"].values()) <= 0:
        raise RuntimeError("constructed scene lacks complete occupancy support")
    for setting in SETTINGS:
        solve(grid, setting)
    return grid


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    _plain_int("seed", seed, 0, 2**63 - 1)
    _plain_int("demos", demos, 2, 6)
    _plain_int("queries", queries, 1, 4)
    normalized = _settings(settings)
    episode = {"settings": normalized, "program_solution": program(normalized), "train": [], "test": []}
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = scene(seed, split, index)
            episode[split].append({"input": grid, "output": solve(grid, normalized)})
    return episode


def public_turn(episode: dict[str, Any], query_index: Any = 0) -> dict[str, Any]:
    _plain_int("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])} for pair in episode["train"]],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def fit_settings(train: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [setting for setting in SETTINGS if all(solve(pair["input"], setting) == pair["output"] for pair in train)]


def rival_predictions(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    results = {f"setting:{name}": _solve_selection(grid, name) for name in SELECTIONS}
    for name in (
        "denser_panel_only",
        "upper_only",
        "lower_only",
        "and",
        "or",
        "xnor",
        "sparser_including_overlap",
        "denser_including_overlap",
    ):
        results[name] = _solve_selection(grid, name)
    return results


def self_review(episode: dict[str, Any]) -> dict[str, Any]:
    names = tuple(rival_predictions(episode["train"][0]["input"]))
    survivors = []
    harmful = []
    for name in names:
        if all(rival_predictions(pair["input"])[name] == pair["output"] for pair in episode["train"]):
            if name.startswith("setting:"):
                survivors.append(name.split(":", 1)[1])
            elif any(rival_predictions(pair["input"])[name] != pair["output"] for pair in episode["test"]):
                harmful.append(name)
    return {"intended_survivors": survivors, "harmful_survivors": harmful, "rivals_checked": len(names)}


def diff_cells(left: list[list[int]], right: list[list[int]]) -> int:
    height = max(len(left), len(right))
    width = max(max((len(row) for row in left), default=0), max((len(row) for row in right), default=0))
    return sum(
        (left[r][c] if r < len(left) and c < len(left[r]) else None)
        != (right[r][c] if r < len(right) and c < len(right[r]) else None)
        for r in range(height)
        for c in range(width)
    )


def causal_case() -> dict[str, Any]:
    grid = scene(0, "train", 0)
    stats = occupancy_stats(grid)
    correct = _solve_selection(grid, "sparser_panel_only")
    wrong = _solve_selection(grid, "denser_panel_only")
    return {
        "input": grid,
        "settings": {"selection": "sparser_panel_only"},
        "intermediate_value": {
            "upper_count": stats["upper_count"],
            "lower_count": stats["lower_count"],
            "selected_panel": stats["sparser"],
        },
        "output": correct,
        "counterfactual_output": wrong,
        "difference_cells": diff_cells(correct, wrong),
        "ablation": "wrong_intermediate",
    }


def episode_digest(episode: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(episode, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

# Backward-compatible surface for the earlier reviewed 27-setting exploratory
# prototype.  Native promotion uses program()/generate() above; these wrappers
# preserve the prior task-local evidence contracts and CLI without making that
# exploratory family part of the promoted parameter domain.
def _load_legacy_module():
    import importlib.util
    import sys

    path = HERE / "legacy_27_settings.py"
    name = "_af0ae766e671_legacy_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_LEGACY = _load_legacy_module()
Parameters = _LEGACY.Parameters
DEFAULT = _LEGACY.DEFAULT
emit_program = _LEGACY.emit_program
execute_program = _LEGACY.execute_program
sample_parameters = _LEGACY.sample_parameters
covering_seeds = _LEGACY.covering_seeds
public_challenge = _LEGACY.public_challenge
check_identifiability = _LEGACY.check_identifiability
distinct_witness = _LEGACY.distinct_witness
canonical_parity = _LEGACY.canonical_parity


def make_episode(seed, *, difficulty=None, bridge=None):
    original = _LEGACY.sample_parameters
    _LEGACY.sample_parameters = globals()["sample_parameters"]
    try:
        return _LEGACY.make_episode(seed, difficulty=difficulty, bridge=bridge)
    finally:
        _LEGACY.sample_parameters = original


def _audit(out, seed_start, bridge):
    """Run the historical 27-setting audit without rebinding its generator.

    The task-local tests intentionally monkeypatch this module's ``make_episode``
    to inject a single rejected row.  Delegating by overwriting
    ``_LEGACY.make_episode`` creates a recursion loop because the compatibility
    wrapper itself calls the legacy function.  Keep the old evidence schema but
    invoke the public compatibility surface dynamically for each attempted row.
    """
    seeds = _LEGACY.covering_seeds(seed_start)
    programs = [
        {
            "parameters": parameters.as_dict(),
            "program": _LEGACY.emit_program(parameters),
            "program_sha256": _LEGACY._text_digest(_LEGACY.emit_program(parameters)),
        }
        for parameters in _LEGACY.SETTINGS
    ]
    _LEGACY._write_json(out / "programs.json", programs)
    parity = _LEGACY.canonical_parity(bridge=bridge)
    _LEGACY._write_json(out / "canonical-parity.json", parity)
    witness = _LEGACY.distinct_witness(bridge=bridge)
    _LEGACY._write_json(out / "witness.json", witness)

    episode_summaries, failures = [], []
    with (out / "episodes.private.jsonl").open("w", encoding="utf-8") as private, \
            (out / "challenges.public.jsonl").open("w", encoding="utf-8") as public:
        for index, seed in enumerate(seeds):
            parameters = globals()["sample_parameters"](seed)
            try:
                episode = globals()["make_episode"](seed, bridge=bridge)
            except Exception as exc:
                failures.append(
                    {
                        "attempt_index": index,
                        "line_index": None,
                        "seed": seed,
                        "parameters": parameters.as_dict(),
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
            else:
                private.write(json.dumps(episode, sort_keys=True, separators=(",", ":")) + "\n")
                public.write(json.dumps(_LEGACY.public_challenge(episode), separators=(",", ":")) + "\n")
                private.flush()
                public.flush()
                episode_summaries.append(
                    {
                        "attempt_index": index,
                        "line_index": len(episode_summaries),
                        "seed": seed,
                        "parameters": parameters.as_dict(),
                        "program_sha256": episode["program_sha256"],
                        "survivors": episode["identifiability"]["survivors"],
                    }
                )
            print(
                json.dumps(
                    {
                        "episode": index + 1,
                        "requested": len(seeds),
                        "seed": seed,
                        "completed": len(episode_summaries),
                        "failed": len(failures),
                    }
                ),
                flush=True,
            )

    ambiguous_train = [
        {"input": [[9, 9, 9, 9], [4, 4, 4, 4]], "output": [[3, 3, 3, 3]]}
    ]
    ambiguity = {
        "purpose": "diagnostic only: intentionally missing occupancy states; never an emitted episode",
        "train": ambiguous_train,
        "identifiability": _LEGACY.check_identifiability(ambiguous_train, bridge=bridge),
    }
    _LEGACY._write_json(out / "ambiguity.json", ambiguity)
    passed = (
        parity["passed"]
        and witness["all_settings_distinct"]
        and not failures
        and len(episode_summaries) == len(_LEGACY.SETTINGS)
        and ambiguity["identifiability"]["survivors"]
        == [_LEGACY.Parameters("and", 3).as_dict(), _LEGACY.Parameters("or", 3).as_dict()]
    )
    report = {
        "schema": _LEGACY.VERSION + "-audit",
        "status": "prototype",
        "passed": passed,
        "task_id": _LEGACY.TASK,
        "default": _LEGACY.DEFAULT.as_dict(),
        "parameter_values": {"operation": ["xor", "and", "or"], "output_color": list(range(1, 10))},
        "parameter_dependent_input_constraints": [],
        "input_contract": "two equally sized stacked panels; one distinct nonzero color per panel; all four occupancy states",
        "seed_start": seed_start,
        "seed_search_end": max(seeds),
        "selected_seeds": seeds,
        "settings_requested": len(_LEGACY.SETTINGS),
        "episodes_completed": len(episode_summaries),
        "demonstrations_per_episode": 3,
        "queries_per_episode": 1,
        "canonical_pairs_checked": parity["pairs_checked"],
        "distinct_witness_outputs": witness["distinct_outputs"],
        "rival_settings_per_episode": len(_LEGACY.SETTINGS),
        "episodes": episode_summaries,
        "failures": failures,
        "sources": _LEGACY._sources(),
        "runtime": bridge.runtime_identity,
        "limitations": [
            "Proposed task-local prototype, not a production parametric API or approval.",
            "One seed-selected episode per setting; finite evidence, not all seeds or all valid inputs.",
            "Identifiability is relative to these 27 declared settings, not every possible ARC rule.",
            "Diagnostic ambiguity is retained and intentionally outside the full-state generation domain.",
            "Public and private JSONL rows align by order; disclose only the public file to a solver.",
        ],
    }
    _LEGACY._write_json(out / "report.json", report)
    return report


def legacy_main(argv=None):
    return _LEGACY.main(argv)


if __name__ == "__main__":
    raise SystemExit(legacy_main())
