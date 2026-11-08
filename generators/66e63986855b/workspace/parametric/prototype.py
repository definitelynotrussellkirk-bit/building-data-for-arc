#!/usr/bin/env python3
"""Proposed episode-wide rule parameters for ARC task 66e63986855b.

The approved production generator and canonical Racket authority stay unchanged.
This task-local prototype varies how far the row-front concavity is filled and
whether the source outline is cleared before painting the fill.
"""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from reviewer_support import canonical_path, find_root


TASK_ID = "66e63986855b"
PROTOTYPE_VERSION = "proposed-row-front-parameters-v1"
CANONICAL_SOURCE_SHA256 = (
    "e228483658ada007f41f36b034b9aab19ff06535e4fdec54757c831d386421b5"
)
CANONICAL_RULE_HASH = "e9ecd02cbe2e"
END_SITE = "(end (- (* 2 maxc) rc))"
CLEAR_SITE = "(cellmap g (r c v) 0)"

PARAMETER_SPECS = {
    "fill_extent": {
        "values": ("reflected", "to_axis"),
        "default": "reflected",
    },
    "source_policy": {
        "values": ("clear", "retain"),
        "default": "clear",
    },
}
SETTINGS = (
    {"fill_extent": "reflected", "source_policy": "clear"},
    {"fill_extent": "to_axis", "source_policy": "clear"},
    {"fill_extent": "reflected", "source_policy": "retain"},
    {"fill_extent": "to_axis", "source_policy": "retain"},
)

HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
RULE_DIR = HERE.parent / "rules"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _validate_seed(seed: int) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer (not bool) in 0..2**63-1")
    return seed


def _validate_parameter(name: str, value: str) -> str:
    values = PARAMETER_SPECS[name]["values"]
    if type(value) is not str or value not in values:
        raise ValueError(f"{name} must be one of {values}, got {value!r}")
    return value


def validate_parameters(parameters: dict[str, Any]) -> dict[str, str]:
    if not isinstance(parameters, dict) or set(parameters) != set(PARAMETER_SPECS):
        raise ValueError(
            "parameters must contain exactly fill_extent and source_policy"
        )
    return {
        name: _validate_parameter(name, parameters[name])
        for name in PARAMETER_SPECS
    }


def parameters_for_seed(seed: int) -> dict[str, str]:
    """Choose one of the four settings deterministically for the whole episode."""
    seed = _validate_seed(seed)
    return dict(SETTINGS[seed % len(SETTINGS)])


