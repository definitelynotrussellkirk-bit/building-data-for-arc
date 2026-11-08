#!/usr/bin/env python3
"""Proposed, unapproved episode-level label-offset variants.

The selected production generator and canonical Racket authority stay unchanged.
This task-local prototype keeps the row-label/column-label intersection rule but
chooses once per episode whether a row paints columns carrying the same palette
label (offset 0, canonical) or the next label in cyclic border order (offset 1).
All retained labels are executed by the included Racket bridge.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "dafb4f819b93"
VERSION = "proposed-label-offset-v1"
ALLOWED_LABEL_OFFSETS = (0, 1)
DEFAULT_LABEL_OFFSET = 0
CANONICAL_RULE_HASH = "6bb5aaacd2ec"
CANONICAL_SHA256 = "fd28f01b9690c2b68a529d5ecb88df555c53e93cc5254d1f6662017f1fdcf6cc"
CANONICAL_DECISION = (
    "(if (= 1 (length (unique common))) (first (unique common)) 0)"
)
OFFSET_ONE_DECISION = (
    "(let* ((palette (unique (map (lambda (rr) (at g rr (- w 1))) "
    "(range 0 h)))) "
    "(row-color (first row-colors)) "
    "(column-color (first col-colors)) "
    "(target-color (list-ref palette "
    "(modulo (+ 1 (index-of palette row-color)) (length palette))))) "
    "(if (= column-color target-color) row-color 0))"
)


def _sha256(value: str | bytes) -> str:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _grid_sha256(grid: Any) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    return seed


def _validate_counts(n_train: Any, n_test: Any) -> tuple[int, int]:
    if (
        type(n_train) is not int
        or type(n_test) is not int
        or not 1 <= n_train <= 16
        or not 1 <= n_test <= 16
        or n_train + n_test > 24
    ):
        raise ValueError(
            "demonstration/query count must be literal integers in 1..16 "
            "with total at most 24"
        )
    return n_train, n_test


def _validate_offset(label_offset: Any) -> int:
    if type(label_offset) is not int or label_offset not in ALLOWED_LABEL_OFFSETS:
        raise ValueError("label_offset must be the integer 0 or 1")
    return label_offset


def _check_canonical_source(source: Any) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(CANONICAL_DECISION) != 1:
        raise ValueError("canonical source must contain one guarded equality decision")
    if OFFSET_ONE_DECISION in source:
        raise ValueError("canonical source unexpectedly contains the proposed variant")
    return source


def canonical_source(*, root: str | Path | None = None) -> str:
    """Read the one exact canonical rule bound to this task."""
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if isinstance(source, str):
                    sources.add(source)
    if len(sources) != 1:
        raise ValueError(
            f"expected one distinct canonical source for {TASK_ID}, got {len(sources)}"
        )
    return _check_canonical_source(sources.pop())


def materialize_rule(
    label_offset: int = DEFAULT_LABEL_OFFSET,
    *,
    root: str | Path | None = None,
    source: str | None = None,
) -> str:
    """Return exact Racket for one declared setting; offset 0 is byte-identical."""
    offset = _validate_offset(label_offset)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if offset == DEFAULT_LABEL_OFFSET:
        return canonical
    return canonical.replace(CANONICAL_DECISION, OFFSET_ONE_DECISION, 1)


def rule_setting(source: Any, *, root: str | Path | None = None) -> int:
    if not isinstance(source, str):
        raise ValueError("variant source must be Racket text")
    canonical = canonical_source(root=root)
    if source == canonical:
        return 0
    if source == canonical.replace(CANONICAL_DECISION, OFFSET_ONE_DECISION, 1):
        return 1
    raise ValueError("source is not the pinned rule or declared label-offset variant")


def rule_callable(source: str, *, root: str | Path | None = None) -> str:
    """Extract the exact lambda from one verified ``(rule! ...)`` source."""
    rule_setting(source, root=root)
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise ValueError("source must be exactly one (rule! expression)")
    body = source[len(prefix) : -1]
    if not body.lstrip().startswith("(lambda (g)"):
        raise ValueError("pinned source must contain a lambda over g")
    return body


def execute_rule_many(
    source: str,
    grids: Any,
    *,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Execute one exact Racket rule over many inputs in one bridge request."""
    normalized = [normalize_grid(grid) for grid in grids]
    if not normalized:
        return []
    literals = [
        "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        for grid in normalized
    ]
    expression = (
        f"(map {rule_callable(source, root=root)} "
        + "'(" + " ".join(literals) + "))"
    )
    if bridge is None:
        with RacketBridge() as owned:
            result = owned.eval_text(expression)
    else:
        result = bridge.eval_text(expression)
    return [normalize_grid(grid) for grid in result]


