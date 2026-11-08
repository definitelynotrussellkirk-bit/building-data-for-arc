#!/usr/bin/env python3
"""Materialize and exact-Racket-verify both projection-reach settings."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[2]
ROOT = next(parent for parent in HERE.parents if (parent / "shared" / "runtime").is_dir())
for _path in (ROOT / "shared" / "runtime", ROOT / "src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.generic.concepts.extraction import (  # noqa: E402
    _program_body as extract_program_body,
)
from reviewer_support import canonical_pairs  # noqa: E402

REPORT_SCHEMA = "48bda9528e71-parametric-projection-reach-v1"


def _load_prototype():
    source = HERE.with_name("prototype.py")
    spec = importlib.util.spec_from_file_location(
        "verify_parametric_48bda9528e71", source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import projection-reach prototype from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_json(value: Any) -> str:
    return _sha_bytes(
        json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    )


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def _racket_apply_many(
    bridge: RacketBridge,
    program: str,
    grids: list[list[list[int]]],
) -> list[list[list[int]]]:
    body = extract_program_body(program)
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


def write_public_batch(
    episodes: Iterable[dict[str, Any]],
    out_dir: Path,
    *,
    proto=None,
) -> list[dict[str, str]]:
    """Write visible-only challenges, rejecting duplicate visible payloads first."""
    proto = _load_prototype() if proto is None else proto
    staged: list[tuple[str, str, bytes]] = []
    seen_ids: set[str] = set()
    for episode in episodes:
        public_id = proto.public_id(episode)
        if public_id in seen_ids:
            raise ValueError(f"duplicate public challenge: {public_id}")
        seen_ids.add(public_id)
        filename = proto.public_filename(episode)
        expected = f"challenge-{public_id}.json"
        if filename != expected:
            raise ValueError(
                f"public filename must derive only from visible bytes: {filename!r}"
            )
        staged.append((public_id, filename, proto.public_bytes(episode)))

    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for public_id, filename, data in sorted(staged):
        path = out_dir / filename
        path.write_bytes(data)
        rows.append(
            {
                "public_id": public_id,
                "path": _display_path(path),
                "sha256": _sha_bytes(data),
            }
        )
    return rows


def build_report(*, artifact_root: Path | None = None) -> dict[str, Any]:
    """Build two four-query episodes and verify intended/rival Racket exactly."""
    proto = _load_prototype()
    base = HERE.parent if artifact_root is None else Path(artifact_root)
    programs_dir = base / "programs"
    private_dir = base / "episodes" / "private"
    public_dir = base / "episodes" / "public"
    evidence_dir = base / "evidence"
    for directory in (programs_dir, private_dir, evidence_dir):
        directory.mkdir(parents=True, exist_ok=True)

    setting_seeds = {"one_step": 20, "to_boundary": 21}
    episodes = {
        setting: proto.generate_episode(
            setting_seeds[setting],
            projection_reach=setting,
            difficulty="hard",
            n_train=4,
            n_test=4,
        )
        for setting in proto.SETTINGS
    }
    public_rows = write_public_batch(episodes.values(), public_dir, proto=proto)
    public_by_id = {row["public_id"]: row for row in public_rows}

    rows = []
    all_input_hashes: list[str] = []
    bridge = RacketBridge()
    try:
        canonical = canonical_pairs(proto.TASK_ID, root=ROOT)
        canonical_inputs = [pair["input"] for pair in canonical]
        canonical_got = _racket_apply_many(
            bridge, proto.program_for(proto.DEFAULT_SETTING), canonical_inputs
        )
        canonical_rows = [
            {
                "index": index,
                "input_sha256": _sha_json(pair["input"]),
                "expected_output_sha256": _sha_json(pair["output"]),
                "racket_output_sha256": _sha_json(got),
                "racket_matches_canonical": got == pair["output"],
            }
            for index, (pair, got) in enumerate(zip(canonical, canonical_got, strict=True))
        ]

        for setting in proto.SETTINGS:
            seed = setting_seeds[setting]
            episode = episodes[setting]
            public_id = proto.public_id(episode)
            public_row = public_by_id[public_id]
            program = proto.program_for(setting)
            rival = next(value for value in proto.SETTINGS if value != setting)
            rival_program = proto.program_for(rival)

            program_path = programs_dir / f"{setting}.rkt"
            private_path = private_dir / f"{setting}-complete.json"
            program_path.write_text(program + "\n")
            private_path.write_text(json.dumps(episode, indent=2, sort_keys=True) + "\n")

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
                rival_python = proto.apply_python(pair["input"], rival)
                input_hash = _sha_json(pair["input"])
                all_input_hashes.append(input_hash)
                pair_rows.append(
                    {
                        "split": split,
                        "index": index,
                        "input_sha256": input_hash,
                        "stored_output_sha256": _sha_json(pair["output"]),
                        "racket_output_sha256": _sha_json(got),
                        "racket_matches_stored": got == pair["output"],
                        "rival": rival,
                        "rival_output_sha256": _sha_json(rival_got),
                        "rival_racket_matches_python": rival_got == rival_python,
                        "rival_differs_from_intended": rival_got != pair["output"],
                    }
                )

            public = proto.public_challenge(episode)
            row = {
                "setting": setting,
                "seed": seed,
                "demo_count": len(episode["train"]),
                "query_count": len(episode["test"]),
                "program_path": _display_path(program_path),
                "program_sha256": _sha_bytes(program_path.read_bytes()),
                "normalized_program_sha256": proto.normalized_program_hash(setting),
                "private_episode_path": _display_path(private_path),
                "private_episode_sha256": _sha_bytes(private_path.read_bytes()),
                "public_episode_path": public_row["path"],
                "public_episode_sha256": public_row["sha256"],
                "public_id": public_id,
                "public_answer_masked": _public_is_masked(public),
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
            rows.append(row)
    finally:
        bridge.shutdown()

    source_paths = [TASK_DIR / "generator.py", HERE.with_name("prototype.py"), HERE]
    public_ids = [row["public_id"] for row in rows]
    report = {
        "schema": REPORT_SCHEMA,
        "status": "proposed_prototype_not_selected",
        "task_id": proto.TASK_ID,
        "public_parent": {
            "task_id": proto.PUBLIC_PARENT_TASK_ID,
            "sha256": proto.PUBLIC_PARENT_SHA256,
            "mode": "inspired_extension",
            "transferred_reasoning": (
                "object-derived projections continue beyond a local marker; "
                "the assigned family's source object, rare color and row/column "
                "extent dependencies remain unchanged"
            ),
        },
        "parameters": {
            proto.PARAMETER_NAME: {
                **proto.PARAMETER_SPEC,
                "allowed_values": list(proto.PARAMETER_SPEC["allowed_values"]),
            }
        },
        "settings": rows,
        "canonical_default_pairs": canonical_rows,
        "canonical_default_racket_exact": all(
            row["racket_matches_canonical"] for row in canonical_rows
        ),
        "source_hashes": {
            str(path.relative_to(ROOT)): _sha_bytes(path.read_bytes())
            for path in source_paths
        },
        "all_racket_exact": all(row["all_racket_exact"] for row in rows),
        "all_rival_racket_python_exact": all(
            row["rival_racket_python_exact"] for row in rows
        ),
        "all_rivals_refuted_by_every_demo": all(
            row["rival_refuted_by_every_demo"] for row in rows
        ),
        "all_queries_setting_sensitive": all(
            row["rival_changes_every_query"] for row in rows
        ),
        "all_public_challenges_masked": all(
            row["public_answer_masked"] for row in rows
        ),
        "all_public_ids_unique": len(public_ids) == len(set(public_ids)),
        "unique_input_count": len(set(all_input_hashes)),
        "limitations": [
            "This is a task-local proposed extension; production remains the one-step rule.",
            "Evidence covers two deterministic hard episodes, one per setting, not all seeds.",
            "Only projection reach varies; source-object, rare-color and extent semantics are fixed.",
        ],
        "replay": {
            "cwd": "repo",
            "argv": [
                "python3",
                "generators/48bda9528e71/workspace/parametric/verify.py",
                "--out",
                "../checks/parametric/48bda9528e71-projection-reach.json",
            ],
        },
    }
    manifest_path = evidence_dir / "manifest.json"
    manifest_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    args = parser.parse_args()
    report = build_report(artifact_root=args.artifact_root)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    ok = all(
        (
            report["canonical_default_racket_exact"],
            report["all_racket_exact"],
            report["all_rival_racket_python_exact"],
            report["all_rivals_refuted_by_every_demo"],
            report["all_queries_setting_sensitive"],
            report["all_public_challenges_masked"],
            report["all_public_ids_unique"],
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
