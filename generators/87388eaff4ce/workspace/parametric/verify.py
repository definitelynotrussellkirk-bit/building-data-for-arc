#!/usr/bin/env python3
"""Materialize and Racket-verify both proposed tie-break settings."""
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
ROOT = next(
    parent for parent in HERE.parents
    if (parent / "shared" / "runtime" / "reviewer_support.py").exists()
)
for path in (ROOT / "src", ROOT / "shared" / "runtime"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.generic.concepts.extraction import _program_body  # noqa: E402


def _load_prototype():
    spec = importlib.util.spec_from_file_location("verify_parametric_87388", HERE.with_name("prototype.py"))
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import prototype")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_json(value: Any) -> str:
    return _sha_bytes(json.dumps(value, separators=(",", ":"), sort_keys=True).encode())


def build_report() -> dict[str, Any]:
    proto = _load_prototype()
    programs_dir = HERE.parent / "programs"
    episodes_dir = HERE.parent / "episodes"
    programs_dir.mkdir(parents=True, exist_ok=True)
    episodes_dir.mkdir(parents=True, exist_ok=True)

    setting_seeds = {"color_asc": 40, "color_desc": 41}
    report_rows = []
    all_inputs = []
    with RacketBridge() as bridge:
        for setting in proto.ALLOWED_SETTINGS:
            other = next(value for value in proto.ALLOWED_SETTINGS if value != setting)
            episode = proto.generate_episode(setting_seeds[setting], setting=setting)
            public = proto.public_challenge(episode)
            program = proto.program_for(setting)
            program_path = programs_dir / f"{setting}.rkt"
            program_path.write_text(program + "\n")
            episode_path = episodes_dir / f"{setting}-complete.json"
            public_path = episodes_dir / f"{setting}-public.json"
            episode_path.write_text(json.dumps(episode, indent=2, sort_keys=True) + "\n")
            public_path.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n")

            body = _program_body(program)
            other_body = _program_body(proto.program_for(other))
            pair_rows = []
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    bridge.define_grid("g", pair["input"])
                    got = bridge.eval_text(body)
                    bridge.define_grid("g", pair["input"])
                    other_got = bridge.eval_text(other_body)
                    pair_rows.append(
                        {
                            "split": split,
                            "index": index,
                            "input_sha256": _sha_json(pair["input"]),
                            "stored_output_sha256": _sha_json(pair["output"]),
                            "racket_output_sha256": _sha_json(got),
                            "racket_matches_stored": got == pair["output"],
                            "alternate_racket_matches_python": other_got == proto.solve(pair["input"], other),
                            "alternate_differs_from_intended": other_got != pair["output"],
                        }
                    )
                    all_inputs.append(pair["input"])

            report_rows.append(
                {
                    "setting": setting,
                    "seed": setting_seeds[setting],
                    "program_path": str(program_path.relative_to(ROOT)),
                    "program_sha256": _sha_bytes(program_path.read_bytes()),
                    "normalized_program_sha256": proto.normalized_program_hash(setting),
                    "episode_path": str(episode_path.relative_to(ROOT)),
                    "episode_sha256": _sha_bytes(episode_path.read_bytes()),
                    "public_path": str(public_path.relative_to(ROOT)),
                    "public_sha256": _sha_bytes(public_path.read_bytes()),
                    "pairs": pair_rows,
                    "all_racket_exact": all(row["racket_matches_stored"] for row in pair_rows),
                    "alternative_refuted_by_every_demo": all(
                        row["alternate_differs_from_intended"]
                        for row in pair_rows
                        if row["split"] == "train"
                    ),
                    "alternative_changes_query": all(
                        row["alternate_differs_from_intended"]
                        for row in pair_rows
                        if row["split"] == "test"
                    ),
                }
            )

    source_paths = [
        TASK_DIR / "generator.py",
        HERE.parent / "prototype.py",
        HERE,
    ]
    report = {
        "schema": "87388eaff4ce-parametric-tiebreak-prototype-v1",
        "status": "proposed_prototype_not_selected",
        "task_id": "87388eaff4ce",
        "parameter": {
            "name": proto.PARAMETER_NAME,
            "allowed_values": list(proto.ALLOWED_SETTINGS),
            "original_default": proto.DEFAULT_SETTING,
            "selection_scope": "once per complete episode",
            "input_constraint": (
                "every demonstration and query contains an equal-height pair whose "
                "color order changes the result"
            ),
        },
        "settings": report_rows,
        "source_hashes": {
            str(path.relative_to(ROOT)): _sha_bytes(path.read_bytes()) for path in source_paths
        },
        "all_racket_exact": all(row["all_racket_exact"] for row in report_rows),
        "all_alternatives_refuted_by_demos": all(
            row["alternative_refuted_by_every_demo"] for row in report_rows
        ),
        "all_queries_setting_sensitive": all(
            row["alternative_changes_query"] for row in report_rows
        ),
        "unique_input_count": len({_sha_json(grid) for grid in all_inputs}),
        "limitations": [
            "This is a task-local proposal; the selected catalog remains fixed to color_asc.",
            "Evidence covers two retained seeds and the declared two-value setting space, not all seeds.",
            "The prototype varies only the tie-break; height-descending and packing remain fixed.",
        ],
        "replay": {
            "cwd": "repo",
            "argv": [
                "python3",
                "generators/87388eaff4ce/workspace/parametric/verify.py",
                "--out",
                "../checks/parametric/87388eaff4ce-tiebreak.json",
            ],
        },
    }
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
    ok = (
        report["all_racket_exact"]
        and report["all_alternatives_refuted_by_demos"]
        and report["all_queries_setting_sensitive"]
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