@lru_cache(maxsize=1)
def canonical_source() -> str:
    sources: set[str] = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    source = row.get("program_solution")
                    if not isinstance(source, str) or not source:
                        raise ValueError(f"canonical task {TASK_ID} has no Racket source")
                    sources.add(source)
    if len(sources) != 1:
        raise ValueError(
            f"expected exactly one canonical source for {TASK_ID}, found {len(sources)}"
        )
    source = sources.pop()
    if _sha256_text(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("canonical source SHA-256 does not match the pinned prototype")
    if source.count(END_SITE) != 1:
        raise ValueError("canonical source must contain exactly one fill-end site")
    if source.count(CLEAR_SITE) != 1:
        raise ValueError("canonical source must contain exactly one clear-grid site")
    return source


def materialize_rule(
    *, fill_extent: str = "reflected", source_policy: str = "clear"
) -> str:
    """Return the exact Racket program for one validated parameter setting."""
    fill_extent = _validate_parameter("fill_extent", fill_extent)
    source_policy = _validate_parameter("source_policy", source_policy)
    source = canonical_source()
    if fill_extent == "to_axis":
        source = source.replace(END_SITE, "(end maxc)", 1)
    if source_policy == "retain":
        source = source.replace(CLEAR_SITE, "g", 1)
    return source


def setting_key(parameters: dict[str, Any]) -> str:
    checked = validate_parameters(parameters)
    return f"{checked['fill_extent']}-{checked['source_policy']}"


def rule_path(parameters: dict[str, Any]) -> Path:
    return RULE_DIR / f"{setting_key(parameters)}.rkt"


def grid_sha256(grid: list[list[int]]) -> str:
    from reviewer_support import normalize_grid

    normalized = normalize_grid(grid)
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return _sha256_text(payload)


@lru_cache(maxsize=1)
def load_generator():
    """Load the selected source from this packet and return module/path/hash."""
    from reviewer_support import load_selected_generator

    return load_selected_generator(TASK_ID, root=ROOT)


def apply_python(grid: list[list[int]], parameters: dict[str, Any]) -> list[list[int]]:
    """Independent Python mirror for one prototype setting."""
    import copy

    from reviewer_support import normalize_grid

    checked = validate_parameters(parameters)
    normalized = normalize_grid(grid)
    generator, _, _ = load_generator()
    findings = generator.self_check(normalized)
    if findings:
        raise ValueError("input is outside the prototype manifold: " + "; ".join(findings))

    cells = [
        (row, column)
        for row, values in enumerate(normalized)
        for column, value in enumerate(values)
        if value != 0
    ]
    colors = {normalized[row][column] for row, column in cells}
    if len(colors) != 1:
        raise ValueError("prototype inputs require exactly one nonzero color")
    color = next(iter(colors))
    first_row = min(row for row, _ in cells)
    last_row = max(row for row, _ in cells)
    max_column = max(column for _, column in cells)

    if checked["source_policy"] == "retain":
        output = copy.deepcopy(normalized)
    else:
        output = [[0 for _ in row] for row in normalized]

    for row in range(first_row + 1, last_row):
        columns = [
            column
            for column, value in enumerate(normalized[row])
            if value != 0
        ]
        if not columns:
            continue
        frontier = max(columns)
        end = (
            2 * max_column - frontier
            if checked["fill_extent"] == "reflected"
            else max_column
        )
        for column in range(frontier + 1, end + 1):
            if 0 <= column < len(output[row]):
                output[row][column] = color
    return output


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    )
    return f"'({rows})"


def _racket_runtime():
    import sys
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
    from reviewer_support import normalize_grid

    normalized = normalize_grid(grid)
    expression = f"({wrap_rule(source)} {_grid_literal(normalized)})"
    return normalize_grid(bridge.eval_text(expression))


def apply_racket(
    grid: list[list[int]], parameters: dict[str, Any], *, bridge=None, wrap_rule=None
) -> list[list[int]]:
    """Execute the exact materialized rule in the pinned protected runtime."""
    checked = validate_parameters(parameters)
    source = materialize_rule(**checked)
    if bridge is not None:
        if wrap_rule is None:
            _, wrap_rule = _racket_runtime()
        return _execute_racket(bridge, wrap_rule, source, grid)
    RacketBridge, wrap = _racket_runtime()
    with RacketBridge(timeout=20, max_calls_before_restart=32) as owned:
        return _execute_racket(owned, wrap, source, grid)


