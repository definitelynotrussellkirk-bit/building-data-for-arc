#!/usr/bin/env python3
"""Adversarial auditor for the fallback-panel parametric prototype.

The auditor has two independent surfaces:

* ``audit_export`` checks that public IDs hash the exact public bytes, private
  settings/query answers stay private, exact rules and canonical replay receipts
  are present, and paired settings hold visible inputs fixed.
* ``audit_rule_matrix`` executes both exact Racket settings over a bounded input
  matrix and checks them against an independent Python semantics mirror.

It is intentionally task-local.  Passing it does not approve the proposed
``fallback_panel='right'`` rule or admit either export to training.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import cache
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, load_selected_generator, public_challenge_bytes

TASK_ID = "27080597d778"
ROOT = find_root(__file__)
PROTOTYPE_PATH = Path(__file__).with_name("prototype.py")
Grid = list[list[int]]


@cache
def _prototype():
    spec = importlib.util.spec_from_file_location(
        "parametric_fallback_panel_27080597d778_for_audit", PROTOTYPE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load prototype: {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc


def _inside(base: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ValueError(f"invalid evidence path: {relative!r}")
    base = base.resolve()
    target = (base / relative).resolve()
    try:
        target.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"evidence path escapes root: {relative!r}") from exc
    return target


def _check_grid(grid: Any, *, width: int, label: str) -> None:
    if not isinstance(grid, list) or not grid:
        raise ValueError(f"{label} must be a nonempty grid")
    for row_index, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != width:
            raise ValueError(f"{label} row {row_index} must have width {width}")
        for column_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError(
                    f"{label}[{row_index}][{column_index}] must be an exact integer color 0..9"
                )


def _branch(grid: Grid) -> str:
    overlap = sum(bool(row[c]) and bool(row[c + 5]) for row in grid for c in range(4))
    gap = sum(not row[c] and not row[c + 5] for row in grid for c in range(4))
    if overlap and gap:
        return "balanced" if overlap == gap else "mixed"
    return "overlap" if overlap else "gap" if gap else "complement"


def _episode_pairs(episode: dict[str, Any]) -> list[dict[str, Any]]:
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("private episode must contain train/test lists")
    return [*train, *test]


def audit_export(evidence_dir: Path | str, *, root: Path | str = ROOT) -> dict[str, Any]:
    """Validate one materialized evidence directory without trusting its manifest."""
    evidence_dir = Path(evidence_dir).resolve()
    root = Path(root)
    manifest_path = evidence_dir / "manifest.json"
    manifest = _read_json(manifest_path)
    if manifest.get("task_id") != TASK_ID:
        raise ValueError(f"manifest task_id is not {TASK_ID}")
    if manifest.get("canonical_default_unchanged") is not True:
        raise ValueError("manifest does not preserve the canonical default")

    generator_path = root / "generators" / TASK_ID / "generator.py"
    expected_generator_sha256 = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    if manifest.get("generator_sha256") != expected_generator_sha256:
        raise ValueError(
            "generator hash mismatch: "
            f"manifest={manifest.get('generator_sha256')!r}, current={expected_generator_sha256}"
        )
    expected_prototype_sha256 = hashlib.sha256(PROTOTYPE_PATH.read_bytes()).hexdigest()
    if manifest.get("prototype_sha256") != expected_prototype_sha256:
        raise ValueError(
            "prototype hash mismatch: "
            f"manifest={manifest.get('prototype_sha256')!r}, current={expected_prototype_sha256}"
        )

    prototype = _prototype()
    canonical = prototype.canonical_record(root=root)["program_solution"]
    exact_rules: dict[str, str] = {}
    for setting in prototype.PARAMETER_SPEC["values"]:
        rule_path = evidence_dir / "rules" / f"{setting}.rkt"
        try:
            rule = rule_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"missing exact rule {rule_path}: {exc}") from exc
        expected = prototype.program_for(setting, root=root)
        if rule != expected:
            raise ValueError(f"exact rule mismatch for fallback_panel={setting!r}")
        exact_rules[setting] = rule
    if exact_rules[prototype.PARAMETER_SPEC["default"]] != canonical:
        raise ValueError("canonical/default exact rule changed")
    expected_program_hashes = {
        setting: hashlib.sha256(program.encode("utf-8")).hexdigest()
        for setting, program in exact_rules.items()
    }
    if manifest.get("program_sha256") != expected_program_hashes:
        raise ValueError("program hash mismatch between manifest and exact rules")

    replay_path = evidence_dir / "private" / "canonical-replay.json"
    replay = _read_json(replay_path)
    if not isinstance(replay, list) or len(replay) != 9:
        raise ValueError("canonical replay must contain exactly nine labeled pairs")
    if not all(isinstance(row, dict) and row.get("passed") is True for row in replay):
        raise ValueError("canonical replay contains a failure")

    episodes_meta = manifest.get("episodes")
    if not isinstance(episodes_meta, list) or not episodes_meta:
        raise ValueError("manifest episodes must be a nonempty list")

    private_by_id: dict[str, dict[str, Any]] = {}
    public_by_id: dict[str, dict[str, Any]] = {}
    public_hashes: list[str] = []
    for row in episodes_meta:
        if not isinstance(row, dict):
            raise ValueError("manifest episode entry must be an object")
        identifier = row.get("public_id")
        if not isinstance(identifier, str) or len(identifier) != 64:
            raise ValueError(f"invalid public_id: {identifier!r}")
        public_path = _inside(evidence_dir, row.get("public_file"))
        private_path = _inside(evidence_dir, row.get("private_file"))
        if public_path.name != f"challenge-{identifier}.json":
            raise ValueError(f"public filename is not opaque/content-bound: {public_path.name}")
        try:
            payload = public_path.read_bytes()
        except OSError as exc:
            raise ValueError(f"missing public challenge {public_path}: {exc}") from exc
        observed_hash = hashlib.sha256(payload).hexdigest()
        if observed_hash != identifier or row.get("public_sha256") != identifier:
            raise ValueError(
                f"public hash mismatch for {public_path.name}: expected {identifier}, got {observed_hash}"
            )
        public = _read_json(public_path)
        if public_challenge_bytes(public) != payload:
            raise ValueError(f"public bytes are not canonical for {public_path.name}")
        if set(public) != {"train", "test"}:
            raise ValueError(f"public challenge {identifier} exposes unexpected top-level fields")
        if not isinstance(public["train"], list) or not isinstance(public["test"], list):
            raise ValueError(f"public challenge {identifier} has invalid train/test containers")
        for pair_index, pair in enumerate(public["train"]):
            if not isinstance(pair, dict) or set(pair) != {"input", "output"}:
                raise ValueError(f"public train pair {pair_index} has private/unexpected fields")
            _check_grid(pair["input"], width=9, label=f"public train {pair_index} input")
            _check_grid(pair["output"], width=4, label=f"public train {pair_index} output")
        for pair_index, pair in enumerate(public["test"]):
            if not isinstance(pair, dict) or set(pair) != {"input"}:
                raise ValueError(f"public test pair {pair_index} leaks an answer or metadata")
            _check_grid(pair["input"], width=9, label=f"public test {pair_index} input")

        private = _read_json(private_path)
        if prototype.public_challenge(private) != public:
            raise ValueError(f"private/public projection mismatch for {identifier}")
        for pair_index, pair in enumerate(_episode_pairs(private)):
            if not isinstance(pair, dict) or set(pair) != {"input", "output"}:
                raise ValueError(f"private pair {pair_index} is malformed")
            _check_grid(pair["input"], width=9, label=f"private pair {pair_index} input")
            _check_grid(pair["output"], width=4, label=f"private pair {pair_index} output")

        changed_private = deepcopy(private)
        changed_private.setdefault("meta", {})["audit_private_mutation"] = True
        for pair in changed_private["test"]:
            pair["output"] = [[9] * 4 for _ in pair["output"]]
        if prototype.public_id(changed_private) != identifier:
            raise ValueError(f"private metadata/query answers affect public ID {identifier}")

        changed_visible = deepcopy(private)
        old = changed_visible["train"][0]["input"][0][0]
        changed_visible["train"][0]["input"][0][0] = (old + 1) % 10
        if prototype.public_id(changed_visible) == identifier:
            raise ValueError(f"visible input mutation did not change public ID {identifier}")

        public_hashes.append(identifier)
        public_by_id[identifier] = public
        private_by_id[identifier] = private

    if len(set(public_hashes)) != len(public_hashes):
        raise ValueError("manifest contains duplicate public challenge IDs")
    if public_hashes != sorted(public_hashes):
        raise ValueError("manifest episodes are not sorted by public ID")

    setting_map = _read_json(evidence_dir / "private" / "setting-map.json")
    if not isinstance(setting_map, list) or len(setting_map) != len(private_by_id):
        raise ValueError("private setting map does not cover every public challenge exactly once")
    settings_by_id: dict[str, str] = {}
    for row in setting_map:
        if not isinstance(row, dict):
            raise ValueError("private setting-map row must be an object")
        identifier = row.get("public_id")
        setting = row.get("fallback_panel")
        if identifier not in private_by_id or setting not in prototype.PARAMETER_SPEC["values"]:
            raise ValueError(f"invalid private setting-map row: {row!r}")
        if identifier in settings_by_id:
            raise ValueError(f"duplicate setting-map public_id: {identifier}")
        settings_by_id[identifier] = setting
        private_setting = private_by_id[identifier]["meta"]["parameters"]["fallback_panel"]
        if private_setting != setting:
            raise ValueError(f"setting-map/private episode disagreement for {identifier}")

    ordered_settings = sorted(settings_by_id.values())
    paired_inputs_identical = False
    branch_relation_counts = {"same_on_complement": 0, "different_on_noncomplement": 0}
    if set(settings_by_id.values()) == set(prototype.PARAMETER_SPEC["values"]):
        by_setting = {setting: private_by_id[identifier] for identifier, setting in settings_by_id.items()}
        left_pairs = _episode_pairs(by_setting["left"])
        right_pairs = _episode_pairs(by_setting["right"])
        left_inputs = [pair["input"] for pair in left_pairs]
        right_inputs = [pair["input"] for pair in right_pairs]
        paired_inputs_identical = left_inputs == right_inputs
        if not paired_inputs_identical:
            raise ValueError("paired left/right episodes do not hold visible inputs and order fixed")
        if by_setting["left"]["meta"].get("input_seed") != by_setting["right"]["meta"].get(
            "input_seed"
        ):
            raise ValueError("paired left/right episodes do not share input_seed")
        for left_pair, right_pair in zip(left_pairs, right_pairs, strict=True):
            branch = _branch(left_pair["input"])
            same = left_pair["output"] == right_pair["output"]
            if branch == "complement":
                if not same:
                    raise ValueError("paired settings disagree on a complement input")
                branch_relation_counts["same_on_complement"] += 1
            else:
                if same:
                    raise ValueError(f"paired settings fail to distinguish {branch} input")
                branch_relation_counts["different_on_noncomplement"] += 1

    return {
        "schema": "27080597d778-parametric-export-audit-v1",
        "passed": True,
        "task_id": TASK_ID,
        "evidence_dir": str(evidence_dir),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "public_challenges_checked": len(public_hashes),
        "public_ids": public_hashes,
        "private_settings": ordered_settings,
        "paired_inputs_identical": paired_inputs_identical,
        "paired_branch_relations": branch_relation_counts,
        "canonical_pairs_replayed": len(replay),
        "program_sha256": {
            setting: hashlib.sha256(program.encode("utf-8")).hexdigest()
            for setting, program in exact_rules.items()
        },
        "checks": [
            "exact public bytes hash to opaque filename/ID",
            "public JSON has demos and query inputs only",
            "private metadata and query answers do not affect public IDs",
            "visible input mutation changes the public ID",
            "private/public projections, settings, exact rules, and canonical receipts agree",
            "paired settings hold visible inputs fixed and differ only on noncomplement fallback",
            "all serialized grid cells are exact integer colors 0..9",
        ],
    }


def _int_sequence(name: str, values: Iterable[int]) -> list[int]:
    values = list(values)
    if not values or any(type(value) is not int or value < 0 for value in values):
        raise ValueError(f"{name} must be a nonempty sequence of nonnegative integers")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} must not contain duplicates")
    return values


def audit_rule_matrix(
    *,
    root: Path | str = ROOT,
    input_seeds: Iterable[int] = (0, 1, 2),
    sample_indices: Iterable[int] = tuple(range(8)),
    difficulties: Iterable[str] = ("easy", "medium", "hard"),
) -> dict[str, Any]:
    """Execute both exact rules over a bounded deterministic generator matrix."""
    root = Path(root)
    input_seeds = _int_sequence("input_seeds", input_seeds)
    sample_indices = _int_sequence("sample_indices", sample_indices)
    difficulties = list(difficulties)
    if not difficulties or any(value not in ("easy", "medium", "hard") for value in difficulties):
        raise ValueError("difficulties must be a nonempty subset of easy/medium/hard")
    if len(set(difficulties)) != len(difficulties):
        raise ValueError("difficulties must not contain duplicates")

    prototype = _prototype()
    generator, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    programs = {
        setting: prototype.program_for(setting, root=root)
        for setting in prototype.PARAMETER_SPEC["values"]
    }
    canonical = prototype.canonical_record(root=root)["program_solution"]
    if programs[prototype.PARAMETER_SPEC["default"]] != canonical:
        raise ValueError("canonical/default program changed before matrix audit")

    branch_counts: dict[str, int] = {}
    distinguishing_noncomplements = 0
    rows: list[dict[str, Any]] = []
    with RacketBridge(max_calls_before_restart=256) as bridge:
        runtime = bridge.runtime_identity
        for difficulty in difficulties:
            for input_seed in input_seeds:
                for sample_index in sample_indices:
                    grid = generator.generate(input_seed, sample_index, difficulty=difficulty)
                    _check_grid(
                        grid,
                        width=9,
                        label=f"matrix {difficulty}/{input_seed}/{sample_index} input",
                    )
                    branch = _branch(grid)
                    branch_counts[branch] = branch_counts.get(branch, 0) + 1
                    outputs: dict[str, Grid] = {}
                    for setting, program in programs.items():
                        racket_output = prototype.execute(bridge, program, grid)
                        python_output = prototype.apply_python(grid, setting)
                        if racket_output != python_output:
                            raise ValueError(
                                "Racket/Python parity failure at "
                                f"difficulty={difficulty}, input_seed={input_seed}, "
                                f"sample_index={sample_index}, setting={setting}"
                            )
                        _check_grid(
                            racket_output,
                            width=4,
                            label=(
                                f"matrix {difficulty}/{input_seed}/{sample_index} "
                                f"{setting} output"
                            ),
                        )
                        outputs[setting] = racket_output
                    same = outputs["left"] == outputs["right"]
                    if branch == "complement":
                        if not same:
                            raise ValueError(
                                "settings disagree on successful complement overlay at "
                                f"{difficulty}/{input_seed}/{sample_index}"
                            )
                    else:
                        if not same:
                            distinguishing_noncomplements += 1
                    rows.append(
                        {
                            "difficulty": difficulty,
                            "input_seed": input_seed,
                            "sample_index": sample_index,
                            "branch": branch,
                            "input_sha256": hashlib.sha256(
                                json.dumps(grid, separators=(",", ":")).encode("utf-8")
                            ).hexdigest(),
                            "settings_differ": not same,
                        }
                    )

    return {
        "schema": "27080597d778-parametric-racket-matrix-audit-v1",
        "passed": True,
        "task_id": TASK_ID,
        "input_seeds": input_seeds,
        "sample_indices": sample_indices,
        "difficulties": difficulties,
        "inputs_checked": len(rows),
        "racket_evaluations": len(rows) * len(programs),
        "branch_counts": dict(sorted(branch_counts.items())),
        "distinguishing_noncomplements": distinguishing_noncomplements,
        "generator_version": generator.VERSION,
        "generator_path": str(Path(generator_path).relative_to(root)),
        "generator_sha256": generator_sha256,
        "program_sha256": {
            setting: hashlib.sha256(program.encode("utf-8")).hexdigest()
            for setting, program in programs.items()
        },
        "runtime": runtime,
        "rows": rows,
    }


def write_audit(
    *,
    evidence_dir: Path | str,
    out: Path | str,
    root: Path | str = ROOT,
    input_seeds: Iterable[int] = (0, 1, 2),
    sample_indices: Iterable[int] = tuple(range(8)),
    difficulties: Iterable[str] = ("easy", "medium", "hard"),
) -> dict[str, Any]:
    """Run both audit surfaces and write one compact source-bound report."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"audit output already exists: {out}")
    export = audit_export(evidence_dir, root=root)
    matrix = audit_rule_matrix(
        root=root,
        input_seeds=input_seeds,
        sample_indices=sample_indices,
        difficulties=difficulties,
    )
    report = {
        "schema": "27080597d778-parametric-adversarial-audit-v1",
        "passed": export["passed"] and matrix["passed"],
        "status": "bounded no-finding result; proposed rule remains unapproved",
        "export": export,
        "racket_matrix": matrix,
        "audit_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "limitations": [
            "bounded deterministic matrix, not an exhaustive input proof",
            "compares only the two declared fallback_panel settings",
            "does not approve production use or training admission",
        ],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--input-seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--sample-indices", type=int, nargs="+", default=list(range(8)))
    parser.add_argument(
        "--difficulties", nargs="+", choices=("easy", "medium", "hard"),
        default=["easy", "medium", "hard"],
    )
    args = parser.parse_args(argv)
    report = write_audit(
        evidence_dir=args.evidence,
        out=args.out,
        input_seeds=args.input_seeds,
        sample_indices=args.sample_indices,
        difficulties=args.difficulties,
    )
    print(json.dumps({
        "passed": report["passed"],
        "export_public_challenges": report["export"]["public_challenges_checked"],
        "matrix_inputs": report["racket_matrix"]["inputs_checked"],
        "matrix_racket_evaluations": report["racket_matrix"]["racket_evaluations"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
