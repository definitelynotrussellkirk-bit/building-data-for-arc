#!/usr/bin/env python3
"""Materialize and exact-Racket-verify both ray-orientation settings."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[2]
ROOT = HERE.parents[4]
for dependency in (ROOT / "shared" / "runtime", ROOT / "src"):
    if str(dependency) not in sys.path:
        sys.path.insert(0, str(dependency))

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.generic.concepts.extraction import _program_body  # noqa: E402
from reviewer_support import canonical_pairs, canonical_path  # noqa: E402

REPORT_SCHEMA = "1d62131e83ca-parametric-ray-orientation-v1"


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "verify_prototype_1d62131e83ca", HERE.with_name("prototype.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import ray-orientation prototype")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_json(value: Any) -> str:
    return _sha_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _racket_apply_many(
    bridge: RacketBridge,
    program: str,
    grids: list[list[list[int]]],
) -> list[list[list[int]]]:
    body = _program_body(program)
    outputs = []
    for grid in grids:
        bridge.define_grid("g", grid)
        outputs.append(bridge.eval_text(body))
    return outputs


def _canonical_program(task_id: str) -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                program = row.get("program_solution")
                if not isinstance(program, str) or not program:
                    raise ValueError(f"canonical task {task_id} has no program_solution")
                return program
    raise KeyError(task_id)


def _public_is_masked(public: dict[str, Any]) -> bool:
    return (
        set(public) == {"train", "test"}
        and all(set(pair) == {"input", "output"} for pair in public["train"])
        and all(set(pair) == {"input"} for pair in public["test"])
    )


def _clear_generated_files(base_dir: Path) -> None:
    patterns = (
        "programs/*.rkt",
        "episodes/private/*.json",
        "episodes/public/challenge-*.json",
        "evidence/manifest.json",
    )
    for pattern in patterns:
        for path in base_dir.glob(pattern):
            if path.is_file():
                path.unlink()


def build_report(*, base_dir: Path | None = None) -> dict[str, Any]:
    """Write two bounded episodes and verify every label with exact Racket."""
    proto = _load_prototype()
    base = HERE.parent if base_dir is None else Path(base_dir).resolve()
    programs_dir = base / "programs"
    private_dir = base / "episodes" / "private"
    public_dir = base / "episodes" / "public"
    evidence_dir = base / "evidence"
    for directory in (programs_dir, private_dir, public_dir, evidence_dir):
        directory.mkdir(parents=True, exist_ok=True)
    _clear_generated_files(base)

    canonical_source = _canonical_program(proto.TASK_ID)
    canonical_rows = canonical_pairs(proto.TASK_ID, root=ROOT, labeled_only=True)
    setting_seeds = {"nw_se": 117, "ne_sw": 118}
    settings: list[dict[str, Any]] = []
    all_input_hashes: list[str] = []
    visible_ids: set[str] = set()

    bridge = RacketBridge()
    try:
        canonical_outputs = _racket_apply_many(
            bridge,
            proto.program_for(proto.DEFAULT_RAY_ORIENTATION),
            [row["input"] for row in canonical_rows],
        )
        canonical_pair_checks = [
            {
                "split": row["split"],
                "pair_index": row["pair_index"],
                "input_sha256": _sha_json(row["input"]),
                "expected_output_sha256": _sha_json(row["output"]),
                "racket_output_sha256": _sha_json(actual),
                "matches": actual == row["output"],
            }
            for row, actual in zip(canonical_rows, canonical_outputs, strict=True)
        ]
        canonical_default_exact = (
            proto.program_for(proto.DEFAULT_RAY_ORIENTATION) == canonical_source
            and all(row["matches"] for row in canonical_pair_checks)
        )

        for setting in proto.SETTINGS:
            seed = setting_seeds[setting]
            episode = proto.generate_episode(
                seed,
                difficulty="medium",
                ray_orientation=setting,
                demo_count=3,
                query_count=4,
            )
            replay = proto.generate_episode(
                seed,
                difficulty="medium",
                ray_orientation=setting,
                demo_count=3,
                query_count=4,
            )
            if replay != episode:
                raise AssertionError(f"same-seed replay changed for {setting}")

            program = proto.program_for(setting)
            rival = next(value for value in proto.SETTINGS if value != setting)
            rival_program = proto.program_for(rival)
            public = proto.public_challenge(episode)
            visible_bytes = proto.public_bytes(episode)
            public_id = proto.public_id(episode)
            if public_id in visible_ids:
                raise AssertionError("duplicate visible public challenge")
            visible_ids.add(public_id)

            private_mutation = deepcopy(episode)
            private_mutation["parameters"]["ray_orientation"] = rival
            private_mutation["program"] = "private mutation"
            private_mutation["meta"]["seed"] = seed + 1_000_000
            for pair in private_mutation["test"]:
                pair["output"] = [[9]]
            public_id_visible_only = proto.public_id(private_mutation) == public_id

            program_path = programs_dir / f"{setting}.rkt"
            private_path = private_dir / f"{setting}.json"
            public_path = public_dir / f"challenge-{public_id}.json"
            program_path.write_text(program + "\n")
            _write_json(private_path, episode)
            public_path.write_bytes(visible_bytes)

            pairs = [
                (split, index, pair)
                for split in ("train", "test")
                for index, pair in enumerate(episode[split])
            ]
            inputs = [pair["input"] for _, _, pair in pairs]
            intended_racket = _racket_apply_many(bridge, program, inputs)
            rival_racket = _racket_apply_many(bridge, rival_program, inputs)

            pair_rows = []
            for split_index, ((split, index, pair), intended, rival_output) in enumerate(
                zip(pairs, intended_racket, rival_racket, strict=True)
            ):
                rival_python = proto.solve(pair["input"], ray_orientation=rival)
                pair_rows.append(
                    {
                        "ordinal": split_index,
                        "split": split,
                        "index": index,
                        "input_sha256": _sha_json(pair["input"]),
                        "stored_output_sha256": _sha_json(pair["output"]),
                        "racket_output_sha256": _sha_json(intended),
                        "racket_matches_stored": intended == pair["output"],
                        "rival": rival,
                        "rival_racket_output_sha256": _sha_json(rival_output),
                        "rival_racket_matches_python": rival_output == rival_python,
                        "rival_differs_from_intended": rival_output != pair["output"],
                    }
                )
                all_input_hashes.append(_sha_json(pair["input"]))

            row = {
                "setting": setting,
                "seed": seed,
                "rival": rival,
                "program_path": str(program_path.relative_to(base)),
                "program_sha256": _sha_bytes(program_path.read_bytes()),
                "normalized_program_sha256": proto.normalized_program_hash(setting),
                "private_episode_path": str(private_path.relative_to(base)),
                "private_episode_sha256": _sha_bytes(private_path.read_bytes()),
                "public_episode_path": str(public_path.relative_to(base)),
                "public_episode_sha256": _sha_bytes(public_path.read_bytes()),
                "public_id": public_id,
                "public_bytes_sha256": _sha_bytes(visible_bytes),
                "public_answer_masked": _public_is_masked(public),
                "public_id_visible_only": public_id_visible_only,
                "deterministic_replay": replay == episode,
                "pairs": pair_rows,
                "all_racket_exact": all(
                    item["racket_matches_stored"] for item in pair_rows
                ),
                "rival_racket_python_exact": all(
                    item["rival_racket_matches_python"] for item in pair_rows
                ),
                "rival_refuted_by_every_demo": all(
                    item["rival_differs_from_intended"]
                    for item in pair_rows
                    if item["split"] == "train"
                ),
                "rival_changes_every_query": all(
                    item["rival_differs_from_intended"]
                    for item in pair_rows
                    if item["split"] == "test"
                ),
            }
            settings.append(row)
    finally:
        bridge.shutdown()

    settings.sort(key=lambda row: row["public_episode_path"])
    source_paths = [TASK_DIR / "generator.py", HERE.with_name("prototype.py"), HERE]
    report = {
        "schema": REPORT_SCHEMA,
        "status": "proposed_prototype_not_selected",
        "approved": False,
        "task_id": proto.TASK_ID,
        "parameter": {
            "name": "ray_orientation",
            "allowed_values": list(proto.ALLOWED_RAY_ORIENTATIONS),
            "original_default": proto.DEFAULT_RAY_ORIENTATION,
            "selection_scope": "once per complete episode",
            "input_constraints": (
                "retained pairs use the common collision-free support of both "
                "orientations and each pair changes under the rival"
            ),
        },
        "episode_shape": {"demonstrations": 3, "queries": 4},
        "settings": settings,
        "canonical_program_exact_text": (
            proto.program_for(proto.DEFAULT_RAY_ORIENTATION) == canonical_source
        ),
        "canonical_pair_checks": canonical_pair_checks,
        "canonical_default_exact": canonical_default_exact,
        "all_racket_exact": all(row["all_racket_exact"] for row in settings),
        "all_rival_racket_python_exact": all(
            row["rival_racket_python_exact"] for row in settings
        ),
        "all_rivals_refuted_by_every_demo": all(
            row["rival_refuted_by_every_demo"] for row in settings
        ),
        "all_queries_setting_sensitive": all(
            row["rival_changes_every_query"] for row in settings
        ),
        "all_public_challenges_masked": all(
            row["public_answer_masked"] for row in settings
        ),
        "all_public_ids_visible_only": all(
            row["public_id_visible_only"] for row in settings
        ),
        "unique_input_count": len(set(all_input_hashes)),
        "source_hashes": {
            str(path.relative_to(ROOT)): _sha_bytes(path.read_bytes())
            for path in source_paths
        },
        "counts": {
            "settings": len(settings),
            "episodes": len(settings),
            "demonstrations": 3 * len(settings),
            "queries": 4 * len(settings),
            "racket_evaluations": len(canonical_rows) + 14 * len(settings),
            "canonical_pairs": len(canonical_rows),
        },
        "limitations": [
            "Task-local proposed prototype only; production generator and canonical authority are unchanged.",
            "Evidence covers two retained medium episodes, one per setting, not every seed or grid size.",
            "Rival analysis covers only the two declared ray orientations, not every conceivable rule.",
            "The sampler uses the common collision-free domain so both settings are lawful on every retained input.",
        ],
        "replay": {
            "cwd": "repo",
            "argv": [
                "python3",
                "generators/1d62131e83ca/workspace/parametric/verify.py",
                "--out",
                "../checks/parametric/1d62131e83ca-ray-orientation.json",
            ],
        },
    }
    manifest_path = evidence_dir / "manifest.json"
    _write_json(manifest_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-dir", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(base_dir=args.base_dir)
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
            report["canonical_default_exact"],
            report["all_public_challenges_masked"],
            report["all_public_ids_visible_only"],
            report["unique_input_count"] == 14,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
