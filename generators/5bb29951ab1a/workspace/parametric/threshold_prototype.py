"""Task-local parametric prototype for ARC task 5bb29951ab1a.

The canonical rule absorbs sparse-color dots when at least two orthogonal
neighbors have the modal nonzero rectangle color.  This prototype keeps every
other role and transformation fixed while choosing that threshold once per
episode from ``{1, 2, 3}``.

It is intentionally separate from the production ``generate`` entry point and
therefore does not alter or claim approval for the canonical task.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import random
import sys
import tempfile

TASK_ID = "5bb29951ab1a"
PROTOTYPE_VERSION = "1.0.0"
DEFAULT_THRESHOLD = 2
ALLOWED_THRESHOLDS = (1, 2, 3)

TASK_HOME = Path(__file__).resolve().parents[2]
ROOT = Path(__file__).resolve().parents[4]
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_threshold(threshold: int) -> None:
    if type(threshold) is not int or threshold not in ALLOWED_THRESHOLDS:
        raise ValueError(
            f"threshold must be one of {ALLOWED_THRESHOLDS}, got {threshold!r}"
        )


@lru_cache(maxsize=1)
def canonical_program() -> str:
    """Load the selected canonical Racket source for the task."""
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row.get("program_solution")
                if not isinstance(program, str) or not program.strip():
                    raise ValueError(f"canonical task {TASK_ID} has no Racket program")
                return program
    raise ValueError(f"canonical task {TASK_ID} is absent from {path}")


def racket_program(threshold: int) -> str:
    """Return exact Racket for one threshold setting.

    Threshold 2 is byte-for-byte the canonical authority.  Alternatives change
    only the executed comparison constant.
    """
    _validate_threshold(threshold)
    source = canonical_program()
    needle = "(>= adj 2)"
    if source.count(needle) != 1:
        raise ValueError("canonical threshold expression is not uniquely identifiable")
    if threshold == DEFAULT_THRESHOLD:
        return source
    return source.replace(needle, f"(>= adj {threshold})")


@lru_cache(maxsize=1)
def _production_generator():
    path = TASK_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("threshold_source_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load production generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _roles(grid) -> tuple[int, int]:
    counts = Counter(value for row in grid for value in row)
    nonzero = sorted(
        ((count, color) for color, count in counts.items() if color != 0),
        reverse=True,
    )
    if len(nonzero) != 2:
        raise ValueError(f"expected exactly two nonzero colors, found {sorted(counts)}")
    (rectangle_count, rectangle_color), (dot_count, dot_color) = nonzero
    if rectangle_count <= dot_count:
        raise ValueError("rectangle color must be strictly more frequent than dot color")
    return rectangle_color, dot_color


def _adjacent_count(grid, row: int, col: int, rectangle_color: int) -> int:
    height = len(grid)
    width = len(grid[0])
    return sum(
        1
        for dr, dc in _DIRS
        if 0 <= row + dr < height
        and 0 <= col + dc < width
        and grid[row + dr][col + dc] == rectangle_color
    )


def adjacency_histogram(grid) -> dict[int, int]:
    """Count sparse-color dots by original-input orthogonal support degree."""
    rectangle_color, dot_color = _roles(grid)
    histogram = {degree: 0 for degree in range(5)}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value == dot_color:
                histogram[_adjacent_count(grid, row_index, col_index, rectangle_color)] += 1
    return histogram


def apply_python(grid, threshold: int):
    """Independent Python mirror used for construction and parity assertions."""
    _validate_threshold(threshold)
    rectangle_color, dot_color = _roles(grid)
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value != dot_color:
                continue
            adjacent = _adjacent_count(grid, row_index, col_index, rectangle_color)
            output[row_index][col_index] = rectangle_color if adjacent >= threshold else 0
    return output


def _complete_threshold_witness(grid) -> bool:
    histogram = adjacency_histogram(grid)
    return (
        histogram[0] > 0
        and histogram[1] > 0
        and histogram[2] > 0
        and histogram[3] + histogram[4] > 0
    )


def build_episode(
    seed: int,
    *,
    threshold: int | None = None,
    n_train: int = 3,
    n_test: int = 1,
):
    """Build a complete fixed-threshold episode.

    Every retained input contains dots of support degrees 0, 1, 2, and at least
    one of 3/4.  Consequently each demonstration independently distinguishes all
    three allowed thresholds and shows both an absorbed and rejected dot.
    """
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(n_train) is not int or n_train < 3:
        raise ValueError("n_train must be an integer >= 3")
    if type(n_test) is not int or n_test < 1:
        raise ValueError("n_test must be an integer >= 1")

    if threshold is None:
        threshold = random.Random(seed).choice(ALLOWED_THRESHOLDS)
    _validate_threshold(threshold)

    generator = _production_generator()
    needed = n_train + n_test
    pairs = []
    accepted_indices = []
    generation_seed = seed * 1009 + 17
    bands = ("easy", "medium", "hard")

    for sample_index in range(600):
        band = bands[sample_index % len(bands)]
        grid = generator.generate(
            generation_seed,
            sample_index,
            difficulty=band,
            n_absorb=8,
            n_reject=8,
        )
        if not _complete_threshold_witness(grid):
            continue
        pairs.append({"input": grid, "output": apply_python(grid, threshold)})
        accepted_indices.append({"sample_index": sample_index, "difficulty": band})
        if len(pairs) == needed:
            break

    if len(pairs) != needed:
        raise RuntimeError(
            f"found only {len(pairs)}/{needed} complete threshold witnesses in 600 draws"
        )

    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": racket_program(threshold),
        "chain": ["infer_frequency_roles", "count_orthogonal_neighbors", f"threshold_{threshold}"],
        "meta": {
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "seed": seed,
            "generation_seed": generation_seed,
            "threshold": threshold,
            "default_threshold": DEFAULT_THRESHOLD,
            "allowed_thresholds": list(ALLOWED_THRESHOLDS),
            "canonical_setting": threshold == DEFAULT_THRESHOLD,
            "accepted": accepted_indices,
        },
    }


def public_challenge(episode):
    """Strip hidden rule metadata, executable source, and query answers."""
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def racket_outputs(program: str, grids):
    """Execute a supplied prototype program through the included Racket bridge."""
    if not isinstance(program, str) or not program.strip():
        raise ValueError("program must be a nonempty Racket source string")

    sys.path.insert(0, str(ROOT / "shared/runtime"))
    sys.path.insert(0, str(ROOT / "src"))
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-threshold-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        request = stage / "threshold-request.json"
        request.write_text(
            json.dumps({"program": program, "grids": grids}),
            encoding="utf-8",
        )
        script = r"""
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path('threshold-request.json').read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    outputs = [runner._apply_rule(bridge, name, grid) for grid in request['grids']]
    print(json.dumps(outputs))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                "Racket worker failed: "
                f"stderr={result['stderr']!r} stdout={result['stdout']!r}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs
