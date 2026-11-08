"""Proposed line-axis variant for the row-uniformity ARC family.

The production generator and canonical rule remain unchanged.  This task-local
prototype chooses one hidden ``line_axis`` once per episode:

* ``row`` (canonical/default): classify and paint complete rows.
* ``column``: classify and paint complete columns.

A line is gray (5) exactly when all of its cells are identical; otherwise it is
black (0).  Controlled inputs contain exactly one uniform row and one uniform
column, so every labelled pair distinguishes both settings.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any, Iterable

from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
)


TASK_ID = "2a5919c40197"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "line_axis"
PARAMETER_VALUES = ("row", "column")
DEFAULT_PARAMETER = "row"
N_TRAIN = 3
N_TEST = 1
_INPUT_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_CANONICAL_FRAGMENT = "(unique (row-at g r))"
_COLUMN_FRAGMENT = "(unique (col g c))"
HERE = Path(__file__).resolve().parent


def _validate_nonnegative_int(name: str, value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer (not bool, float, or string)")
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def validate_parameter(value: Any) -> str:
    if type(value) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a string")
    if value not in PARAMETER_VALUES:
        raise ValueError(
            f"unknown {PARAMETER_NAME}={value!r}; expected one of {PARAMETER_VALUES}"
        )
    return value


def choose_parameter(seed: Any, value: Any | None = None) -> str:
    """Choose one setting once for a deterministic complete episode."""
    seed = _validate_nonnegative_int("seed", seed)
    if value is not None:
        return validate_parameter(value)
    return PARAMETER_VALUES[seed % len(PARAMETER_VALUES)]


def canonical_program(root: str | Path | None = None) -> str:
    resolved = find_root(__file__) if root is None else Path(root)
    programs = []
    with canonical_path(resolved).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.append(row["program_solution"])
    if not programs or len(set(programs)) != 1:
        raise ValueError(
            f"expected one unambiguous canonical program for {TASK_ID}; "
            f"found {len(programs)} row(s) and {len(set(programs))} distinct program(s)"
        )
    return programs[0]


def racket_program(line_axis: Any, *, root: str | Path | None = None) -> str:
    """Materialize exact Racket source for one bounded axis setting."""
    axis = validate_parameter(line_axis)
    canonical = canonical_program(root)
    if axis == DEFAULT_PARAMETER:
        return canonical
    if canonical.count(_CANONICAL_FRAGMENT) != 1:
        raise ValueError("canonical row-expression edit point is absent or ambiguous")
    return canonical.replace(_CANONICAL_FRAGMENT, _COLUMN_FRAGMENT, 1)


def program_sha256(program: str) -> str:
    return hashlib.sha256(program.encode("utf-8")).hexdigest()


def _json_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(
        not isinstance(row, list)
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("expected rectangular rows of ARC colors 0..9")
    return [row[:] for row in grid]


def build_input(seed: Any, pair_index: Any) -> list[list[int]]:
    """Build a lawful input with exactly one uniform row and one uniform column."""
    seed = _validate_nonnegative_int("seed", seed)
    pair_index = _validate_nonnegative_int("pair_index", pair_index)
    rng = random.Random((seed + 1) * 1_000_003 + (pair_index + 1) * 97_409)

    height = rng.randint(4, 7)
    width = rng.randint(4, 7)
    uniform_row = rng.randrange(height)
    uniform_col = rng.randrange(width)
    palette = list(_INPUT_COLORS)
    rng.shuffle(palette)
    anchor, *fill_colors = palette[:4]

    grid = [
        [fill_colors[(r * width + c + pair_index) % len(fill_colors)] for c in range(width)]
        for r in range(height)
    ]
    for c in range(width):
        grid[uniform_row][c] = anchor
    for r in range(height):
        grid[r][uniform_col] = anchor
    return grid


def selected_generator_self_check(
    grid: list[list[int]], *, root: str | Path | None = None
) -> list[str]:
    """Run the selected generator's grammar check in either repository layout.

    Portable task-test snapshots intentionally contain two equivalent layouts:
    an execution package at ``puzzle_generators/`` and a repository mirror at
    ``shared/runtime/puzzle_generators/``.  Other tests may already have loaded
    the mirror package before this prototype runs.  Loading through the strict
    selected-source helper would then reject the already-cached, same-snapshot
    dependency tree.  This task-local probe instead accepts either dependency
    layout *inside the supplied root* and compiles the hash-bound mirror source
    directly.
    """
    resolved = find_root(__file__) if root is None else Path(root)
    resolved = resolved.resolve()
    source_candidates = (
        resolved / "generators" / TASK_ID / "generator.py",
        resolved / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    source = next((path for path in source_candidates if path.is_file()), None)
    if source is None:
        raise FileNotFoundError(
            f"selected generator source for {TASK_ID} is absent under {resolved}"
        )
    source = source.resolve()
    if not source.is_relative_to(resolved):
        raise ValueError(f"generator source escaped selected root: {source}")

    allowed_package_roots = tuple(
        path.resolve()
        for path in (
            resolved / "puzzle_generators",
            resolved / "shared" / "runtime" / "puzzle_generators",
        )
        if path.is_dir()
    )
    if not allowed_package_roots:
        raise ValueError(f"missing puzzle_generators dependencies under {resolved}")
    for name, module in tuple(sys.modules.items()):
        if name != "puzzle_generators" and not name.startswith("puzzle_generators."):
            continue
        origins = list(getattr(module, "__path__", []))
        origin = getattr(module, "__file__", None)
        if origin:
            origins.append(origin)
        if not origins or any(
            not any(Path(path).resolve().is_relative_to(root_path) for root_path in allowed_package_roots)
            for path in origins
        ):
            raise ImportError(
                f"{name} belongs to a source tree outside selected root {resolved}"
            )

    dependency_root = (
        resolved / "shared" / "runtime"
        if (resolved / "shared" / "runtime" / "puzzle_generators").is_dir()
        else resolved
    )
    body = source.read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    name = f"_parametric_selected_{TASK_ID}_{digest}"
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import selected generator {source}")
    generator = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    before_path = list(sys.path)
    try:
        sys.path.insert(0, str(dependency_root))
        sys.modules[name] = generator
        exec(compile(body, str(source), "exec"), generator.__dict__)
    except BaseException:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        raise
    finally:
        sys.path[:] = before_path
    return generator.self_check(deepcopy(grid))


def apply_rule(grid: list[list[int]], line_axis: Any) -> list[list[int]]:
    """Python assertion mirror; retained evidence labels are executed by Racket."""
    source = _validate_grid(grid)
    axis = validate_parameter(line_axis)
    height = len(source)
    width = len(source[0])
    if axis == "row":
        return [
            [5 if len(set(row)) == 1 else 0] * width
            for row in source
        ]

    column_uniform = [
        len({source[r][c] for r in range(height)}) == 1
        for c in range(width)
    ]
    return [
        [5 if column_uniform[c] else 0 for c in range(width)]
        for _r in range(height)
    ]


def surviving_parameter_values(
    demonstrations: Iterable[dict[str, Any]],
) -> list[str]:
    pairs = list(demonstrations)
    survivors = []
    for axis in PARAMETER_VALUES:
        if all(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and apply_rule(pair["input"], axis) == pair["output"]
            for pair in pairs
        ):
            survivors.append(axis)
    return survivors


def generate_episode(
    seed: Any,
    *,
    line_axis: Any | None = None,
    n_train: Any = N_TRAIN,
    n_test: Any = N_TEST,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Create a deterministic assertion-mirror episode for authoring/tests."""
    seed = _validate_nonnegative_int("seed", seed)
    if type(n_train) is not int or type(n_test) is not int:
        raise TypeError("n_train and n_test must be integers")
    if n_train < 1 or n_test < 1:
        raise ValueError("an episode needs at least one demonstration and one query")
    selected = choose_parameter(seed, line_axis)
    resolved = find_root(__file__) if root is None else Path(root)

    pairs = []
    for pair_index in range(n_train + n_test):
        grid = build_input(seed, pair_index)
        findings = selected_generator_self_check(grid, root=resolved)
        if findings:
            raise RuntimeError(
                f"controlled input {pair_index} is outside selected grammar: {findings}"
            )
        pairs.append({"input": grid, "output": apply_rule(grid, selected)})

    return {
        "schema": "arcpuzzles-task-parametric-prototype-v1",
        "status": "proposed_prototype",
        "task_id": TASK_ID,
        "version": PROTOTYPE_VERSION,
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": racket_program(selected, root=resolved),
        "meta": {
            "seed": seed,
            PARAMETER_NAME: selected,
            "parameter_values": list(PARAMETER_VALUES),
            "canonical_default": DEFAULT_PARAMETER,
            "parameter_selected_once_per_episode": True,
            "label_backend": "python_assertion_mirror_only",
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove the hidden setting, reference program, and query answers."""
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def execute_program(bridge: Any, program: str, grid: list[list[int]]) -> list[list[int]]:
    """Execute exact wrapped Racket bytes with ``g`` bound to one input."""
    if not program.startswith("(rule!") or not program.endswith(")"):
        raise ValueError("expected a rule! wrapped Racket program")
    bridge.define_grid("g", _validate_grid(grid))
    body = program[len("(rule!") : -1].strip()
    output = bridge.eval_text(f"({body} g)")
    return _validate_grid(output)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _rotation_records(pairs: list[dict[str, Any]], selected: str) -> list[dict[str, Any]]:
    records = []
    for query_index in range(len(pairs)):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        survivors = surviving_parameter_values(demos)
        records.append(
            {
                "query_index": query_index,
                "surviving_values": survivors,
                "identifiable": survivors == [selected],
            }
        )
    return records


def build_evidence(
    out: str | Path,
    *,
    seeds: Any = 6,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Build bounded Racket-backed evidence and public/private episode files."""
    seeds = _validate_nonnegative_int("seeds", seeds)
    if seeds < 2:
        raise ValueError("use at least two seeds so both settings are covered")
    resolved = find_root(__file__) if root is None else Path(root)
    output = Path(out)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"evidence directory must be new or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    from arc_repl.racket_bridge import RacketBridge, racket_runtime_status

    programs = {
        axis: racket_program(axis, root=resolved)
        for axis in PARAMETER_VALUES
    }
    (output / "rules").mkdir(exist_ok=True)
    for axis, program in programs.items():
        (output / "rules" / f"{axis}.rkt").write_text(program + "\n", encoding="utf-8")

    canonical = canonical_pairs(TASK_ID, root=resolved, labeled_only=True)
    canonical_row_matches = 0
    python_matches = {axis: 0 for axis in PARAMETER_VALUES}
    racket_labels = 0
    episodes = []
    execution_rows = []
    covering_seeds: dict[str, int] = {}

    with RacketBridge(startup_timeout=120) as bridge:
        for pair in canonical:
            observed = execute_program(bridge, programs["row"], pair["input"])
            canonical_row_matches += observed == pair["output"]

        for seed in range(seeds):
            selected = choose_parameter(seed)
            covering_seeds.setdefault(selected, seed)
            pair_records = []
            selected_pairs = []
            for pair_index in range(N_TRAIN + N_TEST):
                grid = build_input(seed, pair_index)
                findings = selected_generator_self_check(grid, root=resolved)
                if findings:
                    raise RuntimeError(
                        f"seed {seed} pair {pair_index} outside selected grammar: {findings}"
                    )
                outputs = {}
                for axis in PARAMETER_VALUES:
                    observed = execute_program(bridge, programs[axis], grid)
                    outputs[axis] = observed
                    racket_labels += 1
                    python_matches[axis] += observed == apply_rule(grid, axis)
                if outputs["row"] == outputs["column"]:
                    raise RuntimeError(
                        f"seed {seed} pair {pair_index} does not distinguish settings"
                    )
                pair_records.append(
                    {
                        "pair_index": pair_index,
                        "input": grid,
                        "input_sha256": _json_sha256(grid),
                        "outputs": outputs,
                        "output_sha256": {
                            axis: _json_sha256(value) for axis, value in outputs.items()
                        },
                    }
                )
                selected_pairs.append(
                    {"input": deepcopy(grid), "output": deepcopy(outputs[selected])}
                )

            rotations = _rotation_records(selected_pairs, selected)
            episode = {
                "schema": "2a5919c40197-line-axis-private-episode-v1",
                "status": "proposed_prototype",
                "task_id": TASK_ID,
                "seed": seed,
                "parameters": {PARAMETER_NAME: selected},
                "parameter_selected_once_per_episode": True,
                "program": programs[selected],
                "program_sha256": program_sha256(programs[selected]),
                "label_backend": "included_racket_bridge",
                "train": selected_pairs[:N_TRAIN],
                "test": selected_pairs[N_TRAIN:],
                "rotations": rotations,
            }
            episodes.append(episode)
            execution_rows.append(
                {
                    "seed": seed,
                    "selected": selected,
                    "pairs": pair_records,
                }
            )
            _write_json(output / "private" / f"episode-{seed:03d}.json", episode)
            _write_json(
                output / "public" / f"episode-{seed:03d}.json",
                public_challenge(episode),
            )

    if set(covering_seeds) != set(PARAMETER_VALUES):
        raise RuntimeError(f"bounded seed set did not cover both settings: {covering_seeds}")

    first = execution_rows[0]["pairs"][0]
    witness = {
        "task_id": TASK_ID,
        "seed": 0,
        "pair_index": 0,
        "input": first["input"],
        "row_output": first["outputs"]["row"],
        "column_output": first["outputs"]["column"],
        "outputs_differ": first["outputs"]["row"] != first["outputs"]["column"],
        "program_sha256": {
            axis: program_sha256(program) for axis, program in programs.items()
        },
    }
    _write_json(output / "private" / "same-input-setting-witness.json", witness)
    _write_json(
        output / "private" / "racket-executions.json",
        {
            "schema": "2a5919c40197-line-axis-racket-executions-v1",
            "runtime": racket_runtime_status(),
            "program_sha256": {
                axis: program_sha256(program) for axis, program in programs.items()
            },
            "episodes": execution_rows,
        },
    )

    canonical_check = {
        "task_id": TASK_ID,
        "canonical_pairs": len(canonical),
        "canonical_row_matches": canonical_row_matches,
        "row_program_byte_exact": programs["row"] == canonical_program(resolved),
        "canonical_program_sha256": program_sha256(canonical_program(resolved)),
    }
    _write_json(output / "private" / "canonical-default-check.json", canonical_check)

    total_pairs = seeds * (N_TRAIN + N_TEST)
    all_rotations = [record for episode in episodes for record in episode["rotations"]]
    report = {
        "schema": "2a5919c40197-line-axis-prototype-report-v1",
        "status": "proposed_prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameters": {
            PARAMETER_NAME: {
                "allowed": list(PARAMETER_VALUES),
                "default": DEFAULT_PARAMETER,
                "selection": "once per deterministic episode seed",
                "input_constraints": (
                    "each controlled input has exactly one uniform row and one "
                    "uniform column, with at least three non-output colors"
                ),
            }
        },
        "canonical_rule_unchanged": True,
        "canonical_default_byte_exact": canonical_check["row_program_byte_exact"],
        "canonical_row_matches": canonical_row_matches,
        "canonical_pair_count": len(canonical),
        "program_sha256": {
            axis: program_sha256(program) for axis, program in programs.items()
        },
        "racket_execution": {
            "labels": racket_labels,
            "expected_labels": total_pairs * len(PARAMETER_VALUES),
            "python_matches": python_matches,
            "expected_python_matches_per_setting": total_pairs,
        },
        "census": {
            "seeds": list(range(seeds)),
            "episodes": len(episodes),
            "demonstrations_per_episode": N_TRAIN,
            "queries_per_episode": N_TEST,
            "rotations": len(all_rotations),
            "identifiable_rotations": sum(r["identifiable"] for r in all_rotations),
            "covering_seeds": covering_seeds,
            "selected_parameter_by_seed": [
                {"seed": seed, PARAMETER_NAME: choose_parameter(seed)}
                for seed in range(seeds)
            ],
        },
        "same_input_witness": {
            "path": "private/same-input-setting-witness.json",
            "outputs_differ": witness["outputs_differ"],
        },
        "source_sha256": {
            "prototype.py": _file_sha256(HERE / "prototype.py"),
            "verify.py": _file_sha256(HERE / "verify.py"),
            "README.md": _file_sha256(HERE / "README.md"),
            "test_parametric_line_axis.py": _file_sha256(
                HERE.parents[1] / "tests" / "test_parametric_line_axis.py"
            ),
        },
        "evidence": [
            "private/canonical-default-check.json",
            "private/racket-executions.json",
            "private/same-input-setting-witness.json",
            "private/episode-*.json",
            "public/episode-*.json",
            "rules/row.rkt",
            "rules/column.rkt",
        ],
        "limitations": [
            "This is a task-local proposed prototype, not production integration or approval.",
            "Only row and column line axes are in the bounded parameter domain.",
            "Controlled inputs deliberately contain one uniform line on each axis; broader input distributions are untested.",
            "The finite census checks the declared alternative axis, not every conceivable rival rule.",
            "Public challenge projections omit hidden parameters, reference programs, and query answers.",
        ],
    }
    report["passed"] = bool(
        report["canonical_default_byte_exact"]
        and canonical_row_matches == len(canonical)
        and all(count == total_pairs for count in python_matches.values())
        and report["racket_execution"]["labels"]
        == report["racket_execution"]["expected_labels"]
        and report["census"]["identifiable_rotations"]
        == report["census"]["rotations"]
        and witness["outputs_differ"]
        and set(covering_seeds) == set(PARAMETER_VALUES)
    )
    _write_json(output / "report.json", report)

    members = sorted(
        path for path in output.rglob("*") if path.is_file() and path.name != "manifest.json"
    )
    _write_json(
        output / "manifest.json",
        {
            "schema": "2a5919c40197-line-axis-evidence-manifest-v1",
            "status": "proposed_prototype",
            "task_id": TASK_ID,
            "members": {
                path.relative_to(output).as_posix(): _file_sha256(path)
                for path in members
            },
        },
    )
    return report
