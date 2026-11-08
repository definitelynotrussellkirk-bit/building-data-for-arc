#!/usr/bin/env python3
"""Materialize and exact-Racket-verify both handedness settings."""
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
ROOT = next(
    (parent for parent in HERE.parents if (parent / "shared" / "runtime").is_dir()),
    HERE.parents[4],
)
for path in (ROOT / "shared" / "runtime", ROOT / "src"):
    if path.is_dir() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.generic.concepts.extraction import _program_body  # noqa: E402

REPORT_SCHEMA = "196a7ec58bbc-parametric-handedness-v2"
RETAINED_DEMONSTRATION_COUNT = 3
RETAINED_QUERY_COUNT = 4
LEGACY_ARTIFACT_SHA256 = {
    "clockwise-complete.json": "041dfa35011a366bcf146fb53c53fbb6e08aee8e579e3b3c53c8f4e717d4e2db",
    "clockwise-public.json": "bc568a39ee79b074b0755ae63ca70582271461662f22225f1d0a1a91fc190a13",
    "counterclockwise-complete.json": "bd10c177d5a80fe8db19dc8fd1647d86ba7aab89499ff49fd843b2244805d3a2",
    "counterclockwise-public.json": "4b008e60728638300ff94a555dc59979cb4e44b3bdca1fc391953fdd78735da8",
}


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "verify_parametric_196a7ec58bbc", HERE.with_name("prototype.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import handedness prototype")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_json(value: Any) -> str:
    return _sha_bytes(
        json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    )


def _racket_apply_many(
    bridge: RacketBridge,
    program: str,
    grids: list[list[list[int]]],
):
    body = _program_body(program)
    outputs = []
    for grid in grids:
        bridge.define_grid("g", grid)
        outputs.append(bridge.eval_text(body))
    return outputs


def _public_is_masked(public: dict[str, Any]) -> bool:
    return (
        set(public) == {"train", "test"}
        and all(set(pair) == {"input", "output"} for pair in public.get("train", []))
        and all(set(pair) == {"input"} for pair in public.get("test", []))
    )


def _private_identity_invariance(proto, episode: dict[str, Any]) -> bool:
    changed = deepcopy(episode)
    changed["parameters"] = {"handedness": "private replacement"}
    changed["program"] = "private replacement"
    changed["meta"] = {"seed": 999_999, "private": True}
    for pair in changed["test"]:
        pair["output"] = [[9]]
    return (
        proto.public_bytes(changed) == proto.public_bytes(episode)
        and proto.public_id(changed) == proto.public_id(episode)
        and proto.public_filename(changed) == proto.public_filename(episode)
    )


def _visible_identity_sensitivity(proto, episode: dict[str, Any]) -> bool:
    changed = deepcopy(episode)
    value = changed["test"][0]["input"][0][0]
    changed["test"][0]["input"][0][0] = (value + 1) % 10
    return proto.public_id(changed) != proto.public_id(episode)