def racket_python_parity(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Execute all four Racket settings once and compare an independent mirror."""
    RacketBridge, wrap_rule = _racket_runtime()
    records: list[dict[str, Any]] = []
    with RacketBridge(timeout=20, max_calls_before_restart=16) as bridge:
        for setting in SETTINGS:
            parameters = dict(setting)
            racket_output = apply_racket(
                grid, parameters, bridge=bridge, wrap_rule=wrap_rule
            )
            python_output = apply_python(grid, parameters)
            records.append(
                {
                    "parameters": parameters,
                    "matches": racket_output == python_output,
                    "output_sha256": grid_sha256(racket_output),
                    "python_output_sha256": grid_sha256(python_output),
                }
            )
    return records


def _validate_episode_args(
    *, difficulty: str, start_index: int, n_train: int, n_test: int, max_attempts: int
) -> None:
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")
    if type(start_index) is not int or start_index < 0:
        raise ValueError("start_index must be a nonnegative integer (not bool)")
    if type(n_train) is not int or n_train < 1:
        raise ValueError("n_train must be a positive integer (not bool)")
    if type(n_test) is not int or n_test < 1:
        raise ValueError("n_test must be a positive integer (not bool)")
    if type(max_attempts) is not int or max_attempts < n_train + n_test:
        raise ValueError("max_attempts must cover every requested pair")


def _episode_parameters(episode: dict[str, Any]) -> dict[str, str]:
    meta = episode.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("episode is missing metadata")
    return validate_parameters(meta.get("parameters"))


def query_identifiability_records(
    episode: dict[str, Any], *, predictor=apply_python
) -> list[dict[str, Any]]:
    """Check each query against all parameter rivals using demonstrations only."""
    chosen = _episode_parameters(episode)
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not train:
        raise ValueError("episode needs at least one demonstration")
    if not isinstance(test, list) or not test:
        raise ValueError("episode needs at least one query")

    records: list[dict[str, Any]] = []
    for query_index, query in enumerate(test):
        if not isinstance(query, dict) or "input" not in query:
            raise ValueError(f"query {query_index} is malformed")
        query_input = query["input"]
        chosen_query_output = predictor(query_input, chosen)
        rival_rows: list[dict[str, Any]] = []
        for rival_setting in SETTINGS:
            rival = dict(rival_setting)
            if rival == chosen:
                continue
            rival_query_output = predictor(query_input, rival)
            changes_query = rival_query_output != chosen_query_output
            refuting_demo_indices = []
            for demo_index, demo in enumerate(train):
                if not isinstance(demo, dict) or set(("input", "output")) - set(demo):
                    raise ValueError(f"demonstration {demo_index} is malformed")
                if predictor(demo["input"], rival) != demo["output"]:
                    refuting_demo_indices.append(demo_index)
            rival_rows.append(
                {
                    "parameters": rival,
                    "changes_query": changes_query,
                    "refuting_demo_indices": refuting_demo_indices,
                    "refuted_by_demonstrations": bool(refuting_demo_indices),
                }
            )
        relevant = [row for row in rival_rows if row["changes_query"]]
        records.append(
            {
                "query_index": query_index,
                "query_input_sha256": grid_sha256(query_input),
                "identifiable_from_demonstrations": all(
                    row["refuted_by_demonstrations"] for row in relevant
                ),
                "rivals": rival_rows,
            }
        )
    return records


def query_identifiability_findings(
    episode: dict[str, Any], *, predictor=apply_python
) -> list[str]:
    findings: list[str] = []
    for record in query_identifiability_records(episode, predictor=predictor):
        for rival in record["rivals"]:
            if rival["changes_query"] and not rival["refuted_by_demonstrations"]:
                findings.append(
                    "query "
                    f"{record['query_index']} is ambiguous with {setting_key(rival['parameters'])}"
                )
    return findings


def build_episode(
    *,
    seed: int,
    parameters: dict[str, Any] | None = None,
    difficulty: str = "medium",
    start_index: int = 0,
    n_train: int = 3,
    n_test: int = 4,
    max_attempts: int = 256,
    labeler=apply_python,
) -> dict[str, Any]:
    """Build one episode with a single fixed parameter setting."""
    seed = _validate_seed(seed)
    _validate_episode_args(
        difficulty=difficulty,
        start_index=start_index,
        n_train=n_train,
        n_test=n_test,
        max_attempts=max_attempts,
    )
    selected = (
        parameters_for_seed(seed)
        if parameters is None
        else validate_parameters(parameters)
    )
    generator, generator_path, generator_sha256 = load_generator()
    requested = n_train + n_test
    pairs: list[dict[str, Any]] = []
    seen_inputs: set[str] = set()
    sample_indices: list[int] = []
    for offset in range(max_attempts):
        sample_index = start_index + offset
        grid = generator.generate(seed, sample_index, difficulty=difficulty)
        digest = grid_sha256(grid)
        if digest in seen_inputs:
            continue
        seen_inputs.add(digest)
        sample_indices.append(sample_index)
        pairs.append(
            {
                "input": grid,
                "output": labeler(grid, selected),
                "input_sha256": digest,
            }
        )
        if len(pairs) == requested:
            break
    if len(pairs) != requested:
        raise RuntimeError(
            f"sampled only {len(pairs)} distinct inputs after {max_attempts} attempts; "
            f"requested {requested}"
        )

    episode = {
        "schema": "66e63986855b-parametric-episode-v1",
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "meta": {
            "task_id": TASK_ID,
            "prototype": True,
            "status": "proposed_unapproved",
            "parameters": selected,
            "parameter_scope": "chosen once per episode",
            "seed": seed,
            "difficulty": difficulty,
            "start_index": start_index,
            "sample_indices": sample_indices,
            "n_train": n_train,
            "n_test": n_test,
            "input_generator": {
                "path": str(generator_path.relative_to(ROOT)),
                "sha256": generator_sha256,
                "version": generator.VERSION,
            },
        },
    }
    episode["meta"]["query_identifiability"] = query_identifiability_records(
        episode, predictor=labeler
    )
    return episode


def public_challenge(episode: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Return only visible demonstrations and query inputs."""
    import copy

    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode must contain train and test lists")
    return copy.deepcopy(
        {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in train
            ],
            "test": [{"input": pair["input"]} for pair in test],
        }
    )


