#!/usr/bin/env python3
"""Build bounded live-Racket evidence for the edge_policy prototype."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[4]
RUNTIME_ROOT = (
    REPO_ROOT
    if (REPO_ROOT / "RUNTIME_MANIFEST.json").is_file()
    else REPO_ROOT / "shared/runtime"
)
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_pairs,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
)

import prototype

EVIDENCE_SCHEMA = f"{prototype.TASK_ID}-edge-policy-evidence-v1"


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _seed_for_setting(setting: str, start_seed: int) -> int:
    for seed in range(start_seed, start_seed + 10_000):
        if prototype.choose_parameters(seed)[prototype.PARAMETER_NAME] == setting:
            return seed
    raise RuntimeError(f"no seed found for {setting!r}")


def _define_rules(bridge: RacketBridge, programs: dict[str, str]) -> dict[str, str]:
    symbols = {}
    for index, setting in enumerate(prototype.SETTINGS):
        symbol = f"__a762_edge_policy_{index}"
        bridge.eval_text(f"(define {symbol} {wrap_rule(programs[setting])})")
        symbols[setting] = symbol
    return symbols


def _execute_all(
    bridge: RacketBridge,
    symbols: dict[str, str],
    grid: list[list[int]],
    ordinal: int,
) -> dict[str, list[list[int]]]:
    grid_symbol = f"__a762_grid_{ordinal}"
    bridge.define_grid(grid_symbol, grid)
    return {
        setting: bridge.eval_text(f"({symbols[setting]} {grid_symbol})")
        for setting in prototype.SETTINGS
    }


def _episode_with_racket_labels(
    bridge: RacketBridge,
    symbols: dict[str, str],
    seed: int,
    setting: str,
    demo_count: int,
    query_count: int,
    ordinal_start: int,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    episode = prototype.build_episode(
        seed,
        edge_policy=setting,
        demo_count=demo_count,
        query_count=query_count,
    )
    observations = []
    labelled = {"train": [], "test": []}
    ordinal = ordinal_start
    for split in ("train", "test"):
        for pair_index, pair in enumerate(episode[split]):
            outputs = _execute_all(bridge, symbols, pair["input"], ordinal)
            ordinal += 1
            for candidate, output in outputs.items():
                expected = prototype.apply_python(pair["input"], candidate)
                if output != expected:
                    raise AssertionError(
                        f"Racket/Python mismatch: setting={candidate}, seed={seed}, "
                        f"{split}[{pair_index}]"
                    )
            labelled[split].append(
                {
                    "input": pair["input"],
                    "output": outputs[setting],
                    "sample_index": pair["sample_index"],
                }
            )
            observations.append(
                {
                    "split": split,
                    "pair_index": pair_index,
                    "sample_index": pair["sample_index"],
                    "outputs": outputs,
                }
            )

    private = dict(episode)
    private["train"] = labelled["train"]
    private["test"] = labelled["test"]
    private["label_executor"] = "protected-racket"

    survivors = prototype.surviving_settings(private["train"])
    if survivors != [setting]:
        raise AssertionError(f"Racket demos leave survivors {survivors}, expected {[setting]}")
    rivals = [candidate for candidate in prototype.SETTINGS if candidate != setting]
    demo_rows = [row for row in observations if row["split"] == "train"]
    query_rows = [row for row in observations if row["split"] == "test"]
    demo_disagreements = {
        rival: sum(row["outputs"][rival] != row["outputs"][setting] for row in demo_rows)
        for rival in rivals
    }
    if any(count != demo_count for count in demo_disagreements.values()):
        raise AssertionError(f"demos do not all distinguish settings: {demo_disagreements}")
    query_checks = []
    for row in query_rows:
        disagrees = [
            rival for rival in rivals
            if row["outputs"][rival] != row["outputs"][setting]
        ]
        if set(disagrees) != set(rivals):
            raise AssertionError(f"query did not distinguish every rival: {disagrees}")
        query_checks.append(
            {
                "pair_index": row["pair_index"],
                "sample_index": row["sample_index"],
                "disagrees_with": disagrees,
            }
        )
    return (
        private,
        {
            "setting": setting,
            "seed": seed,
            "difficulty": private["difficulty"],
            "public_identifier": prototype.public_identifier(private),
            "all_labels_executed_by_racket": True,
            "surviving_settings_from_demos": survivors,
            "demo_disagreement_counts": demo_disagreements,
            "queries": query_checks,
            "all_outputs": {
                f"{row['split']}:{row['pair_index']}": row["outputs"]
                for row in observations
            },
        },
        ordinal,
    )


def _manifest(root: Path) -> dict[str, Any]:
    files = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        relative = path.relative_to(root).as_posix()
        files[relative] = {
            "sha256": _sha256_file(path),
            "bytes": path.stat().st_size,
        }
    return {"schema": f"{EVIDENCE_SCHEMA}-manifest", "hash": "sha256", "files": files}


def build_evidence(
    out: Path | str,
    *,
    start_seed: int = 20261023,
    demo_count: int = prototype.DEFAULT_DEMO_COUNT,
    query_count: int = prototype.DEFAULT_QUERY_COUNT,
) -> dict[str, Any]:
    destination = Path(out).resolve()
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite existing evidence: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    root = Path(find_root(SCRIPT_PATH))
    parent, generator_path, generator_sha = load_selected_generator(
        prototype.TASK_ID, root=root
    )
    programs = {
        setting: prototype.racket_program(setting, root=root)
        for setting in prototype.SETTINGS
    }
    if programs[prototype.DEFAULT_SETTING] != prototype.canonical_program(root=root):
        raise AssertionError("default edge policy is not exact canonical Racket source")
    if len(set(programs.values())) != len(prototype.SETTINGS):
        raise AssertionError("edge-policy settings produced duplicate Racket programs")

    preflight = racket_runtime_status()
    if not preflight["available"]:
        raise RuntimeError(preflight["reason"])

    seeds = {
        setting: _seed_for_setting(setting, start_seed)
        for setting in prototype.SETTINGS
    }
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.tmp-", dir=destination.parent)
    )
    try:
        rules_dir = temporary / "private/rules"
        rules_dir.mkdir(parents=True)
        for setting, program in programs.items():
            (rules_dir / f"rule-{setting}.rkt").write_text(program + "\n", encoding="utf-8")

        public_payloads: dict[str, bytes] = {}
        episode_summaries = []
        same_input = None
        ordinal = 0
        canonical_checks = []
        with RacketBridge(
            timeout=20.0,
            startup_timeout=45.0,
            max_calls_before_restart=128,
        ) as bridge:
            symbols = _define_rules(bridge, programs)

            for pair_index, pair in enumerate(
                canonical_pairs(prototype.TASK_ID, root=root, labeled_only=True)
            ):
                outputs = _execute_all(bridge, symbols, pair["input"], ordinal)
                ordinal += 1
                actual = outputs[prototype.DEFAULT_SETTING]
                canonical_checks.append(
                    {
                        "variant": pair["variant"],
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                        "racket_matches_canonical_label": actual == pair["output"],
                        "racket_matches_selected_python_mirror": actual
                        == parent.rule_mirror(pair["input"]),
                    }
                )
            if not canonical_checks or not all(
                row["racket_matches_canonical_label"]
                and row["racket_matches_selected_python_mirror"]
                for row in canonical_checks
            ):
                raise AssertionError("canonical clip setting lost canonical parity")

            for setting in prototype.SETTINGS:
                private, execution, ordinal = _episode_with_racket_labels(
                    bridge,
                    symbols,
                    seeds[setting],
                    setting,
                    demo_count,
                    query_count,
                    ordinal,
                )
                private["racket_outputs_by_pair"] = execution.pop("all_outputs")
                private_name = f"episode-{setting}.json"
                _write_json(temporary / "private" / private_name, private)

                public_name = execution["public_identifier"]
                if public_name in public_payloads:
                    raise AssertionError(f"duplicate public challenge: {public_name}")
                public_payloads[public_name] = public_challenge_bytes(private)
                execution["private_path"] = f"private/{private_name}"
                execution["public_path"] = f"public/{public_name}"
                episode_summaries.append(execution)

                if same_input is None:
                    same_input = {
                        "source_episode_setting": setting,
                        "input": private["train"][0]["input"],
                        "outputs": private["racket_outputs_by_pair"]["train:0"],
                    }
            runtime_identity = bridge.runtime_identity

        for name, payload in public_payloads.items():
            path = temporary / "public" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

        if same_input is None or len(
            {_json_bytes(value) for value in same_input["outputs"].values()}
        ) != len(prototype.SETTINGS):
            raise AssertionError("same-input witness does not distinguish settings")
        _write_json(temporary / "private/same-input-disagreement.json", same_input)
        _write_json(temporary / "private/canonical-default-parity.json", canonical_checks)

        prototype_path = SCRIPT_PATH.with_name("prototype.py")
        test_path = REPO_ROOT / "generators" / prototype.TASK_ID / "tests/test_parametric_edge_policy.py"
        report = {
            "schema": EVIDENCE_SCHEMA,
            "status": "passed_bounded_prototype_evidence",
            "prototype_status": "proposed_unapproved",
            "task_id": prototype.TASK_ID,
            "prototype_version": prototype.PROTOTYPE_VERSION,
            "parameter_spec": prototype.PARAMETER_SPEC,
            "counts": {
                "demos_per_episode": demo_count,
                "queries_per_episode": query_count,
            },
            "start_seed": start_seed,
            "episodes": sorted(episode_summaries, key=lambda row: row["public_identifier"]),
            "programs": {
                setting: {
                    "path": f"private/rules/rule-{setting}.rkt",
                    "sha256": _sha256_bytes(program.encode("utf-8")),
                    "exact_canonical": setting == prototype.DEFAULT_SETTING,
                }
                for setting, program in programs.items()
            },
            "canonical_default_checks": "private/canonical-default-parity.json",
            "same_input_witness": "private/same-input-disagreement.json",
            "source": {
                "generator_path": generator_path.relative_to(REPO_ROOT).as_posix(),
                "generator_sha256": generator_sha,
                "prototype_path": prototype_path.relative_to(REPO_ROOT).as_posix(),
                "prototype_sha256": _sha256_file(prototype_path),
                "builder_path": SCRIPT_PATH.relative_to(REPO_ROOT).as_posix(),
                "builder_sha256": _sha256_file(SCRIPT_PATH),
                "test_path": test_path.relative_to(REPO_ROOT).as_posix(),
                "test_sha256": _sha256_file(test_path),
            },
            "racket_runtime": runtime_identity,
            "limitations": [
                "This is a task-local proposed prototype, not an approved production API.",
                "Evidence covers one deterministic eight-pair episode per setting.",
                "Prototype inputs deliberately use 8x8 lattices with odd-parity 2x2 terminal cells so every pair distinguishes edge policies.",
            ],
            "passed": True,
        }
        _write_json(temporary / "report.json", report)
        _write_json(temporary / "manifest.json", _manifest(temporary))
        temporary.rename(destination)
        return report
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--start-seed", type=int, default=20261023)
    parser.add_argument("--demo-count", type=int, default=prototype.DEFAULT_DEMO_COUNT)
    parser.add_argument("--query-count", type=int, default=prototype.DEFAULT_QUERY_COUNT)
    args = parser.parse_args()
    report = build_evidence(
        args.out_dir,
        start_seed=args.start_seed,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