def execute_rule(
    source: str,
    grid: Any,
    *,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> list[list[int]]:
    return execute_rule_many(source, [grid], bridge=bridge, root=root)[0]


def parameters_for_seed(seed: Any) -> dict[str, int]:
    """Choose exactly one hidden rule setting before any pair is sampled."""
    seed = _validate_seed(seed)
    return {"label_offset": random.Random(seed).choice(ALLOWED_LABEL_OFFSETS)}


def _draw_coordinates(seed: int, slot: int, attempt: int) -> tuple[int, int]:
    payload = f"{TASK_ID}:{VERSION}:{seed}:{slot}:{attempt}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    input_seed = int.from_bytes(digest[:8], "big")
    sample_index = int.from_bytes(digest[8:16], "big")
    return input_seed, sample_index


def _episode_input_rows(
    seed: Any,
    *,
    n_train: Any,
    n_test: Any,
    root: str | Path | None,
) -> list[dict[str, Any]]:
    seed = _validate_seed(seed)
    n_train, n_test = _validate_counts(n_train, n_test)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    generator, source_path, source_sha256 = load_selected_generator(
        TASK_ID, root=root_path
    )
    total = n_train + n_test
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    bands = ("easy", "medium", "hard")
    relations = ("matched", "different")
    for slot in range(total):
        n = 8 + (slot % 7)
        n_colors = 4 + (slot % 3)
        relation = relations[slot % len(relations)]
        band = bands[slot % len(bands)]
        for attempt in range(32):
            input_seed, sample_index = _draw_coordinates(seed, slot, attempt)
            grid = generator.generate(
                input_seed,
                sample_index,
                difficulty=band,
                grid_n=n,
                n_colors=n_colors,
                border_relation=relation,
            )
            errors = generator.self_check(grid)
            if errors:
                raise AssertionError("selected generator emitted invalid input: " + "; ".join(errors))
            normalized = normalize_grid(grid)
            key = _stable_json(normalized)
            if key in seen:
                continue
            seen.add(key)
            observed = generator.observe_overrides(normalized)
            if observed != {
                "grid_n": n,
                "n_colors": n_colors,
                "border_relation": relation,
            }:
                raise AssertionError(
                    f"selected generator provenance mismatch: expected {(n, n_colors, relation)}, "
                    f"observed {observed}"
                )
            rows.append(
                {
                    "input": normalized,
                    "slot": slot,
                    "difficulty": band,
                    "input_seed": input_seed,
                    "sample_index": sample_index,
                    "observed_axes": observed,
                    "selected_generator_path": str(source_path.relative_to(root_path)),
                    "selected_generator_sha256": source_sha256,
                }
            )
            break
        else:
            raise RuntimeError(f"could not draw a distinct lawful input for slot {slot}")
    return rows


def episode_inputs(
    seed: Any,
    *,
    n_train: Any = 3,
    n_test: Any = 4,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    return [
        copy.deepcopy(row["input"])
        for row in _episode_input_rows(
            seed,
            n_train=n_train,
            n_test=n_test,
            root=root,
        )
    ]


def distinguishing_input(*, root: str | Path | None = None) -> list[list[int]]:
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    pairs = canonical_pairs(TASK_ID, root=root_path, labeled_only=True)
    if not pairs:
        raise ValueError("no labeled canonical pair is available")
    return copy.deepcopy(pairs[0]["input"])


def _make_episode_with_bridge(
    seed: int,
    *,
    n_train: int,
    n_test: int,
    root: Path,
    bridge: RacketBridge,
) -> dict[str, Any]:
    parameters = parameters_for_seed(seed)
    selected = parameters["label_offset"]
    rows = _episode_input_rows(
        seed,
        n_train=n_train,
        n_test=n_test,
        root=root,
    )
    inputs = [row["input"] for row in rows]
    canonical = canonical_source(root=root)
    sources = {
        offset: materialize_rule(offset, source=canonical)
        for offset in ALLOWED_LABEL_OFFSETS
    }
    outputs_by_offset = {
        offset: execute_rule_many(
            source,
            inputs,
            bridge=bridge,
            root=root,
        )
        for offset, source in sources.items()
    }
    selected_outputs = outputs_by_offset[selected]
    pairs: list[dict[str, Any]] = []
    for index, (row, output) in enumerate(zip(rows, selected_outputs, strict=True)):
        role = "demonstration" if index < n_train else "query"
        pairs.append(
            {
                "input": copy.deepcopy(row["input"]),
                "output": copy.deepcopy(output),
                "role": role,
                "role_index": index if role == "demonstration" else index - n_train,
                "label_offset": selected,
                "input_sha256": _grid_sha256(row["input"]),
                "output_sha256": _grid_sha256(output),
                "input_provenance": {k: copy.deepcopy(v) for k, v in row.items() if k != "input"},
            }
        )

    rivals: list[dict[str, Any]] = []
    ambiguities: list[dict[str, Any]] = []
    for offset in ALLOWED_LABEL_OFFSETS:
        outputs = outputs_by_offset[offset]
        demo_mismatches = [
            index
            for index in range(n_train)
            if outputs[index] != selected_outputs[index]
        ]
        query_mismatches = [
            index
            for index in range(n_test)
            if outputs[n_train + index] != selected_outputs[n_train + index]
        ]
        if offset == selected:
            status = "selected_setting"
        elif demo_mismatches:
            status = "refuted_by_demonstrations"
        elif query_mismatches:
            status = "ambiguous_query"
        else:
            status = "answer_equivalent"
        rival = {
            "label_offset": offset,
            "racket_sha256": _sha256(sources[offset]),
            "status": status,
            "demonstration_mismatch_indices": demo_mismatches,
            "query_mismatch_indices": query_mismatches,
        }
        rivals.append(rival)
        if status == "ambiguous_query":
            ambiguities.append(copy.deepcopy(rival))

    source = sources[selected]
    prototype_path = Path(__file__).resolve()
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": parameters,
        "parameter_selection": (
            "one random.Random(seed).choice((0, 1)) draw before input sampling"
        ),
        "parameter": {
            "name": "label_offset",
            "allowed_values": list(ALLOWED_LABEL_OFFSETS),
            "original_default": DEFAULT_LABEL_OFFSET,
            "input_constraints_depend_on_parameter": False,
        },
        "invariant_reasoning": (
            "read the right-border row label and bottom-border column label, "
            "compare their positions in the shared ordered palette, preserve all "
            "nonzero border labels, and paint selected intersections with the row label"
        ),
        "prototype_sha256": _sha256(prototype_path.read_bytes()),
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "racket_source": source,
        "racket_sha256": _sha256(source),
        "racket_callable_sha256": _sha256(rule_callable(source, root=root)),
        "racket_path": f"private/rules/label-offset-{selected}.rkt",
        "n_train": n_train,
        "n_test": n_test,
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "parameter_rivals": rivals,
        "ambiguities": ambiguities,
        "racket_label_count": len(ALLOWED_LABEL_OFFSETS) * len(inputs),
    }


def make_episode(
    seed: Any,
    *,
    n_train: Any = 3,
    n_test: Any = 4,
    root: str | Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    seed = _validate_seed(seed)
    n_train, n_test = _validate_counts(n_train, n_test)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    if bridge is None:
        with RacketBridge(max_calls_before_restart=64) as owned:
            return _make_episode_with_bridge(
                seed,
                n_train=n_train,
                n_test=n_test,
                root=root_path,
                bridge=owned,
            )
    return _make_episode_with_bridge(
        seed,
        n_train=n_train,
        n_test=n_test,
        root=root_path,
        bridge=bridge,
    )


def public_challenge(episode: Any) -> dict[str, Any]:
    """Return only demonstration labels and query inputs, with no aliases."""
    if not isinstance(episode, dict):
        raise ValueError("episode must be a mapping")
    try:
        public = {
            "train": [
                {
                    "input": copy.deepcopy(pair["input"]),
                    "output": copy.deepcopy(pair["output"]),
                }
                for pair in episode["train"]
            ],
            "test": [
                {"input": copy.deepcopy(pair["input"])}
                for pair in episode["test"]
            ],
        }
    except (KeyError, TypeError) as exc:
        raise ValueError("episode does not contain valid train/test pairs") from exc
    public_challenge_bytes(public)
    return public


def public_filename(challenge: Any) -> str:
    return f"challenge-{public_challenge_id(challenge)}.json"


def _canonical_replay(
    *, root: Path, bridge: RacketBridge
) -> dict[str, Any]:
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    source = materialize_rule(0, root=root)
    outputs = execute_rule_many(
        source,
        [pair["input"] for pair in pairs],
        bridge=bridge,
        root=root,
    )
    rows = []
    for pair, actual in zip(pairs, outputs, strict=True):
        rows.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input_sha256": _grid_sha256(pair["input"]),
                "expected_sha256": _grid_sha256(pair["output"]),
                "actual_sha256": _grid_sha256(actual),
                "matched": actual == pair["output"],
            }
        )
    return {
        "label_offset": 0,
        "racket_sha256": _sha256(source),
        "pairs": rows,
        "passed": bool(rows) and all(row["matched"] for row in rows),
    }


