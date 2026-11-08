#!/usr/bin/env python3
"""Materialize and exact-Racket-verify all four midpoint-rule settings."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[2]
ROOT = next(parent for parent in HERE.parents if (parent / "shared" / "runtime").is_dir())
for path in (ROOT / "shared" / "runtime", ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.generic.concepts.extraction import _program_body  # noqa: E402


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "verify_parametric_92f4d4eb0dbb", HERE.with_name("prototype.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import midpoint prototype")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_json(value: Any) -> str:
    return _sha_bytes(
        json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    )


def _setting_name(setting: tuple[str, str]) -> str:
    return f"{setting[0]}_{setting[1]}"


def _racket_apply_many(bridge: RacketBridge, program: str, grids: list[list[list[int]]]):
    """Evaluate the exact rule body through the packet's Racket bridge.

    The stripped review bundle intentionally omits the ``scripts`` package used
    by the general-purpose rule wrapper, so this task-local verifier extracts
    the body of its own known ``(rule! (lambda (g) ...))`` programs directly.
    """
    body = _program_body(program)
    outputs = []
    for grid in grids:
        bridge.define_grid("g", grid)
        outputs.append(bridge.eval_text(body))
    return outputs


def build_report() -> dict[str, Any]:
    proto = _load_prototype()
    base = HERE.parent
    programs_dir = base / "programs"
    episodes_dir = base / "episodes"
    evidence_dir = base / "evidence"
    for directory in (programs_dir, episodes_dir, evidence_dir):
        directory.mkdir(parents=True, exist_ok=True)

    setting_seeds = {setting: index for index, setting in enumerate(proto.SETTINGS)}
    rows = []
    all_input_hashes = []
    bridge = RacketBridge()
    try:
        for setting in proto.SETTINGS:
            name = _setting_name(setting)
            seed = setting_seeds[setting]
            episode = proto.generate_episode(
                seed, side=setting[0], boundary=setting[1]
            )
            public = proto.public_challenge(episode)
            program = proto.program_for(*setting)

            program_path = programs_dir / f"{name}.rkt"
            complete_path = episodes_dir / f"{name}-complete.json"
            public_path = episodes_dir / f"{name}-public.json"
            program_path.write_text(program + "\n")
            complete_path.write_text(json.dumps(episode, indent=2, sort_keys=True) + "\n")
            public_path.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n")

            pairs = [
                (split, index, pair)
                for split in ("train", "test")
                for index, pair in enumerate(episode[split])
            ]
            inputs = [pair["input"] for _, _, pair in pairs]
            racket_outputs = _racket_apply_many(bridge, program, inputs)
            rival_racket = {
                rival: _racket_apply_many(bridge, proto.program_for(*rival), inputs)
                for rival in proto.SETTINGS
                if rival != setting
            }

            pair_rows = []
            for pair_index, ((split, index, pair), got) in enumerate(
                zip(pairs, racket_outputs, strict=True)
            ):
                rival_rows = {}
                for rival, outputs in rival_racket.items():
                    rival_name = _setting_name(rival)
                    rival_output = outputs[pair_index]
                    rival_rows[rival_name] = {
                        "racket_matches_python": rival_output
                        == proto.solve(
                            pair["input"], side=rival[0], boundary=rival[1]
                        ),
                        "differs_from_intended": rival_output != pair["output"],
                        "output_sha256": _sha_json(rival_output),
                    }
                pair_rows.append(
                    {
                        "split": split,
                        "index": index,
                        "input_sha256": _sha_json(pair["input"]),
                        "stored_output_sha256": _sha_json(pair["output"]),
                        "racket_output_sha256": _sha_json(got),
                        "racket_matches_stored": got == pair["output"],
                        "rivals": rival_rows,
                    }
                )
                all_input_hashes.append(_sha_json(pair["input"]))

            row = {
                "setting": {"side": setting[0], "boundary": setting[1]},
                "seed": seed,
                "program_path": str(program_path.relative_to(ROOT)),
                "program_sha256": _sha_bytes(program_path.read_bytes()),
                "normalized_program_sha256": proto.normalized_program_hash(*setting),
                "complete_episode_path": str(complete_path.relative_to(ROOT)),
                "complete_episode_sha256": _sha_bytes(complete_path.read_bytes()),
                "public_episode_path": str(public_path.relative_to(ROOT)),
                "public_episode_sha256": _sha_bytes(public_path.read_bytes()),
                "pairs": pair_rows,
                "all_racket_exact": all(item["racket_matches_stored"] for item in pair_rows),
                "every_rival_refuted_by_every_demo": all(
                    rival["differs_from_intended"]
                    for item in pair_rows
                    if item["split"] == "train"
                    for rival in item["rivals"].values()
                ),
                "every_rival_changes_query": all(
                    rival["differs_from_intended"]
                    for item in pair_rows
                    if item["split"] == "test"
                    for rival in item["rivals"].values()
                ),
                "all_rival_racket_python_exact": all(
                    rival["racket_matches_python"]
                    for item in pair_rows
                    for rival in item["rivals"].values()
                ),
            }
            rows.append(row)

    finally:
        bridge.shutdown()

    source_paths = [TASK_DIR / "generator.py", base / "prototype.py", HERE]
    report = {
        "schema": "92f4d4eb0dbb-parametric-midpoint-v1",
        "status": "proposed_prototype_not_selected",
        "task_id": proto.TASK_ID,
        "parameters": {
            "side": {
                "allowed_values": list(proto.ALLOWED_SIDES),
                "original_default": proto.DEFAULT_SIDE,
            },
            "boundary": {
                "allowed_values": list(proto.ALLOWED_BOUNDARIES),
                "original_default": proto.DEFAULT_BOUNDARY,
            },
            "selection_scope": "once per complete episode",
            "input_constraint": (
                "odd occupied height with an occupied midpoint row and occupied "
                "cells on both strict sides; all four settings differ per pair"
            ),
        },
        "settings": rows,
        "source_hashes": {
            str(path.relative_to(ROOT)): _sha_bytes(path.read_bytes())
            for path in source_paths
        },
        "all_racket_exact": all(row["all_racket_exact"] for row in rows),
        "all_rival_racket_python_exact": all(
            row["all_rival_racket_python_exact"] for row in rows
        ),
        "all_rivals_refuted_by_every_demo": all(
            row["every_rival_refuted_by_every_demo"] for row in rows
        ),
        "all_queries_setting_sensitive": all(
            row["every_rival_changes_query"] for row in rows
        ),
        "unique_input_count": len(set(all_input_hashes)),
        "limitations": [
            "This is a task-local proposal; the selected catalog remains lower/strict.",
            "Evidence covers four retained episodes, one per declared setting, not all seeds.",
            "Only side and boundary semantics vary; input colors, midpoint source, and recolor color stay fixed.",
        ],
        "replay": {
            "cwd": "repo",
            "argv": [
                "python3",
                "generators/92f4d4eb0dbb/workspace/parametric/verify.py",
                "--out",
                "../checks/parametric/92f4d4eb0dbb-midpoint.json",
            ],
        },
    }

    manifest_path = evidence_dir / "manifest.json"
    manifest_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report()
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    ok = all(
        (
            report["all_racket_exact"],
            report["all_rival_racket_python_exact"],
            report["all_rivals_refuted_by_every_demo"],
            report["all_queries_setting_sensitive"],
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
