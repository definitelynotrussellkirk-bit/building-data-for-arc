#!/usr/bin/env python3
"""Build bounded, Racket-backed evidence for the connection_axes prototype.

This file is intentionally isolated from the approved generator.  It executes
all retained labels with the packet's protected Racket bridge, compares them to
an independent Python mirror, and writes public challenges without hidden rule
metadata or query labels.
"""
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
SOURCE_RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
RUNTIME_ROOT = (
    REPO_ROOT
    if (REPO_ROOT / "RUNTIME_MANIFEST.json").is_file()
    else SOURCE_RUNTIME_ROOT
)
if not (RUNTIME_ROOT / "puzzle_generators").is_dir():
    raise ImportError(f"cannot locate packet runtime under {REPO_ROOT}")
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
)

import prototype


EVIDENCE_SCHEMA = f"{prototype.TASK_ID}-connection-axes-evidence-v1"


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")


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


def _seed_for_each_setting(start_seed: int) -> dict[str, int]:
    if type(start_seed) is not int:
        raise TypeError("start_seed must be an integer")
    if start_seed < 0:
        raise ValueError("start_seed must be nonnegative")
    # Move forward to a complete setting block so all compared episodes share
    # one difficulty instead of coupling a rule setting to a difficulty tier.
    aligned_start = start_seed + (-start_seed % len(prototype.SETTINGS))
    selected = {
        prototype.choose_setting(seed): seed
        for seed in range(aligned_start, aligned_start + len(prototype.SETTINGS))
    }
    if set(selected) != set(prototype.SETTINGS):
        raise RuntimeError("aligned seed block did not cover all settings")
    difficulties = {prototype.episode_difficulty(seed) for seed in selected.values()}
    if len(difficulties) != 1:
        raise RuntimeError("aligned setting block did not preserve one difficulty")
    return selected


def _define_rules(bridge: RacketBridge, programs: dict[str, str]) -> dict[str, str]:
    symbols: dict[str, str] = {}
    for setting in prototype.SETTINGS:
        symbol = f"__connection_axes_{setting}"
        bridge.eval_text(f"(define {symbol} {wrap_rule(programs[setting])})")
        symbols[setting] = symbol
    return symbols


def _execute_all(
    bridge: RacketBridge,
    symbols: dict[str, str],
    grid: list[list[int]],
    ordinal: int,
) -> dict[str, list[list[int]]]:
    grid_symbol = f"__evidence_grid_{ordinal}"
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
        connection_axes=setting,
        demo_count=demo_count,
        query_count=query_count,
    )
    selected_pairs: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    ordinal = ordinal_start

    for split in ("train", "test"):
        for pair_index, pair in enumerate(episode[split]):
            outputs = _execute_all(bridge, symbols, pair["input"], ordinal)
            ordinal += 1
            for candidate_setting, output in outputs.items():
                python_output = prototype.apply_python(pair["input"], candidate_setting)
                if output != python_output:
                    raise AssertionError(
                        f"Racket/Python mismatch for {candidate_setting}, "
                        f"seed={seed}, {split}[{pair_index}]"
                    )
            if outputs[setting] != pair["output"]:
                raise AssertionError(
                    f"selected Racket label differs from episode mirror for "
                    f"seed={seed}, {split}[{pair_index}]"
                )
            observations.append(
                {
                    "split": split,
                    "pair_index": pair_index,
                    "sample_index": pair["sample_index"],
                    "outputs": outputs,
                }
            )
            selected_pairs.append(
                {
                    "input": pair["input"],
                    "output": outputs[setting],
                    "sample_index": pair["sample_index"],
                }
            )

    private_episode = dict(episode)
    private_episode["train"] = selected_pairs[:demo_count]
    private_episode["test"] = selected_pairs[demo_count:]
    private_episode["label_executor"] = "protected-racket"

    survivors = prototype.surviving_settings(private_episode["train"])
    if survivors != [setting]:
        raise AssertionError(
            f"Racket demonstrations do not uniquely identify {setting}: {survivors}"
        )

    demo_observations = observations[:demo_count]
    query_observations = observations[demo_count:]
    rivals = [candidate for candidate in prototype.SETTINGS if candidate != setting]
    demo_disagreement_counts = {
        rival: sum(
            observation["outputs"][rival] != observation["outputs"][setting]
            for observation in demo_observations
        )
        for rival in rivals
    }
    if any(count != demo_count for count in demo_disagreement_counts.values()):
        raise AssertionError(
            f"not every demonstration distinguishes {setting}: "
            f"{demo_disagreement_counts}"
        )

    query_rows = []
    for observation in query_observations:
        disagrees_with = [
            rival
            for rival in rivals
            if observation["outputs"][rival] != observation["outputs"][setting]
        ]
        if set(disagrees_with) != set(rivals):
            raise AssertionError(
                f"query does not distinguish every rival for {setting}: "
                f"{disagrees_with}"
            )
        query_rows.append(
            {
                "pair_index": observation["pair_index"],
                "sample_index": observation["sample_index"],
                "disagrees_with": disagrees_with,
            }
        )

    summary = {
        "setting": setting,
        "seed": seed,
        "difficulty": private_episode["difficulty"],
        "public_identifier": prototype.public_identifier(private_episode),
        "all_labels_executed_by_racket": True,
        "surviving_settings": survivors,
        "demo_disagreement_counts": demo_disagreement_counts,
        "queries": query_rows,
    }
    all_outputs = {
        f"{observation['split']}:{observation['pair_index']}": observation["outputs"]
        for observation in observations
    }
    return private_episode, {"summary": summary, "all_outputs": all_outputs}, ordinal