def _manifest_rows(out: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted(out.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        relative = path.relative_to(out).as_posix()
        body = path.read_bytes()
        rows[relative] = {"bytes": len(body), "sha256": _sha256(body)}
    return rows


def _sorted_unique_episode_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: row["public_id"])
    ids = [row["public_id"] for row in ordered]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate visible public challenge")
    return ordered


def _materialize_with_bridge(
    out: Path,
    *,
    seeds: tuple[int, ...],
    n_train: int,
    n_test: int,
    root: Path,
    bridge: RacketBridge,
) -> dict[str, Any]:
    canonical = canonical_source(root=root)
    prototype_path = Path(__file__).resolve()
    for offset in ALLOWED_LABEL_OFFSETS:
        rule_path = out / f"private/rules/label-offset-{offset}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(materialize_rule(offset, source=canonical), encoding="utf-8")

    canonical_check = _canonical_replay(root=root, bridge=bridge)
    _write_json(out / "private/canonical-replay.json", canonical_check)
    if not canonical_check["passed"]:
        raise AssertionError("default label_offset=0 did not reproduce canonical labels")

    witness = distinguishing_input(root=root)
    witness_outputs = {
        str(offset): execute_rule(
            materialize_rule(offset, source=canonical),
            witness,
            bridge=bridge,
            root=root,
        )
        for offset in ALLOWED_LABEL_OFFSETS
    }
    if witness_outputs["0"] == witness_outputs["1"]:
        raise AssertionError("declared settings do not differ on the retained witness")
    _write_json(
        out / "private/distinguishing-witness.json",
        {
            "input": witness,
            "input_sha256": _grid_sha256(witness),
            "outputs": witness_outputs,
            "output_sha256": {
                key: _grid_sha256(value) for key, value in witness_outputs.items()
            },
        },
    )

    pending: list[tuple[dict[str, Any], dict[str, Any], str]] = []
    for seed in seeds:
        episode = make_episode(
            seed,
            n_train=n_train,
            n_test=n_test,
            root=root,
            bridge=bridge,
        )
        public = public_challenge(episode)
        public_id = public_challenge_id(public)
        pending.append((episode, public, public_id))
    if len({public_id for _, _, public_id in pending}) != len(pending):
        raise ValueError("duplicate visible public challenge")

    episode_rows: list[dict[str, Any]] = []
    for private_index, (episode, public, public_id) in enumerate(
        sorted(pending, key=lambda row: row[2])
    ):
        public_path = Path("public") / public_filename(public)
        private_path = Path("private") / f"episode-{private_index:03d}.json"
        episode["public_id"] = public_id
        episode["public_path"] = public_path.as_posix()
        episode["private_path"] = private_path.as_posix()
        _write_json(out / public_path, public)
        _write_json(out / private_path, episode)
        episode_rows.append(
            {
                "public_id": public_id,
                "public_path": public_path.as_posix(),
                "private_path": private_path.as_posix(),
                "parameters": copy.deepcopy(episode["parameters"]),
                "seed": episode["seed"],
                "racket_sha256": episode["racket_sha256"],
                "ambiguity_count": len(episode["ambiguities"]),
            }
        )
    episode_rows = _sorted_unique_episode_rows(episode_rows)
    ambiguous_count = sum(row["ambiguity_count"] for row in episode_rows)
    report = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "prototype_source": str(prototype_path.relative_to(root)),
        "prototype_source_sha256": _sha256(prototype_path.read_bytes()),
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "parameter": {
            "name": "label_offset",
            "allowed_values": list(ALLOWED_LABEL_OFFSETS),
            "original_default": DEFAULT_LABEL_OFFSET,
            "input_constraints_depend_on_parameter": False,
        },
        "invariant_reasoning": (
            "read row and column labels from the two borders, compare their "
            "ordered-palette positions, preserve the borders, and paint selected "
            "intersections with the row label"
        ),
        "episodes": episode_rows,
        "canonical_replay": "private/canonical-replay.json",
        "distinguishing_witness": "private/distinguishing-witness.json",
        "counts": {
            "episodes": len(episode_rows),
            "settings_exercised": len(
                {row["parameters"]["label_offset"] for row in episode_rows}
            ),
            "demonstrations": n_train * len(episode_rows),
            "queries": n_test * len(episode_rows),
            "canonical_pairs_checked": len(canonical_check["pairs"]),
            "ambiguous_parameter_rivals": ambiguous_count,
        },
        "limits": [
            "finite evidence covers only label_offset values 0 and 1 and the retained seeds",
            "rival checks distinguish only the declared parameter settings, not arbitrary programs",
            "this prototype does not alter production generation, approval, or training admission",
        ],
        "runtime": racket_runtime_status(),
    }
    _write_json(out / "report.json", report)
    manifest = {
        "schema": "arcpuzzles-proposed-parametric-manifest-v1",
        "task_id": TASK_ID,
        "status": "proposed_unapproved",
        "files": _manifest_rows(out),
    }
    _write_json(out / "manifest.json", manifest)
    return report