def _programs_from_retained_files() -> dict[str, str]:
    programs: dict[str, str] = {}
    for setting in SETTINGS:
        key = setting_key(setting)
        expected = materialize_rule(**setting)
        path = rule_path(setting)
        if not path.is_file():
            raise FileNotFoundError(f"missing retained rule source: {path}")
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            raise ValueError(f"retained rule source does not match materializer: {path}")
        programs[key] = actual
    return programs


def public_artifact_name(episode: dict[str, Any]) -> str:
    """Derive an opaque public filename from visible bytes only."""
    from reviewer_support import public_challenge_id

    return f"challenge_{public_challenge_id(public_challenge(episode))}.json"


def build_evidence(
    *,
    seeds: list[int],
    difficulty: str = "medium",
    start_index: int = 0,
    n_train: int = 3,
    n_test: int = 4,
) -> dict[str, Any]:
    """Build bounded Racket-backed evidence for every retained episode setting."""
    if not isinstance(seeds, list) or not seeds:
        raise ValueError("seeds must be a nonempty list")
    if len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be distinct")
    for seed in seeds:
        _validate_seed(seed)
    _validate_episode_args(
        difficulty=difficulty,
        start_index=start_index,
        n_train=n_train,
        n_test=n_test,
        max_attempts=max(256, n_train + n_test),
    )
    demonstrated_settings = {
        setting_key(parameters_for_seed(seed)) for seed in seeds
    }
    required_settings = {setting_key(setting) for setting in SETTINGS}
    if demonstrated_settings != required_settings:
        missing = sorted(required_settings - demonstrated_settings)
        extra = sorted(demonstrated_settings - required_settings)
        raise ValueError(
            f"seeds must demonstrate every setting exactly as a set; missing={missing}, extra={extra}"
        )

    from arc_repl.racket_bridge import racket_runtime_status
    from reviewer_support import canonical_pairs, canonical_path

    generator, generator_path, generator_sha256 = load_generator()
    programs = _programs_from_retained_files()
    default_key = setting_key(
        {name: spec["default"] for name, spec in PARAMETER_SPECS.items()}
    )
    default_program_byte_identical = programs[default_key] == canonical_source()

    canonical_checks: list[dict[str, Any]] = []
    episode_records: list[dict[str, Any]] = []
    all_input_hashes: set[str] = set()
    python_parity_passed = 0
    query_identifiable = 0
    query_checks = 0
    racket_evaluations = 0
    prediction_cache: dict[tuple[str, str], list[list[int]]] = {}

    RacketBridge, wrap_rule = _racket_runtime()
    with RacketBridge(timeout=20, max_calls_before_restart=128) as bridge:
        runtime_identity = bridge.runtime_identity

        def racket_predictor(
            grid: list[list[int]], parameters: dict[str, Any]
        ) -> list[list[int]]:
            nonlocal racket_evaluations
            checked = validate_parameters(parameters)
            key = (grid_sha256(grid), setting_key(checked))
            if key not in prediction_cache:
                prediction_cache[key] = _execute_racket(
                    bridge, wrap_rule, programs[key[1]], grid
                )
                racket_evaluations += 1
            return prediction_cache[key]

        for pair in canonical_pairs(
            TASK_ID, root=ROOT, labeled_only=True
        ):
            actual = _execute_racket(
                bridge, wrap_rule, programs[default_key], pair["input"]
            )
            racket_evaluations += 1
            canonical_checks.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "input_sha256": grid_sha256(pair["input"]),
                    "expected_output_sha256": grid_sha256(pair["output"]),
                    "actual_output_sha256": grid_sha256(actual),
                    "passed": actual == pair["output"],
                }
            )

        for seed in seeds:
            parameters = parameters_for_seed(seed)
            episode = build_episode(
                seed=seed,
                parameters=parameters,
                difficulty=difficulty,
                start_index=start_index,
                n_train=n_train,
                n_test=n_test,
                labeler=racket_predictor,
            )
            pairs = [*episode["train"], *episode["test"]]
            pair_checks: list[dict[str, Any]] = []
            for pair_index, pair in enumerate(pairs):
                python_output = apply_python(pair["input"], parameters)
                parity = python_output == pair["output"]
                python_parity_passed += int(parity)
                all_input_hashes.add(pair["input_sha256"])
                pair_checks.append(
                    {
                        "pair_index": pair_index,
                        "input_sha256": pair["input_sha256"],
                        "racket_output_sha256": grid_sha256(pair["output"]),
                        "python_output_sha256": grid_sha256(python_output),
                        "python_parity": parity,
                    }
                )

            # Recompute from Racket-backed predictions so the private evidence
            # does not rely on query labels or a Python-only rival check.
            records = query_identifiability_records(
                episode, predictor=racket_predictor
            )
            episode["meta"]["query_identifiability"] = records
            findings = query_identifiability_findings(
                episode, predictor=racket_predictor
            )
            query_checks += len(records)
            query_identifiable += sum(
                record["identifiable_from_demonstrations"] for record in records
            )

            filename = public_artifact_name(episode)
            episode_records.append(
                {
                    "seed": seed,
                    "parameters": parameters,
                    "episode": episode,
                    "pair_checks": pair_checks,
                    "query_identifiability_findings": findings,
                    "public_id": filename.removeprefix("challenge_").removesuffix(".json"),
                    "public_filename": filename,
                }
            )

        witness_grid = episode_records[0]["episode"]["train"][0]["input"]
        witness_outputs = {
            setting_key(setting): racket_predictor(witness_grid, dict(setting))
            for setting in SETTINGS
        }

    output_hashes = {
        key: grid_sha256(output) for key, output in witness_outputs.items()
    }
    witness = {
        "input": witness_grid,
        "input_sha256": grid_sha256(witness_grid),
        "outputs": witness_outputs,
        "output_sha256": output_hashes,
        "distinct_output_count": len(set(output_hashes.values())),
    }
    total_pairs = len(seeds) * (n_train + n_test)
    counts = {
        "settings_materialized": len(programs),
        "episodes": len(episode_records),
        "distinct_settings_demonstrated": len(demonstrated_settings),
        "canonical_pairs": len(canonical_checks),
        "canonical_passed": sum(row["passed"] for row in canonical_checks),
        "train_pairs": len(seeds) * n_train,
        "query_pairs": len(seeds) * n_test,
        "distinct_inputs": len(all_input_hashes),
        "python_parity_passed": python_parity_passed,
        "query_checks": query_checks,
        "query_identifiable": query_identifiable,
        "racket_evaluations": racket_evaluations,
    }
    public_names = [record["public_filename"] for record in episode_records]
    all_findings = [
        finding
        for record in episode_records
        for finding in record["query_identifiability_findings"]
    ]
    passed = bool(
        default_program_byte_identical
        and runtime_identity.get("protected") is True
        and counts["settings_materialized"] == len(SETTINGS)
        and counts["distinct_settings_demonstrated"] == len(SETTINGS)
        and counts["canonical_pairs"] > 0
        and counts["canonical_passed"] == counts["canonical_pairs"]
        and counts["python_parity_passed"] == total_pairs
        and counts["query_identifiable"] == counts["query_checks"]
        and counts["distinct_inputs"] == total_pairs
        and witness["distinct_output_count"] == len(SETTINGS)
        and len(set(public_names)) == len(public_names)
        and not all_findings
    )

    test_path = ROOT / "generators" / TASK_ID / "tests" / "test_parametric_row_front.py"
    ledger_path = canonical_path(ROOT)
    report = {
        "schema": "66e63986855b-parametric-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "passed": passed,
        "completion_state": "complete" if passed else "blocked",
        "canonical_authority_changed": False,
        "default_program_byte_identical": default_program_byte_identical,
        "parameter_contract": {
            "parameters": PARAMETER_SPECS,
            "settings": [dict(setting) for setting in SETTINGS],
            "scope": "chosen once per episode",
            "input_constraints_depend_on_parameters": False,
            "input_constraints": [
                "the selected generator's one-color contiguous row-front manifold",
                "endpoint rows reach the global rightmost source column",
                "all reflected endpoints fit inside the canvas",
            ],
            "invariant_reasoning": [
                "locate the occupied row span and global rightmost source column",
                "read each interior row's rightmost occupied frontier",
                "paint a right-side fill interval in the source color",
            ],
            "parameter_effects": {
                "fill_extent": {
                    "reflected": "end at the frontier reflected across the global rightmost column",
                    "to_axis": "end at the global rightmost column",
                },
                "source_policy": {
                    "clear": "start from a blank canvas (canonical)",
                    "retain": "start from a copy of the source outline",
                },
            },
        },
        "replay": {
            "seeds": seeds,
            "difficulty": difficulty,
            "start_index": start_index,
            "n_train": n_train,
            "n_test": n_test,
        },
        "programs": {
            key: {
                "path": str(
                    rule_path(
                        next(
                            setting for setting in SETTINGS
                            if setting_key(setting) == key
                        )
                    ).relative_to(ROOT)
                ),
                "sha256": _sha256_text(source),
                "text": source,
            }
            for key, source in programs.items()
        },
        "sources": {
            "prototype": {
                "path": str(HERE.relative_to(ROOT)),
                "sha256": _sha256_bytes(HERE.read_bytes()),
            },
            "tests": {
                "path": str(test_path.relative_to(ROOT)),
                "sha256": _sha256_bytes(test_path.read_bytes()),
            },
            "selected_generator": {
                "path": str(generator_path.relative_to(ROOT)),
                "sha256": generator_sha256,
                "version": generator.VERSION,
                "rule_hash": generator.RULE_HASH,
            },
            "canonical_ledger": {
                "path": str(ledger_path.relative_to(ROOT)),
                "sha256": _sha256_bytes(ledger_path.read_bytes()),
            },
        },
        "runtime": {
            "status": racket_runtime_status(),
            "identity": runtime_identity,
        },
        "canonical_checks": canonical_checks,
        "episodes": episode_records,
        "setting_difference_witness": witness,
        "counts": counts,
        "limitations": [
            "This is a task-local proposed prototype, not a production parametric API, approval, or training admission.",
            "Evidence covers only the retained seeds, selected-generator inputs, four declared settings, and declared parameter rivals.",
            "The retain setting makes the source outline visible in the answer; demonstrations must teach this composition explicitly.",
            "The to_axis setting is the existing simple axis-fill rival promoted to an explicit episode-wide rule setting; no claim is made about every possible extent rule.",
        ],
    }
    return report


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_evidence(
    *,
    out_dir: Path,
    public_dir: Path,
    report: dict[str, Any] | None = None,
    seeds: list[int] | None = None,
    difficulty: str = "medium",
    start_index: int = 0,
    n_train: int = 3,
    n_test: int = 4,
) -> dict[str, Any]:
    """Install sorted, deduplicated private/public evidence without overwrites."""
    import os
    import shutil
    import tempfile

    from reviewer_support import public_challenge_bytes, public_challenge_id

    out_dir = Path(out_dir).resolve()
    public_dir = Path(public_dir).resolve()
    if out_dir.exists():
        raise FileExistsError(f"refusing to overwrite evidence directory: {out_dir}")
    if public_dir.exists():
        raise FileExistsError(f"refusing to overwrite public directory: {public_dir}")
    if report is None:
        report = build_evidence(
            seeds=[0, 1, 2, 3] if seeds is None else seeds,
            difficulty=difficulty,
            start_index=start_index,
            n_train=n_train,
            n_test=n_test,
        )
    if report.get("schema") != "66e63986855b-parametric-evidence-v1":
        raise ValueError("unexpected evidence report schema")

    out_dir.parent.mkdir(parents=True, exist_ok=True)
    public_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_out = Path(
        tempfile.mkdtemp(prefix=f".{out_dir.name}.tmp-", dir=out_dir.parent)
    )
    temp_public = Path(
        tempfile.mkdtemp(prefix=f".{public_dir.name}.tmp-", dir=public_dir.parent)
    )
    installed_out = False
    try:
        _write_json(temp_out / "report.json", report)
        _write_json(
            temp_out / "setting-difference-witness.json",
            report["setting_difference_witness"],
        )
        _write_json(temp_out / "canonical-checks.json", report["canonical_checks"])

        program_dir = temp_out / "private" / "rules"
        for key, row in report["programs"].items():
            path = program_dir / f"{key}.rkt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(row["text"], encoding="utf-8")
            if _sha256_bytes(path.read_bytes()) != row["sha256"]:
                raise AssertionError(f"written rule hash mismatch for {key}")

        exports: list[tuple[str, str, bytes, dict[str, Any]]] = []
        seen_public: dict[str, bytes] = {}
        for record in report["episodes"]:
            challenge = public_challenge(record["episode"])
            public_id = public_challenge_id(challenge)
            filename = f"challenge_{public_id}.json"
            if filename != record["public_filename"] or public_id != record["public_id"]:
                raise AssertionError("public identifier is not derived from visible bytes")
            payload = public_challenge_bytes(challenge)
            if public_id in seen_public:
                if seen_public[public_id] == payload:
                    raise ValueError(f"duplicate visible public payload: {public_id}")
                raise ValueError(f"public identifier collision: {public_id}")
            seen_public[public_id] = payload
            exports.append((public_id, filename, payload, record))
        exports.sort(key=lambda row: row[0])

        setting_map: list[dict[str, Any]] = []
        for ordinal, (public_id, filename, payload, record) in enumerate(exports):
            private_path = temp_out / "private" / "episodes" / f"episode-{ordinal:03d}.json"
            _write_json(private_path, record)
            public_path = temp_public / filename
            public_path.write_bytes(payload)
            setting_map.append(
                {
                    "public_id": public_id,
                    "public_filename": filename,
                    "private_episode": str(private_path.relative_to(temp_out)),
                    "seed": record["seed"],
                    "parameters": record["parameters"],
                }
            )
        _write_json(temp_out / "private" / "setting-map.json", setting_map)

        files = {
            str(path.relative_to(temp_out)): _sha256_bytes(path.read_bytes())
            for path in sorted(temp_out.rglob("*"))
            if path.is_file() and path.name != "manifest.json"
        }
        public_files = {
            str(path.relative_to(temp_public)): _sha256_bytes(path.read_bytes())
            for path in sorted(temp_public.rglob("*"))
            if path.is_file()
        }
        manifest = {
            "schema": "66e63986855b-parametric-evidence-manifest-v1",
            "task_id": TASK_ID,
            "status": report["status"],
            "passed": report["passed"],
            "report_sha256": files["report.json"],
            "files": files,
            "public_files": public_files,
        }
        _write_json(temp_out / "manifest.json", manifest)
        os.replace(temp_out, out_dir)
        installed_out = True
        os.replace(temp_public, public_dir)
        return manifest
    except BaseException:
        if installed_out:
            shutil.rmtree(out_dir, ignore_errors=True)
        shutil.rmtree(temp_out, ignore_errors=True)
        shutil.rmtree(temp_public, ignore_errors=True)
        raise


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--public-dir", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3])
    parser.add_argument(
        "--difficulty", choices=("easy", "medium", "hard"), default="medium"
    )
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--n-train", type=int, default=3)
    parser.add_argument("--n-test", type=int, default=4)
    args = parser.parse_args()

    report = build_evidence(
        seeds=args.seeds,
        difficulty=args.difficulty,
        start_index=args.start_index,
        n_train=args.n_train,
        n_test=args.n_test,
    )
    manifest = write_evidence(
        out_dir=args.out_dir,
        public_dir=args.public_dir,
        report=report,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "completion_state": report["completion_state"],
                "passed": report["passed"],
                "counts": report["counts"],
                "manifest_sha256": _sha256_text(
                    json.dumps(manifest, sort_keys=True, separators=(",", ":"))
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