def _manifest(root: Path) -> dict[str, Any]:
    files: dict[str, Any] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        relative = path.relative_to(root).as_posix()
        files[relative] = {
            "sha256": _sha256_file(path),
            "bytes": path.stat().st_size,
        }
    return {
        "schema": f"{EVIDENCE_SCHEMA}-manifest",
        "hash": "sha256",
        "files": files,
    }


def build_evidence(
    out: Path | str,
    *,
    start_seed: int = 20261023,
    demo_count: int = prototype.DEFAULT_DEMO_COUNT,
    query_count: int = prototype.DEFAULT_QUERY_COUNT,
) -> dict[str, Any]:
    """Build one bounded evidence directory without overwriting prior output."""
    destination = Path(out).resolve()
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite existing evidence: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    seeds = _seed_for_each_setting(start_seed)
    programs = {
        setting: prototype.racket_program(setting, root=find_root(SCRIPT_PATH))
        for setting in prototype.SETTINGS
    }
    if programs[prototype.DEFAULT_SETTING] != prototype.canonical_program(
        root=find_root(SCRIPT_PATH)
    ):
        raise AssertionError("default prototype program is not exact canonical source")
    if len(set(programs.values())) != len(prototype.SETTINGS):
        raise AssertionError("axis settings do not produce distinct rule sources")

    parent, generator_path, generator_sha256 = load_selected_generator(
        prototype.TASK_ID,
        root=find_root(SCRIPT_PATH),
    )
    del parent
    runtime_preflight = racket_runtime_status()
    if not runtime_preflight["available"]:
        raise RuntimeError(runtime_preflight["reason"])

    temporary = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.tmp-", dir=destination.parent)
    )
    try:
        rules_dir = temporary / "private" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        for setting, program in programs.items():
            (rules_dir / f"rule-{setting}.rkt").write_text(program, encoding="utf-8")

        episode_summaries: list[dict[str, Any]] = []
        public_identifiers: set[str] = set()
        public_payloads: dict[str, bytes] = {}
        same_input: dict[str, Any] | None = None
        ordinal = 0
        with RacketBridge(
            timeout=20.0,
            startup_timeout=45.0,
            max_calls_before_restart=120,
        ) as bridge:
            symbols = _define_rules(bridge, programs)
            for setting in prototype.SETTINGS:
                private_episode, execution, ordinal = _episode_with_racket_labels(
                    bridge,
                    symbols,
                    seeds[setting],
                    setting,
                    demo_count,
                    query_count,
                    ordinal,
                )
                summary = execution["summary"]
                episode_summaries.append(summary)

                private_payload = dict(private_episode)
                private_payload["racket_outputs_by_pair"] = execution["all_outputs"]
                _write_json(
                    temporary / "private" / f"episode-{setting}.json",
                    private_payload,
                )

                public_name = summary["public_identifier"]
                if public_name in public_identifiers:
                    raise AssertionError(f"duplicate visible public challenge: {public_name}")
                public_identifiers.add(public_name)
                public_payloads[public_name] = public_challenge_bytes(private_episode)

                if same_input is None:
                    key = "train:0"
                    same_input = {
                        "seed": private_episode["seed"],
                        "sample_index": private_episode["train"][0]["sample_index"],
                        "input": private_episode["train"][0]["input"],
                        "outputs": execution["all_outputs"][key],
                    }

            runtime_identity = bridge.runtime_identity

        for public_name in sorted(public_payloads):
            public_path = temporary / "public" / public_name
            public_path.parent.mkdir(parents=True, exist_ok=True)
            public_path.write_bytes(public_payloads[public_name])

        if same_input is None or len(
            {_json_bytes(output) for output in same_input["outputs"].values()}
        ) != len(prototype.SETTINGS):
            raise AssertionError("same-input witness does not distinguish all settings")
        _write_json(
            temporary / "private" / "same-input-disagreement.json",
            same_input,
        )

        episode_summaries.sort(key=lambda row: row["public_identifier"])

        prototype_path = SCRIPT_PATH.with_name("prototype.py")
        test_path = (
            REPO_ROOT
            / "generators"
            / prototype.TASK_ID
            / "tests"
            / "test_parametric_connection_axes.py"
        )
        report = {
            "schema": EVIDENCE_SCHEMA,
            "status": "passed_bounded_prototype_evidence",
            "prototype_status": "proposed_unapproved",
            "task_id": prototype.TASK_ID,
            "prototype_version": prototype.PROTOTYPE_VERSION,
            "parameter": {
                "name": prototype.PARAMETER_NAME,
                "default": prototype.DEFAULT_SETTING,
                "allowed": list(prototype.SETTINGS),
            },
            "counts": {
                "demos_per_episode": demo_count,
                "queries_per_episode": query_count,
            },
            "start_seed": start_seed,
            "episodes": episode_summaries,
            "programs": {
                setting: {
                    "path": f"private/rules/rule-{setting}.rkt",
                    "sha256": _sha256_bytes(program.encode("utf-8")),
                    "exact_canonical": setting == prototype.DEFAULT_SETTING,
                }
                for setting, program in programs.items()
            },
            "source": {
                "generator_path": generator_path.relative_to(REPO_ROOT).as_posix(),
                "generator_sha256": generator_sha256,
                "prototype_path": prototype_path.relative_to(REPO_ROOT).as_posix(),
                "prototype_sha256": _sha256_file(prototype_path),
                "test_path": test_path.relative_to(REPO_ROOT).as_posix(),
                "test_sha256": _sha256_file(test_path),
                "verifier_path": SCRIPT_PATH.relative_to(REPO_ROOT).as_posix(),
                "verifier_sha256": _sha256_file(SCRIPT_PATH),
            },
            "racket": {
                "preflight": runtime_preflight,
                "identity": runtime_identity,
                "all_retained_labels_executed": True,
            },
            "privacy": {
                "public_payload": "train input/output plus test input only",
                "public_filenames": "sha256 of exact visible challenge bytes",
                "private_setting_names_in_public_paths": False,
            },
            "limitations": [
                "bounded prototype evidence; not an approval or production rollout",
                "three deterministic episodes, one per parameter setting",
                "the approved generator and canonical ledger are not modified",
            ],
        }
        _write_json(temporary / "report.json", report)
        _write_json(temporary / "manifest.json", _manifest(temporary))
        temporary.rename(destination)
        return report
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--start-seed", type=int, default=20261023)
    parser.add_argument("--demo-count", type=int, default=prototype.DEFAULT_DEMO_COUNT)
    parser.add_argument("--query-count", type=int, default=prototype.DEFAULT_QUERY_COUNT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = build_evidence(
            args.out,
            start_seed=args.start_seed,
            demo_count=args.demo_count,
            query_count=args.query_count,
        )
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "status": report["status"],
                "output": str(args.out.resolve()),
                "episodes": len(report["episodes"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