def materialize(
    out: str | Path,
    *,
    seeds: Any = (1, 0),
    n_train: Any = 3,
    n_test: Any = 4,
    root: str | Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    seeds = tuple(seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("provide at least one distinct episode seed")
    seeds = tuple(_validate_seed(seed) for seed in seeds)
    n_train, n_test = _validate_counts(n_train, n_test)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    out_path = Path(out)
    out_path.mkdir(parents=True, exist_ok=False)
    try:
        if bridge is None:
            with RacketBridge(max_calls_before_restart=64) as owned:
                return _materialize_with_bridge(
                    out_path,
                    seeds=seeds,
                    n_train=n_train,
                    n_test=n_test,
                    root=root_path,
                    bridge=owned,
                )
        return _materialize_with_bridge(
            out_path,
            seeds=seeds,
            n_train=n_train,
            n_test=n_test,
            root=root_path,
            bridge=bridge,
        )
    except Exception as exc:
        _write_json(
            out_path / "failure.json",
            {
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "seeds": list(seeds),
                "n_train": n_train,
                "n_test": n_test,
            },
        )
        raise


def _verify_tree_with_bridge(
    out: Path,
    *,
    root: Path,
    bridge: RacketBridge,
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "status": "fail",
            "errors": [f"cannot read report/manifest: {type(exc).__name__}: {exc}"],
        }

    current_source_sha = _sha256(Path(__file__).read_bytes())
    if report.get("prototype_source_sha256") != current_source_sha:
        errors.append("prototype source hash does not match the current prototype")
    if report.get("canonical_source_sha256") != CANONICAL_SHA256:
        errors.append("canonical source hash is not pinned to the declared authority")

    manifest_files = manifest.get("files")
    actual_manifest_files = _manifest_rows(out)
    if not isinstance(manifest_files, dict) or manifest_files != actual_manifest_files:
        saved_names = set(manifest_files) if isinstance(manifest_files, dict) else set()
        actual_names = set(actual_manifest_files)
        missing = sorted(saved_names - actual_names)
        unexpected = sorted(actual_names - saved_names)
        changed = sorted(
            name
            for name in saved_names & actual_names
            if manifest_files[name] != actual_manifest_files[name]
        )
        errors.append(
            "manifest inventory mismatch: "
            f"missing={missing}, unexpected={unexpected}, changed={changed}"
        )

    for offset in ALLOWED_LABEL_OFFSETS:
        relative = f"private/rules/label-offset-{offset}.rkt"
        path = out / relative
        expected = materialize_rule(offset, root=root)
        if not path.is_file() or path.read_text(encoding="utf-8") != expected:
            errors.append(f"rule snapshot mismatch: {relative}")

    witness_path = out / report.get(
        "distinguishing_witness", "private/distinguishing-witness.json"
    )
    try:
        saved_witness = json.loads(witness_path.read_text(encoding="utf-8"))
        witness_input = distinguishing_input(root=root)
        witness_outputs = {
            str(offset): execute_rule(
                materialize_rule(offset, root=root),
                witness_input,
                bridge=bridge,
                root=root,
            )
            for offset in ALLOWED_LABEL_OFFSETS
        }
        fresh_witness = {
            "input": witness_input,
            "input_sha256": _grid_sha256(witness_input),
            "outputs": witness_outputs,
            "output_sha256": {
                key: _grid_sha256(value) for key, value in witness_outputs.items()
            },
        }
        if saved_witness != fresh_witness or witness_outputs["0"] == witness_outputs["1"]:
            errors.append("distinguishing witness mismatch")
    except Exception as exc:
        errors.append(
            "distinguishing witness mismatch: "
            f"{type(exc).__name__}: {exc}"
        )

    selected_generator, selected_generator_path, selected_generator_sha256 = (
        load_selected_generator(TASK_ID, root=root)
    )
    selected_generator_relative = selected_generator_path.relative_to(root).as_posix()

    seen_public_ids: set[str] = set()
    settings_seen: set[int] = set()
    demonstrations_checked = 0
    queries_checked = 0
    ambiguity_count = 0
    for row in report.get("episodes", []):
        try:
            public_path = out / row["public_path"]
            private_path = out / row["private_path"]
            public = json.loads(public_path.read_text(encoding="utf-8"))
            private = json.loads(private_path.read_text(encoding="utf-8"))
            expected_public = public_challenge(private)
            public_id = public_challenge_id(public)
            if public != expected_public:
                errors.append(f"public/private projection mismatch: {row['public_path']}")
            if public_path.name != public_filename(public):
                errors.append(f"public filename mismatch: {row['public_path']}")
            if public_id != row.get("public_id") or public_id in seen_public_ids:
                errors.append(f"public id mismatch or duplicate: {row['public_path']}")
            seen_public_ids.add(public_id)
            offset = private["parameters"]["label_offset"]
            settings_seen.add(offset)
            demonstrations_checked += len(private["train"])
            queries_checked += len(private["test"])
            ambiguity_count += len(private.get("ambiguities", []))
            pairs = private["train"] + private["test"]
            if any(pair.get("label_offset") != offset for pair in pairs):
                errors.append(f"episode parameter is not fixed: {row['private_path']}")
            for pair_index, pair in enumerate(pairs):
                if pair.get("input_sha256") != _grid_sha256(pair.get("input")):
                    errors.append(
                        "input hash mismatch: "
                        f"{row['private_path']} pair {pair_index}"
                    )
                if pair.get("output_sha256") != _grid_sha256(pair.get("output")):
                    errors.append(
                        "output hash mismatch: "
                        f"{row['private_path']} pair {pair_index}"
                    )
                provenance = pair.get("input_provenance", {})
                if (
                    provenance.get("selected_generator_path")
                    != selected_generator_relative
                    or provenance.get("selected_generator_sha256")
                    != selected_generator_sha256
                ):
                    errors.append(
                        "selected generator binding mismatch: "
                        f"{row['private_path']} pair {pair_index}"
                    )
                    continue
                observed_axes = provenance.get("observed_axes")
                if not isinstance(observed_axes, dict):
                    errors.append(
                        "selected generator provenance missing observed axes: "
                        f"{row['private_path']} pair {pair_index}"
                    )
                    continue
                regenerated = selected_generator.generate(
                    provenance.get("input_seed"),
                    provenance.get("sample_index"),
                    difficulty=provenance.get("difficulty"),
                    **observed_axes,
                )
                if normalize_grid(regenerated) != normalize_grid(pair["input"]):
                    errors.append(
                        "selected generator replay mismatch: "
                        f"{row['private_path']} pair {pair_index}"
                    )
            inputs = [pair["input"] for pair in pairs]
            expected_outputs = execute_rule_many(
                materialize_rule(offset, root=root),
                inputs,
                bridge=bridge,
                root=root,
            )
            actual_outputs = [pair["output"] for pair in private["train"] + private["test"]]
            if expected_outputs != actual_outputs:
                errors.append(f"Racket labels mismatch: {row['private_path']}")
        except Exception as exc:
            errors.append(
                f"episode verification error for {row!r}: {type(exc).__name__}: {exc}"
            )

    canonical_check = _canonical_replay(root=root, bridge=bridge)
    if not canonical_check["passed"]:
        errors.append("fresh canonical replay failed")
    saved_canonical_path = out / report.get(
        "canonical_replay", "private/canonical-replay.json"
    )
    if saved_canonical_path.is_file():
        saved = json.loads(saved_canonical_path.read_text(encoding="utf-8"))
        if saved != canonical_check:
            errors.append("saved canonical replay differs from a fresh replay")
    else:
        errors.append("saved canonical replay is missing")

    expected_counts = {
        "episodes": len(report.get("episodes", [])),
        "settings_exercised": len(settings_seen),
        "demonstrations": demonstrations_checked,
        "queries": queries_checked,
        "canonical_pairs_checked": len(canonical_check["pairs"]),
        "ambiguous_parameter_rivals": ambiguity_count,
    }
    if report.get("counts") != expected_counts:
        errors.append(
            f"report counts mismatch: expected {expected_counts}, got {report.get('counts')}"
        )

    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "episodes_checked": len(report.get("episodes", [])),
        "manifest_files_checked": len(manifest_files) if isinstance(manifest_files, dict) else 0,
        "canonical_pairs_checked": len(canonical_check["pairs"]),
    }


def verify_tree(
    out: str | Path,
    *,
    root: str | Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    out_path = Path(out)
    if bridge is None:
        with RacketBridge(max_calls_before_restart=64) as owned:
            return _verify_tree_with_bridge(
                out_path, root=root_path, bridge=owned
            )
    return _verify_tree_with_bridge(out_path, root=root_path, bridge=bridge)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 0])
    parser.add_argument("--n-train", type=int, default=3)
    parser.add_argument("--n-test", type=int, default=4)
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="verify an existing --out tree instead of creating it",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    root = find_root(__file__)
    if args.verify_only:
        result = verify_tree(args.out, root=root)
    else:
        report = materialize(
            args.out,
            seeds=args.seeds,
            n_train=args.n_train,
            n_test=args.n_test,
            root=root,
        )
        result = {
            "materialized": report,
            "verification": verify_tree(args.out, root=root),
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    status = result.get("status") or result.get("verification", {}).get("status")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