def build_report() -> dict[str, Any]:
    proto = _load_prototype()
    base = HERE.parent
    programs_dir = base / "programs"
    episodes_dir = base / "episodes"
    private_dir = episodes_dir / "private"
    public_dir = episodes_dir / "public"
    evidence_dir = base / "evidence"
    for directory in (programs_dir, private_dir, public_dir, evidence_dir):
        directory.mkdir(parents=True, exist_ok=True)

    # Preserve the original v1 evidence byte-for-byte. The corrected v2 export
    # is additive and lives only under episodes/private and episodes/public.
    legacy_artifacts = {
        name: {
            "path": str((episodes_dir / name).relative_to(ROOT)),
            "sha256": (
                _sha_bytes((episodes_dir / name).read_bytes())
                if (episodes_dir / name).is_file()
                else None
            ),
            "expected_sha256": expected,
        }
        for name, expected in LEGACY_ARTIFACT_SHA256.items()
    }
    legacy_artifacts_preserved_unchanged = all(
        row["sha256"] == row["expected_sha256"]
        for row in legacy_artifacts.values()
    )
    for stale in public_dir.glob("challenge-*.json"):
        stale.unlink()

    setting_seeds = {"clockwise": 0, "counterclockwise": 1}
    episodes: dict[str, dict[str, Any]] = {}
    for setting in proto.SETTINGS:
        episodes[setting] = proto.generate_episode(
            setting_seeds[setting],
            handedness=setting,
            demonstration_count=RETAINED_DEMONSTRATION_COUNT,
            query_count=RETAINED_QUERY_COUNT,
        )

    written = proto.write_public_batch(
        [episodes[setting] for setting in proto.SETTINGS],
        public_dir,
    )
    written_by_id = {row["public_id"]: row for row in written}
    reversed_written = proto.write_public_batch(
        [episodes[setting] for setting in reversed(proto.SETTINGS)],
        public_dir,
    )
    public_batch_order_independent = [
        (row["public_id"], Path(row["path"]).name) for row in written
    ] == [
        (row["public_id"], Path(row["path"]).name) for row in reversed_written
    ]
    try:
        proto.write_public_batch(
            [episodes[proto.SETTINGS[0]], deepcopy(episodes[proto.SETTINGS[0]])],
            public_dir,
        )
    except ValueError as error:
        duplicate_public_payload_rejected = "duplicate public payload" in str(error)
    else:
        duplicate_public_payload_rejected = False

    rows = []
    all_input_hashes = []
    bridge = RacketBridge()
    try:
        for setting in proto.SETTINGS:
            seed = setting_seeds[setting]
            episode = episodes[setting]
            public = proto.public_challenge(episode)
            identifier = proto.public_id(episode)
            program = proto.program_for(setting)
            rival = next(value for value in proto.SETTINGS if value != setting)
            rival_program = proto.program_for(rival)

            program_path = programs_dir / f"{setting}.rkt"
            complete_path = private_dir / f"{setting}-complete.json"
            public_path = Path(written_by_id[identifier]["path"])
            program_path.write_text(program + "\n")
            complete_path.write_text(
                json.dumps(episode, indent=2, sort_keys=True) + "\n"
            )

            pairs = [
                (split, index, pair)
                for split in ("train", "test")
                for index, pair in enumerate(episode[split])
            ]
            inputs = [pair["input"] for _, _, pair in pairs]
            intended_racket = _racket_apply_many(bridge, program, inputs)
            rival_racket = _racket_apply_many(bridge, rival_program, inputs)

            pair_rows = []
            for (split, index, pair), got, rival_got in zip(
                pairs, intended_racket, rival_racket, strict=True
            ):
                rival_python = proto.solve(pair["input"], handedness=rival)
                pair_rows.append(
                    {
                        "split": split,
                        "index": index,
                        "input_sha256": _sha_json(pair["input"]),
                        "stored_output_sha256": _sha_json(pair["output"]),
                        "racket_output_sha256": _sha_json(got),
                        "racket_matches_stored": got == pair["output"],
                        "rival": rival,
                        "rival_racket_matches_python": rival_got == rival_python,
                        "rival_differs_from_intended": rival_got != pair["output"],
                        "rival_output_sha256": _sha_json(rival_got),
                    }
                )
                all_input_hashes.append(_sha_json(pair["input"]))

            demo_rows = [item for item in pair_rows if item["split"] == "train"]
            query_pair_rows = [item for item in pair_rows if item["split"] == "test"]
            demos_identify_setting = any(
                item["rival_differs_from_intended"] for item in demo_rows
            )
            query_rows = [
                {
                    "index": item["index"],
                    "input_sha256": item["input_sha256"],
                    "racket_matches_stored": item["racket_matches_stored"],
                    "rival_changes_query": item["rival_differs_from_intended"],
                    "identifiable_from_demonstrations": (
                        demos_identify_setting and item["rival_differs_from_intended"]
                    ),
                }
                for item in query_pair_rows
            ]

            exact_public_bytes = proto.public_bytes(episode)
            row = {
                "setting": setting,
                "seed": seed,
                "demonstration_count": len(episode["train"]),
                "query_count": len(episode["test"]),
                "unique_episode_input_count": len(
                    {proto.grid_hash(pair["input"]) for _, _, pair in pairs}
                ),
                "program_path": str(program_path.relative_to(ROOT)),
                "program_sha256": _sha_bytes(program_path.read_bytes()),
                "normalized_program_sha256": proto.normalized_program_hash(setting),
                "complete_episode_path": str(complete_path.relative_to(ROOT)),
                "complete_episode_sha256": _sha_bytes(complete_path.read_bytes()),
                "public_id": identifier,
                "public_episode_path": str(public_path.relative_to(ROOT)),
                "public_episode_sha256": _sha_bytes(public_path.read_bytes()),
                "public_path_matches_visible_id": (
                    public_path.name == proto.public_filename(episode)
                ),
                "public_bytes_exact": public_path.read_bytes() == exact_public_bytes,
                "public_answer_masked": _public_is_masked(public),
                "private_fields_and_query_answers_do_not_change_public_identity": (
                    _private_identity_invariance(proto, episode)
                ),
                "visible_query_input_changes_public_identity": (
                    _visible_identity_sensitivity(proto, episode)
                ),
                "pairs": pair_rows,
                "queries": query_rows,
                "all_racket_exact": all(
                    item["racket_matches_stored"] for item in pair_rows
                ),
                "rival_racket_python_exact": all(
                    item["rival_racket_matches_python"] for item in pair_rows
                ),
                "rival_refuted_by_every_demo": all(
                    item["rival_differs_from_intended"] for item in demo_rows
                ),
                "demos_identify_setting": demos_identify_setting,
                "all_queries_identifiable_from_demonstrations": all(
                    item["identifiable_from_demonstrations"] for item in query_rows
                ),
            }
            rows.append(row)
    finally:
        bridge.shutdown()

    current_public_files = sorted(path.name for path in public_dir.glob("*.json"))
    expected_public_files = sorted(proto.public_filename(episode) for episode in episodes.values())
    v2_public_directory_content_addressed_only = (
        current_public_files == expected_public_files
        and all(
            setting not in name
            for name in current_public_files
            for setting in proto.SETTINGS
        )
    )

    source_paths = [TASK_DIR / "generator.py", base / "prototype.py", HERE]
    report = {
        "schema": REPORT_SCHEMA,
        "status": "proposed_prototype_not_selected",
        "task_id": proto.TASK_ID,
        "parameters": {
            "handedness": {
                "allowed_values": list(proto.ALLOWED_HANDEDNESS),
                "original_default": proto.DEFAULT_HANDEDNESS,
                "selection_scope": "once per complete episode",
                "input_constraint": (
                    "four distinct rotations; clockwise and counterclockwise "
                    "quarter-turn quadrants differ on every retained pair"
                ),
            }
        },
        "retained_counts": {
            "demonstrations": RETAINED_DEMONSTRATION_COUNT,
            "queries": RETAINED_QUERY_COUNT,
        },
        "settings": rows,
        "source_hashes": {
            str(path.relative_to(ROOT)): _sha_bytes(path.read_bytes())
            for path in source_paths
        },
        "all_racket_exact": all(row["all_racket_exact"] for row in rows),
        "all_rival_racket_python_exact": all(
            row["rival_racket_python_exact"] for row in rows
        ),
        "all_demos_identify_setting": all(
            row["demos_identify_setting"] for row in rows
        ),
        "all_queries_identifiable_from_demonstrations": all(
            row["all_queries_identifiable_from_demonstrations"] for row in rows
        ),
        "all_public_challenges_masked": all(
            row["public_answer_masked"] for row in rows
        ),
        "all_public_identities_visible_only": all(
            row["public_path_matches_visible_id"]
            and row["public_bytes_exact"]
            and row["private_fields_and_query_answers_do_not_change_public_identity"]
            and row["visible_query_input_changes_public_identity"]
            for row in rows
        ),
        "public_batch_order_independent": public_batch_order_independent,
        "duplicate_public_payload_rejected": duplicate_public_payload_rejected,
        "v2_public_directory_content_addressed_only": (
            v2_public_directory_content_addressed_only
        ),
        "legacy_artifacts_preserved_unchanged": (
            legacy_artifacts_preserved_unchanged
        ),
        "legacy_artifacts": legacy_artifacts,
        "unique_input_count": len(set(all_input_hashes)),
        "limitations": [
            "This is a task-local proposal; the selected catalog remains clockwise.",
            "Evidence covers two retained episodes, one per setting, not all seeds.",
            "Only quadrant handedness varies; TL remains original and BR remains 180 degrees.",
            "Episode requests are bounded to 64 total pairs and 4,096 deterministic candidate attempts.",
        ],
        "replay": {
            "cwd": "repo",
            "argv": [
                "python3",
                "generators/196a7ec58bbc/workspace/parametric/verify.py",
                "--out",
                "../checks/parametric/196a7ec58bbc-handedness-v2.json",
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
            report["all_demos_identify_setting"],
            report["all_queries_identifiable_from_demonstrations"],
            report["all_public_challenges_masked"],
            report["all_public_identities_visible_only"],
            report["public_batch_order_independent"],
            report["duplicate_public_payload_rejected"],
            report["v2_public_directory_content_addressed_only"],
            report["legacy_artifacts_preserved_unchanged"],
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
