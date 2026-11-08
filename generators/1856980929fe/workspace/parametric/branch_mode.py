#!/usr/bin/env python3
"""Proposed episode-level branch-direction extension for ARC task 1856980929fe.

The selected production generator and canonical Racket authority remain unchanged.
This task-local prototype chooses one hidden ``branch_mode`` once per episode:
the canonical two-sided fan, a left-only fan, or a right-only fan.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


TASK_ID = "1856980929fe"
PARAMETER_SPEC = {
    "name": "branch_mode",
    "values": ("both", "left", "right"),
    "default": "both",
}

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[2]
ROOT = HERE.parents[4]
GENERATOR_PATH = TASK_DIR / "generator.py"
CANONICAL_LEDGER = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"

_BOTH_BRANCHES = """(or
                                                   (let ((nc (- c0 (* k rw))))
                                                     (and (>= c nc) (< c (+ nc rw))))
                                                   (let ((nc (+ c0 (* k rw))))
                                                     (and (>= c nc) (< c (+ nc rw)))))"""
_LEFT_BRANCH = """(let ((nc (- c0 (* k rw))))
                                                     (and (>= c nc) (< c (+ nc rw))))"""
_RIGHT_BRANCH = """(let ((nc (+ c0 (* k rw))))
                                                     (and (>= c nc) (< c (+ nc rw))))"""


def _load_generator():
    name = f"parametric_branch_mode_{TASK_ID}_generator"
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load selected generator: {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_GEN = _load_generator()


def _validate_branch_mode(branch_mode: str) -> str:
    if type(branch_mode) is not str or branch_mode not in PARAMETER_SPEC["values"]:
        raise ValueError(
            f"branch_mode must be one of {PARAMETER_SPEC['values']}, got {branch_mode!r}"
        )
    return branch_mode


def canonical_rule() -> str:
    with CANONICAL_LEDGER.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source:
                    raise RuntimeError(f"canonical row {TASK_ID} has no program_solution")
                return source
    raise RuntimeError(f"canonical row {TASK_ID} not found")


def materialize_rule(branch_mode: str = "both") -> str:
    """Return exact executable Racket for one proposed branch setting."""
    mode = _validate_branch_mode(branch_mode)
    source = canonical_rule()
    if mode == "both":
        return source
    if source.count(_BOTH_BRANCHES) != 1:
        raise RuntimeError("canonical branch condition changed; refusing textual variant")
    replacement = _LEFT_BRANCH if mode == "left" else _RIGHT_BRANCH
    return source.replace(_BOTH_BRANCHES, replacement, 1)


def _empty_grid(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def apply_python(grid: list[list[int]], branch_mode: str = "both") -> list[list[int]]:
    """Independent Python mirror of one materialized branch setting."""
    mode = _validate_branch_mode(branch_mode)
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a nonempty grid")
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")

    out = _empty_grid(height, width)
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if value == 3:
                out[row_index][column_index] = 3

    directions = (-1, 1) if mode == "both" else ((-1,) if mode == "left" else (1,))
    for row0, column0, rect_height, rect_width in _GEN._corner_rectangles(grid):
        level = 1
        while row0 + level * rect_height < height:
            row_start = row0 + level * rect_height
            for direction in directions:
                column_start = column0 + direction * level * rect_width
                for row_index in range(row_start, min(row_start + rect_height, height)):
                    for column_index in range(
                        max(0, column_start), min(width, column_start + rect_width)
                    ):
                        out[row_index][column_index] = 3
            level += 1
    return out


def grid_sha256(grid: list[list[int]]) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def choose_branch_mode(seed: int) -> str:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    values = PARAMETER_SPEC["values"]
    return values[seed % len(values)]


def generator_sha256() -> str:
    return hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()


def prototype_sha256() -> str:
    return hashlib.sha256(HERE.read_bytes()).hexdigest()


def _validate_episode_counts(
    *, seed: int, start_index: int, n_train: int, n_test: int, max_attempts: int
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if type(start_index) is not int or start_index < 0:
        raise ValueError("start_index must be a nonnegative integer (not bool)")
    if type(n_train) is not int or n_train < 1:
        raise ValueError("n_train must be a positive integer (not bool)")
    if type(n_test) is not int or n_test < 1:
        raise ValueError("n_test must be a positive integer (not bool)")
    if type(max_attempts) is not int or max_attempts < 1:
        raise ValueError("max_attempts must be a positive integer (not bool)")


def build_episode(
    *,
    seed: int,
    branch_mode: str | None = None,
    difficulty: str = "medium",
    start_index: int = 0,
    n_train: int = 5,
    n_test: int = 4,
    max_attempts: int = 256,
    labeler=None,
) -> dict[str, Any]:
    """Build one fixed-setting episode from pairwise-distinguishing inputs."""
    _validate_episode_counts(
        seed=seed,
        start_index=start_index,
        n_train=n_train,
        n_test=n_test,
        max_attempts=max_attempts,
    )
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")
    selected = choose_branch_mode(seed) if branch_mode is None else _validate_branch_mode(branch_mode)
    selected_labeler = apply_python if labeler is None else labeler
    needed = n_train + n_test
    accepted: list[dict[str, Any]] = []
    accepted_indices: list[int] = []
    seen_inputs: set[str] = set()
    rejected_nondistinguishing = 0
    rejected_duplicate = 0

    for attempt in range(max_attempts):
        sample_index = start_index + attempt
        grid = _GEN.generate(seed, sample_index, difficulty=difficulty)
        input_digest = grid_sha256(grid)
        if input_digest in seen_inputs:
            rejected_duplicate += 1
            continue
        outputs = {
            mode: apply_python(grid, mode) for mode in PARAMETER_SPEC["values"]
        }
        if len({grid_sha256(output) for output in outputs.values()}) != len(outputs):
            rejected_nondistinguishing += 1
            continue
        label = selected_labeler(grid, selected)
        accepted.append({"input": grid, "output": label})
        accepted_indices.append(sample_index)
        seen_inputs.add(input_digest)
        if len(accepted) == needed:
            break

    if len(accepted) != needed:
        raise RuntimeError(
            "sampler exhausted before producing "
            f"{needed} distinct branch-discriminating inputs: accepted {len(accepted)} "
            f"of {max_attempts} attempts"
        )

    return {
        "schema": "1856980929fe-branch-mode-episode-v1",
        "train": accepted[:n_train],
        "test": accepted[n_train:],
        "meta": {
            "task_id": TASK_ID,
            "prototype": True,
            "status": "proposed_not_selected",
            "parameters": {PARAMETER_SPEC["name"]: selected},
            "parameter_scope": "chosen once per episode",
            "allowed_values": list(PARAMETER_SPEC["values"]),
            "canonical_default": PARAMETER_SPEC["default"],
            "seed": seed,
            "difficulty": difficulty,
            "start_index": start_index,
            "accepted_sample_indices": accepted_indices,
            "attempts_used": accepted_indices[-1] - start_index + 1,
            "rejected_nondistinguishing": rejected_nondistinguishing,
            "rejected_duplicate": rejected_duplicate,
            "generator_version": _GEN.VERSION,
            "generator_sha256": generator_sha256(),
        },
    }


def _episode_mode(episode: dict[str, Any]) -> str:
    try:
        return _validate_branch_mode(episode["meta"]["parameters"][PARAMETER_SPEC["name"]])
    except (KeyError, TypeError) as exc:
        raise ValueError("episode is missing branch_mode metadata") from exc


def parameter_rival_findings(episode: dict[str, Any]) -> list[str]:
    selected = _episode_mode(episode)
    demos = episode.get("train")
    if not isinstance(demos, list) or not demos:
        return ["episode needs at least one demonstration"]
    findings: list[str] = []
    for rival in PARAMETER_SPEC["values"]:
        if rival == selected:
            continue
        if all(apply_python(pair["input"], rival) == pair["output"] for pair in demos):
            findings.append(
                f"demonstrations do not distinguish branch_mode={selected!r} from {rival!r}"
            )
    return findings


def query_identifiability(episode: dict[str, Any]) -> list[dict[str, Any]]:
    selected = _episode_mode(episode)
    demos = episode.get("train")
    queries = episode.get("test")
    if not isinstance(demos, list) or not demos:
        raise ValueError("episode needs demonstrations")
    if not isinstance(queries, list) or not queries:
        raise ValueError("episode needs queries")
    rows = []
    for query_index, query in enumerate(queries):
        rival_rows = []
        for rival in PARAMETER_SPEC["values"]:
            if rival == selected:
                continue
            fits_demos = all(
                apply_python(pair["input"], rival) == pair["output"] for pair in demos
            )
            changes_query = apply_python(query["input"], rival) != query["output"]
            rival_rows.append(
                {
                    "branch_mode": rival,
                    "fits_demonstrations": fits_demos,
                    "changes_query": changes_query,
                }
            )
        rows.append(
            {
                "query_index": query_index,
                "rivals": rival_rows,
                "identifiable_from_demonstrations": not any(
                    row["fits_demonstrations"] for row in rival_rows
                ),
                "all_rivals_change_query": all(
                    row["changes_query"] for row in rival_rows
                ),
            }
        )
    return rows


def public_challenge(episode: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    from copy import deepcopy

    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list) or not train or not test:
        raise ValueError("episode must contain nonempty train/test lists")
    try:
        return {
            "train": [
                {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                for pair in train
            ],
            "test": [{"input": deepcopy(pair["input"])} for pair in test],
        }
    except (KeyError, TypeError) as exc:
        raise ValueError("episode pairs are malformed") from exc


def _reviewer_support():
    name = f"parametric_branch_mode_{TASK_ID}_reviewer_support"
    module = sys.modules.get(name)
    if module is not None:
        return module
    path = ROOT / "shared" / "runtime" / "reviewer_support.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load reviewer support: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def public_bytes(episode: dict[str, Any]) -> bytes:
    return _reviewer_support().public_challenge_bytes(public_challenge(episode))


def public_id(episode: dict[str, Any]) -> str:
    return _reviewer_support().public_challenge_id(public_challenge(episode))


def _grid_literal(grid: list[list[int]]) -> str:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colors 0..9 (not bool)")
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    )
    return f"'({rows})"


def _racket_runtime():
    import types

    scripts = sys.modules.get("scripts")
    if scripts is None:
        scripts = types.ModuleType("scripts")
        scripts.__path__ = [str(ROOT / "shared" / "tools")]
        sys.modules["scripts"] = scripts
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    return RacketBridge, wrap_rule


def _execute_racket(bridge, wrap_rule, source: str, grid: list[list[int]]) -> list[list[int]]:
    expression = f"({wrap_rule(source)} {_grid_literal(grid)})"
    output = bridge.eval_text(expression)
    if not isinstance(output, list) or not output or not isinstance(output[0], list):
        raise RuntimeError(f"prototype rule returned non-grid output: {output!r}")
    return [[int(value) for value in row] for row in output]


def apply_racket(grid: list[list[int]], branch_mode: str = "both") -> list[list[int]]:
    """Execute one exact materialized rule through the bundled Racket bridge."""
    source = materialize_rule(branch_mode)
    RacketBridge, wrap_rule = _racket_runtime()
    with RacketBridge(timeout=20, max_calls_before_restart=8) as bridge:
        return _execute_racket(bridge, wrap_rule, source, grid)



def _canonical_pairs() -> list[dict[str, Any]]:
    with CANONICAL_LEDGER.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            train = row.get("train")
            test = row.get("test")
            if not isinstance(train, list) or not train:
                raise RuntimeError(f"canonical row {TASK_ID} has no training pairs")
            tests = test if isinstance(test, list) else [test]
            pairs = [*train, *tests]
            if any(
                not isinstance(pair, dict)
                or "input" not in pair
                or "output" not in pair
                for pair in pairs
            ):
                raise RuntimeError(f"canonical row {TASK_ID} has malformed pairs")
            return pairs
    raise RuntimeError(f"canonical row {TASK_ID} not found")


def _source_sha256(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def build_evidence(
    *,
    seeds: list[int] | tuple[int, ...],
    difficulty: str = "medium",
    start_index: int = 0,
    n_train: int = 5,
    n_test: int = 4,
    max_attempts: int = 256,
) -> dict[str, Any]:
    """Execute exact Racket programs and retain parity/identifiability evidence."""
    if not isinstance(seeds, (list, tuple)) or not seeds:
        raise ValueError("seeds must be a nonempty list or tuple")
    normalized_seeds: list[int] = []
    for seed in seeds:
        if type(seed) is not int:
            raise TypeError("every seed must be an integer (not bool)")
        if seed < 0:
            raise ValueError("every seed must be nonnegative")
        normalized_seeds.append(seed)
    if len(normalized_seeds) != len(set(normalized_seeds)):
        raise ValueError("seeds must be distinct")
    selected_modes = {choose_branch_mode(seed) for seed in normalized_seeds}
    if PARAMETER_SPEC["default"] not in selected_modes or len(selected_modes) < 2:
        raise ValueError(
            "evidence seeds must include the canonical default and at least one alternative setting"
        )

    programs = {
        mode: {
            "source": materialize_rule(mode),
            "canonical_default": mode == PARAMETER_SPEC["default"],
        }
        for mode in PARAMETER_SPEC["values"]
    }
    for row in programs.values():
        row["sha256"] = _source_sha256(row["source"])
        row["bytes"] = len(row["source"].encode("utf-8"))

    RacketBridge, wrap_rule = _racket_runtime()
    canonical_checks: list[dict[str, Any]] = []
    episode_rows: list[dict[str, Any]] = []
    racket_labeled_pairs = 0
    python_parity_passed = 0
    identifiable_queries = 0
    total_queries = 0

    with RacketBridge(timeout=20, max_calls_before_restart=64) as bridge:
        default_source = programs[PARAMETER_SPEC["default"]]["source"]
        for pair_index, pair in enumerate(_canonical_pairs()):
            actual = _execute_racket(bridge, wrap_rule, default_source, pair["input"])
            passed = actual == pair["output"]
            canonical_checks.append(
                {
                    "pair_index": pair_index,
                    "input_sha256": grid_sha256(pair["input"]),
                    "expected_sha256": grid_sha256(pair["output"]),
                    "actual_sha256": grid_sha256(actual),
                    "passed": passed,
                }
            )
            if not passed:
                raise AssertionError(
                    f"canonical Racket default failed canonical pair {pair_index}"
                )

        for seed in normalized_seeds:
            mode = choose_branch_mode(seed)
            source = programs[mode]["source"]

            def racket_labeler(grid, selected_mode, *, _source=source, _mode=mode):
                if selected_mode != _mode:
                    raise AssertionError(
                        f"episode selected {selected_mode!r}, expected {_mode!r}"
                    )
                return _execute_racket(bridge, wrap_rule, _source, grid)

            episode = build_episode(
                seed=seed,
                branch_mode=mode,
                difficulty=difficulty,
                start_index=start_index,
                n_train=n_train,
                n_test=n_test,
                max_attempts=max_attempts,
                labeler=racket_labeler,
            )
            parity_checks: list[dict[str, Any]] = []
            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    expected = apply_python(pair["input"], mode)
                    passed = pair["output"] == expected
                    parity_checks.append(
                        {
                            "split": split,
                            "pair_index": pair_index,
                            "input_sha256": grid_sha256(pair["input"]),
                            "racket_output_sha256": grid_sha256(pair["output"]),
                            "python_output_sha256": grid_sha256(expected),
                            "passed": passed,
                        }
                    )
                    racket_labeled_pairs += 1
                    if passed:
                        python_parity_passed += 1
                    else:
                        raise AssertionError(
                            f"Racket/Python parity failed for seed={seed}, "
                            f"mode={mode}, {split}[{pair_index}]"
                        )

            rival_findings = parameter_rival_findings(episode)
            if rival_findings:
                raise AssertionError(
                    f"parameter lesson is ambiguous for seed={seed}: {rival_findings}"
                )
            query_rows = query_identifiability(episode)
            total_queries += len(query_rows)
            identifiable_queries += sum(
                row["identifiable_from_demonstrations"]
                and row["all_rivals_change_query"]
                for row in query_rows
            )
            episode_rows.append(
                {
                    "public_id": public_id(episode),
                    "seed": seed,
                    "branch_mode": mode,
                    "program_sha256": programs[mode]["sha256"],
                    "episode": episode,
                    "rival_findings": rival_findings,
                    "query_identifiability": query_rows,
                    "racket_python_checks": parity_checks,
                }
            )

    summary = {
        "episodes": len(episode_rows),
        "racket_labeled_pairs": racket_labeled_pairs,
        "canonical_checks": len(canonical_checks),
        "canonical_passed": sum(row["passed"] for row in canonical_checks),
        "python_parity_passed": python_parity_passed,
        "identifiable_queries": identifiable_queries,
        "total_queries": total_queries,
    }
    return {
        "schema": "1856980929fe-branch-mode-evidence-v1",
        "task_id": TASK_ID,
        "parameter_spec": {
            "name": PARAMETER_SPEC["name"],
            "values": list(PARAMETER_SPEC["values"]),
            "default": PARAMETER_SPEC["default"],
            "scope": "chosen once per episode",
        },
        "generator": {
            "version": _GEN.VERSION,
            "rule_hash": _GEN.RULE_HASH,
            "sha256": generator_sha256(),
        },
        "prototype": {
            "path": "workspace/parametric/branch_mode.py",
            "sha256": prototype_sha256(),
        },
        "programs": programs,
        "canonical_checks": canonical_checks,
        "episodes": episode_rows,
        "summary": summary,
        "limitations": [
            "Prototype evidence only; the selected production generator and canonical authority are unchanged.",
            "Sampler evidence is bounded to the supplied seeds, difficulty, start index, and max_attempts.",
        ],
    }


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def write_evidence(out_dir: str | Path, evidence: dict[str, Any]) -> dict[str, Any]:
    """Write a private audit bundle plus public, answer-free ARC challenges."""
    episodes = evidence.get("episodes")
    programs = evidence.get("programs")
    if not isinstance(episodes, list) or not isinstance(programs, dict):
        raise ValueError("evidence must contain programs and episodes")
    expected_prototype = {
        "path": "workspace/parametric/branch_mode.py",
        "sha256": prototype_sha256(),
    }
    if evidence.get("prototype") != expected_prototype:
        raise ValueError("prototype source mismatch in evidence")

    ids: list[str] = []
    for row in episodes:
        if not isinstance(row, dict) or not isinstance(row.get("episode"), dict):
            raise ValueError("evidence contains a malformed episode row")
        claimed = row.get("public_id")
        actual = public_id(row["episode"])
        if claimed != actual:
            raise ValueError(
                f"public challenge id mismatch: claimed {claimed!r}, computed {actual!r}"
            )
        ids.append(actual)
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate public challenge id in evidence")

    manifest_programs: dict[str, dict[str, Any]] = {}
    program_files: list[tuple[str, str]] = []
    for mode in PARAMETER_SPEC["values"]:
        row = programs.get(mode)
        if not isinstance(row, dict) or not isinstance(row.get("source"), str):
            raise ValueError(f"evidence is missing exact program for branch_mode={mode}")
        source = row["source"]
        digest = _source_sha256(source)
        if row.get("sha256") != digest:
            raise ValueError(f"program hash mismatch for branch_mode={mode}")
        rule_name = f"{digest}.rkt"
        program_files.append((rule_name, source))
        manifest_programs[mode] = {
            "sha256": digest,
            "bytes": len(source.encode("utf-8")),
            "canonical_default": mode == PARAMETER_SPEC["default"],
            "private_path": f"rules/{rule_name}",
        }

    destination = Path(out_dir)
    if destination.is_symlink():
        raise ValueError(f"evidence destination must not be a symlink: {destination}")
    if destination.exists() and not destination.is_dir():
        raise ValueError(f"evidence destination is not a directory: {destination}")
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"evidence destination is not empty: {destination}")

    public_dir = destination / "public"
    private_dir = destination / "private"
    rules_dir = private_dir / "rules"
    episodes_dir = private_dir / "episodes"
    public_dir.mkdir(parents=True, exist_ok=True)
    rules_dir.mkdir(parents=True, exist_ok=True)
    episodes_dir.mkdir(parents=True, exist_ok=True)
    for rule_name, source in program_files:
        (rules_dir / rule_name).write_text(source, encoding="utf-8")

    manifest_episodes: list[dict[str, Any]] = []
    ordered_episodes = sorted(episodes, key=lambda row: row["public_id"])
    for row in ordered_episodes:
        challenge_id = row["public_id"]
        episode = row["episode"]
        public_payload = public_bytes(episode)
        (public_dir / f"challenge_{challenge_id}.json").write_bytes(public_payload)
        (episodes_dir / f"{challenge_id}.json").write_bytes(_json_bytes(episode))
        manifest_episodes.append(
            {
                "public_id": challenge_id,
                "public_sha256": hashlib.sha256(public_payload).hexdigest(),
                "seed": row.get("seed"),
                "branch_mode": row.get("branch_mode"),
                "program_sha256": row.get("program_sha256"),
                "rival_findings": row.get("rival_findings", []),
                "query_identifiability": row.get("query_identifiability", []),
                "racket_python_checks": row.get("racket_python_checks", []),
                "private_episode_path": f"episodes/{challenge_id}.json",
                "public_challenge_path": f"../public/challenge_{challenge_id}.json",
            }
        )

    manifest = {
        "schema": evidence.get("schema"),
        "task_id": evidence.get("task_id"),
        "parameter_spec": evidence.get("parameter_spec"),
        "generator": evidence.get("generator"),
        "prototype": expected_prototype,
        "programs": manifest_programs,
        "canonical_checks": evidence.get("canonical_checks", []),
        "episodes": manifest_episodes,
        "summary": evidence.get("summary"),
        "limitations": evidence.get("limitations", []),
    }
    (private_dir / "manifest.json").write_bytes(_json_bytes(manifest))
    return manifest



def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing evidence file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON evidence file: {path}: {exc}") from exc


def _private_path(private_dir: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ValueError("manifest contains an invalid private path")
    base = private_dir.resolve()
    candidate = (private_dir / relative).resolve()
    if candidate != base and base not in candidate.parents:
        raise ValueError(f"private evidence path escapes bundle: {relative!r}")
    return candidate


def verify_evidence(
    out_dir: str | Path, *, rerun_racket: bool = False
) -> dict[str, int]:
    """Verify retained hashes, privacy boundaries, and optionally every Racket label."""
    destination = Path(out_dir)
    if destination.is_symlink():
        raise ValueError(f"evidence destination must not be a symlink: {destination}")
    private_dir = destination / "private"
    public_dir = destination / "public"
    manifest = _read_json(private_dir / "manifest.json")
    if not isinstance(manifest, dict):
        raise ValueError("private manifest must be a JSON object")
    if manifest.get("schema") != "1856980929fe-branch-mode-evidence-v1":
        raise ValueError("private manifest schema mismatch")
    if manifest.get("task_id") != TASK_ID:
        raise ValueError("private manifest task mismatch")
    expected_parameter_spec = {
        "name": PARAMETER_SPEC["name"],
        "values": list(PARAMETER_SPEC["values"]),
        "default": PARAMETER_SPEC["default"],
        "scope": "chosen once per episode",
    }
    if manifest.get("parameter_spec") != expected_parameter_spec:
        raise ValueError("private manifest parameter specification mismatch")
    expected_generator = {
        "version": _GEN.VERSION,
        "rule_hash": _GEN.RULE_HASH,
        "sha256": generator_sha256(),
    }
    if manifest.get("generator") != expected_generator:
        raise ValueError("generator source mismatch in private manifest")
    expected_prototype = {
        "path": "workspace/parametric/branch_mode.py",
        "sha256": prototype_sha256(),
    }
    if manifest.get("prototype") != expected_prototype:
        raise ValueError("prototype source mismatch in private manifest")

    programs = manifest.get("programs")
    if not isinstance(programs, dict) or set(programs) != set(PARAMETER_SPEC["values"]):
        raise ValueError("manifest must contain exactly the three branch_mode programs")
    program_sources: dict[str, str] = {}
    program_hashes: dict[str, str] = {}
    expected_rule_paths: set[str] = set()
    for mode in PARAMETER_SPEC["values"]:
        row = programs[mode]
        if not isinstance(row, dict):
            raise ValueError(f"program manifest row is malformed for {mode}")
        source_path = _private_path(private_dir, row.get("private_path"))
        try:
            source_bytes = source_path.read_bytes()
        except FileNotFoundError as exc:
            raise ValueError(f"missing exact Racket program: {source_path}") from exc
        digest = hashlib.sha256(source_bytes).hexdigest()
        if digest != row.get("sha256"):
            raise ValueError(f"program hash mismatch for branch_mode={mode}")
        expected_relative = f"rules/{digest}.rkt"
        if row.get("private_path") != expected_relative:
            raise ValueError(f"program path mismatch for branch_mode={mode}")
        expected_rule_paths.add(expected_relative)
        try:
            source = source_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Racket program is not UTF-8 for branch_mode={mode}") from exc
        if source != materialize_rule(mode):
            raise ValueError(f"retained Racket program drift for branch_mode={mode}")
        program_sources[mode] = source
        program_hashes[mode] = digest

    rules_dir = private_dir / "rules"
    actual_rule_paths = {
        path.relative_to(private_dir).as_posix()
        for path in rules_dir.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if actual_rule_paths != expected_rule_paths:
        raise ValueError(
            "private rule file set mismatch: "
            f"expected {sorted(expected_rule_paths)}, got {sorted(actual_rule_paths)}"
        )
    if any(path.is_symlink() for path in rules_dir.rglob("*")):
        raise ValueError("private rule files must not be symlinks")

    rows = manifest.get("episodes")
    if not isinstance(rows, list) or not rows:
        raise ValueError("manifest must contain at least one episode")
    public_ids = [row.get("public_id") if isinstance(row, dict) else None for row in rows]
    if any(not isinstance(value, str) for value in public_ids):
        raise ValueError("manifest contains an invalid public challenge id")
    if public_ids != sorted(public_ids):
        raise ValueError("manifest episodes are not sorted by public challenge id")
    if len(public_ids) != len(set(public_ids)):
        raise ValueError("duplicate public challenge id in manifest")

    expected_episode_paths = {f"episodes/{challenge_id}.json" for challenge_id in public_ids}
    for row in rows:
        expected_path = f"episodes/{row['public_id']}.json"
        if row.get("private_episode_path") != expected_path:
            raise ValueError(
                f"private episode path mismatch for public id {row['public_id']}"
            )
    episodes_dir = private_dir / "episodes"
    actual_episode_paths = {
        path.relative_to(private_dir).as_posix()
        for path in episodes_dir.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if actual_episode_paths != expected_episode_paths:
        raise ValueError(
            "private episode file set mismatch: "
            f"expected {sorted(expected_episode_paths)}, got {sorted(actual_episode_paths)}"
        )
    if any(path.is_symlink() for path in episodes_dir.rglob("*")):
        raise ValueError("private episode files must not be symlinks")

    expected_public_files = {f"challenge_{challenge_id}.json" for challenge_id in public_ids}
    actual_public_paths = list(public_dir.glob("challenge_*.json"))
    if any(path.is_symlink() for path in actual_public_paths):
        raise ValueError("public challenge files must not be symlinks")
    actual_public_files = {path.name for path in actual_public_paths}
    if actual_public_files != expected_public_files:
        raise ValueError(
            "public file set mismatch: "
            f"expected {sorted(expected_public_files)}, got {sorted(actual_public_files)}"
        )

    private_labeled_pairs = 0
    retained: list[tuple[str, dict[str, Any], str]] = []
    for row in rows:
        challenge_id = row["public_id"]
        if len(challenge_id) != 64 or any(ch not in "0123456789abcdef" for ch in challenge_id):
            raise ValueError(f"public challenge id is not an opaque SHA-256: {challenge_id!r}")
        episode_path = _private_path(private_dir, row.get("private_episode_path"))
        episode = _read_json(episode_path)
        if not isinstance(episode, dict):
            raise ValueError(f"private episode is not an object: {episode_path}")
        computed_id = public_id(episode)
        if computed_id != challenge_id:
            raise ValueError(
                f"private episode/public id mismatch: expected {challenge_id}, got {computed_id}"
            )
        mode = _episode_mode(episode)
        meta = episode.get("meta")
        if not isinstance(meta, dict):
            raise ValueError(f"private episode metadata is malformed for public id {challenge_id}")
        if meta.get("generator_sha256") != expected_generator["sha256"]:
            raise ValueError(
                f"episode generator source mismatch for public id {challenge_id}"
            )
        if meta.get("generator_version") != expected_generator["version"]:
            raise ValueError(
                f"episode generator version mismatch for public id {challenge_id}"
            )
        if row.get("branch_mode") != mode:
            raise ValueError(f"private branch_mode mismatch for public id {challenge_id}")
        if row.get("program_sha256") != program_hashes[mode]:
            raise ValueError(f"private program association mismatch for public id {challenge_id}")

        expected_public = public_bytes(episode)
        public_path = public_dir / f"challenge_{challenge_id}.json"
        try:
            actual_public = public_path.read_bytes()
        except FileNotFoundError as exc:
            raise ValueError(f"missing public challenge: {public_path}") from exc
        if actual_public != expected_public:
            raise ValueError(f"public bytes mismatch for public id {challenge_id}")
        if hashlib.sha256(actual_public).hexdigest() != row.get("public_sha256"):
            raise ValueError(f"public hash mismatch for public id {challenge_id}")

        for split in ("train", "test"):
            pairs = episode.get(split)
            if not isinstance(pairs, list) or not pairs:
                raise ValueError(f"private episode {challenge_id} has no {split} pairs")
            for pair in pairs:
                if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                    raise ValueError(
                        f"private episode {challenge_id} has malformed labeled {split} pair"
                    )
                private_labeled_pairs += 1
        retained.append((mode, episode, challenge_id))

    racket_rechecks = 0
    if rerun_racket:
        RacketBridge, wrap_rule = _racket_runtime()
        with RacketBridge(timeout=20, max_calls_before_restart=64) as bridge:
            for pair_index, pair in enumerate(_canonical_pairs()):
                actual = _execute_racket(
                    bridge,
                    wrap_rule,
                    program_sources[PARAMETER_SPEC["default"]],
                    pair["input"],
                )
                racket_rechecks += 1
                if actual != pair["output"]:
                    raise ValueError(
                        f"Racket canonical recheck failed at pair {pair_index}"
                    )
            for mode, episode, challenge_id in retained:
                for split in ("train", "test"):
                    for pair_index, pair in enumerate(episode[split]):
                        actual = _execute_racket(
                            bridge, wrap_rule, program_sources[mode], pair["input"]
                        )
                        racket_rechecks += 1
                        if actual != pair["output"]:
                            raise ValueError(
                                "Racket retained-label recheck failed for "
                                f"{challenge_id} {split}[{pair_index}]"
                            )

    return {
        "programs": len(programs),
        "episodes": len(rows),
        "public_files": len(actual_public_files),
        "private_labeled_pairs": private_labeled_pairs,
        "racket_rechecks": racket_rechecks,
    }


def _argument_parser():
    import argparse

    parser = argparse.ArgumentParser(
        description="Build or verify the task-local branch_mode Racket prototype evidence."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser(
        "build", help="execute exact Racket rules and write private/public evidence"
    )
    build.add_argument("--seeds", nargs="+", type=int, required=True)
    build.add_argument(
        "--difficulty", choices=("easy", "medium", "hard"), default="medium"
    )
    build.add_argument("--start-index", type=int, default=0)
    build.add_argument("--demos", type=int, default=5)
    build.add_argument("--queries", type=int, default=4)
    build.add_argument("--max-attempts", type=int, default=256)
    build.add_argument("--out", type=Path, required=True)

    verify = subparsers.add_parser(
        "verify", help="verify hashes/privacy and optionally rerun every Racket label"
    )
    verify.add_argument("--out", type=Path, required=True)
    verify.add_argument("--rerun-racket", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    if args.command == "build":
        evidence = build_evidence(
            seeds=args.seeds,
            difficulty=args.difficulty,
            start_index=args.start_index,
            n_train=args.demos,
            n_test=args.queries,
            max_attempts=args.max_attempts,
        )
        write_evidence(args.out, evidence)
        static_verification = verify_evidence(args.out)
        print(
            json.dumps(
                {
                    "output": str(args.out.resolve()),
                    "summary": evidence["summary"],
                    "static_verification": static_verification,
                },
                sort_keys=True,
            )
        )
        return 0
    if args.command == "verify":
        report = verify_evidence(args.out, rerun_racket=args.rerun_racket)
        print(json.dumps(report, sort_keys=True))
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
