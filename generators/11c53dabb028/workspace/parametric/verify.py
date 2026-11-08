#!/usr/bin/env python3
"""Materialize and exact-Racket-verify all repeat-count settings."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
ROOT = next(
    (
        parent
        for parent in HERE.parents
        if (parent / "shared" / "runtime" / "reviewer_support.py").is_file()
    ),
    HERE.parents[4],
)
for path in (ROOT / "shared" / "runtime", ROOT / "src"):
    if path.is_dir() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.generic.concepts.extraction import _program_body  # noqa: E402
from reviewer_support import canonical_path  # noqa: E402

REPORT_SCHEMA = "11c53dabb028-parametric-repeat-count-v1"
TASK_ID = "11c53dabb028"


def _load_prototype():
    path = HERE.with_name("prototype.py")
    spec = importlib.util.spec_from_file_location(
        "verify_parametric_prototype_11c53dabb028", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import repeat-count prototype from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_json(value: Any) -> str:
    return _sha_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    )


def _canonical_row() -> dict[str, Any]:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise RuntimeError(f"canonical row missing for {TASK_ID}")


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


def _public_is_masked(public: dict[str, Any]) -> bool:
    return (
        set(public) == {"train", "test"}
        and bool(public["train"])
        and bool(public["test"])
        and all(set(pair) == {"input", "output"} for pair in public["train"])
        and all(set(pair) == {"input"} for pair in public["test"])
    )


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    for base in (ROOT, ROOT.parent):
        try:
            return str(resolved.relative_to(base.resolve()))
        except ValueError:
            continue
    return str(resolved)


def _setting_dict(setting: tuple[int, int]) -> dict[str, int]:
    return {
        "vertical_repeats": setting[0],
        "horizontal_repeats": setting[1],
    }


def _setting_slug(setting: tuple[int, int]) -> str:
    return f"vertical-{setting[0]}_horizontal-{setting[1]}"


def _boundary_inputs() -> list[list[list[int]]]:
    square = [[0 for _ in range(15)] for _ in range(15)]
    square[0][0] = 3
    square[7][7] = 5
    return [
        [[7] + [0] * 14],
        [[0] for _ in range(14)] + [[8]],
        square,
    ]


def build_report(
    *,
    seed_base: int = 20261023,
    artifact_dir: Path | str,
) -> dict[str, Any]:
    """Write bounded artifacts and return their exact verification report."""
    if type(seed_base) is not int or seed_base < 0:
        raise ValueError("seed_base must be a nonnegative exact integer")
    artifact_dir = Path(artifact_dir)
    public_dir = artifact_dir / "public"
    rules_dir = artifact_dir / "private" / "rules"
    episodes_dir = artifact_dir / "private" / "episodes"
    for directory in (public_dir, rules_dir, episodes_dir):
        directory.mkdir(parents=True, exist_ok=True)

    proto = _load_prototype()
    canonical = _canonical_row()
    canonical_program = canonical["program_solution"]
    default_program = proto.program_for(*proto.DEFAULT_SETTING)
    canonical_pairs = [*canonical["train"], *canonical["test"]]

    settings_rows: list[dict[str, Any]] = []
    pending_public: list[tuple[str, bytes]] = []
    global_racket_exact = True
    global_rival_python_exact = True
    global_demos_refute = True
    global_queries_identifiable = True
    global_queries_sensitive = True
    global_public_masked = True
    global_boundary_exact = True
    boundary_rows: list[dict[str, Any]] = []

    bridge = RacketBridge(timeout=20, max_calls_before_restart=48)
    runtime_identity = bridge.runtime_identity
    try:
        canonical_outputs = _racket_apply_many(
            bridge,
            default_program,
            [pair["input"] for pair in canonical_pairs],
        )
        canonical_pairs_racket_exact = all(
            got == pair["output"]
            for pair, got in zip(canonical_pairs, canonical_outputs, strict=True)
        )

        boundary_inputs = _boundary_inputs()
        for setting in proto.SETTINGS:
            program = proto.program_for(*setting)
            racket_outputs = _racket_apply_many(bridge, program, boundary_inputs)
            for index, (grid, got) in enumerate(
                zip(boundary_inputs, racket_outputs, strict=True)
            ):
                expected = proto.solve(
                    grid,
                    vertical_repeats=setting[0],
                    horizontal_repeats=setting[1],
                )
                exact = got == expected
                global_boundary_exact &= exact
                boundary_rows.append(
                    {
                        "setting": _setting_dict(setting),
                        "index": index,
                        "input_shape": [len(grid), len(grid[0])],
                        "output_shape": [len(got), len(got[0])],
                        "input_sha256": _sha_json(grid),
                        "racket_output_sha256": _sha_json(got),
                        "racket_matches_python": exact,
                    }
                )

        for setting_index, setting in enumerate(proto.SETTINGS):
            seed = seed_base + setting_index
            episode = proto.generate_episode(
                seed,
                vertical_repeats=setting[0],
                horizontal_repeats=setting[1],
                n_train=3,
                n_test=4,
            )
            public = proto.public_challenge(episode)
            public_bytes = proto.public_bytes(episode)
            public_id = proto.public_id(episode)
            pending_public.append((public_id, public_bytes))
            public_masked = _public_is_masked(public)
            global_public_masked &= public_masked

            slug = _setting_slug(setting)
            program = proto.program_for(*setting)
            program_path = rules_dir / f"{slug}.rkt"
            episode_path = episodes_dir / f"{slug}.json"
            program_path.write_text(program + "\n", encoding="utf-8")
            episode_path.write_text(
                json.dumps(episode, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            pair_refs = [
                (split, index, pair)
                for split in ("train", "test")
                for index, pair in enumerate(episode[split])
            ]
            inputs = [pair["input"] for _, _, pair in pair_refs]
            stored_outputs = [pair["output"] for _, _, pair in pair_refs]
            racket_by_setting = {
                candidate: _racket_apply_many(
                    bridge,
                    proto.program_for(*candidate),
                    inputs,
                )
                for candidate in proto.SETTINGS
            }
            python_by_setting = {
                candidate: [
                    proto.solve(
                        grid,
                        vertical_repeats=candidate[0],
                        horizontal_repeats=candidate[1],
                    )
                    for grid in inputs
                ]
                for candidate in proto.SETTINGS
            }

            pair_rows = []
            intended_racket = racket_by_setting[setting]
            intended_exact = True
            rival_python_exact = True
            setting_sensitive_pairs = True
            for pair_position, ((split, index, pair), intended_got) in enumerate(
                zip(pair_refs, intended_racket, strict=True)
            ):
                intended_match = intended_got == pair["output"]
                intended_python_match = (
                    python_by_setting[setting][pair_position] == pair["output"]
                )
                intended_exact &= intended_match and intended_python_match
                rival_rows = []
                for rival in proto.SETTINGS:
                    if rival == setting:
                        continue
                    rival_racket = racket_by_setting[rival][pair_position]
                    rival_python = python_by_setting[rival][pair_position]
                    racket_python_match = rival_racket == rival_python
                    differs = rival_racket != pair["output"]
                    rival_python_exact &= racket_python_match
                    setting_sensitive_pairs &= differs
                    rival_rows.append(
                        {
                            "setting": _setting_dict(rival),
                            "racket_matches_python": racket_python_match,
                            "differs_from_intended": differs,
                            "output_sha256": _sha_json(rival_racket),
                        }
                    )
                pair_rows.append(
                    {
                        "split": split,
                        "index": index,
                        "input_sha256": _sha_json(pair["input"]),
                        "stored_output_sha256": _sha_json(pair["output"]),
                        "racket_output_sha256": _sha_json(intended_got),
                        "racket_matches_stored": intended_match,
                        "python_matches_stored": intended_python_match,
                        "rivals": rival_rows,
                    }
                )

            query_checks = []
            demos_refute_all_rivals = True
            queries_identifiable = True
            queries_setting_sensitive = True
            train_count = len(episode["train"])
            for query_index, query_pair in enumerate(episode["test"]):
                pair_position = train_count + query_index
                for rival in proto.SETTINGS:
                    if rival == setting:
                        continue
                    fits_all_demos = all(
                        racket_by_setting[rival][demo_index]
                        == stored_outputs[demo_index]
                        for demo_index in range(train_count)
                    )
                    changes_query = (
                        racket_by_setting[rival][pair_position]
                        != query_pair["output"]
                    )
                    ambiguous = fits_all_demos and changes_query
                    demos_refute_all_rivals &= not fits_all_demos
                    queries_identifiable &= not ambiguous
                    queries_setting_sensitive &= changes_query
                    query_checks.append(
                        {
                            "query_index": query_index,
                            "rival_setting": _setting_dict(rival),
                            "fits_all_demonstrations": fits_all_demos,
                            "changes_query": changes_query,
                            "ambiguous": ambiguous,
                        }
                    )

            global_racket_exact &= intended_exact
            global_rival_python_exact &= rival_python_exact
            global_demos_refute &= demos_refute_all_rivals
            global_queries_identifiable &= queries_identifiable
            global_queries_sensitive &= queries_setting_sensitive
            settings_rows.append(
                {
                    "setting": _setting_dict(setting),
                    "seed": seed,
                    "n_train": len(episode["train"]),
                    "n_test": len(episode["test"]),
                    "program_path": _display_path(program_path),
                    "program_sha256": _sha_bytes(program_path.read_bytes()),
                    "normalized_program_hash": proto.normalized_program_hash(*setting),
                    "episode_path": _display_path(episode_path),
                    "episode_sha256": _sha_bytes(episode_path.read_bytes()),
                    "public_id": public_id,
                    "public_answer_masked": public_masked,
                    "pairs": pair_rows,
                    "query_checks": query_checks,
                    "intended_racket_exact": intended_exact,
                    "rival_racket_python_exact": rival_python_exact,
                    "all_pairs_setting_sensitive": setting_sensitive_pairs,
                    "demos_refute_all_rivals": demos_refute_all_rivals,
                    "queries_identifiable_from_demos": queries_identifiable,
                    "queries_setting_sensitive": queries_setting_sensitive,
                }
            )
    finally:
        bridge.shutdown()

    public_ids = sorted(public_id for public_id, _ in pending_public)
    unique_public_ids = len(public_ids) == len(set(public_ids))
    if not unique_public_ids:
        raise RuntimeError("duplicate visible public challenge payloads")
    public_by_id = {public_id: payload for public_id, payload in pending_public}
    for public_id in public_ids:
        path = public_dir / f"challenge-{public_id}.json"
        path.write_bytes(public_by_id[public_id])

    source_paths = [
        ROOT / "generators" / TASK_ID / "generator.py",
        HERE.with_name("prototype.py"),
        HERE,
    ]
    source_hashes = {
        str(path.relative_to(ROOT)): _sha_bytes(path.read_bytes())
        for path in source_paths
    }
    counts = {
        "settings": len(proto.SETTINGS),
        "demonstrations_per_episode": 3,
        "queries_per_episode": 4,
        "pairs": len(proto.SETTINGS) * 7,
        "rival_pair_checks": len(proto.SETTINGS) * 7 * (len(proto.SETTINGS) - 1),
        "query_rival_checks": len(proto.SETTINGS) * 4 * (len(proto.SETTINGS) - 1),
        "boundary_checks": len(proto.SETTINGS) * len(_boundary_inputs()),
    }
    report = {
        "schema": REPORT_SCHEMA,
        "status": "proposed_prototype_not_selected",
        "task_id": TASK_ID,
        "parameters": {
            "vertical_repeats": {
                "allowed_values": list(proto.ALLOWED_REPEATS),
                "original_default": 2,
                "selection_scope": "once_per_episode",
                "effect": "number of vertical copies of the inverted periodic tile",
            },
            "horizontal_repeats": {
                "allowed_values": list(proto.ALLOWED_REPEATS),
                "original_default": 2,
                "selection_scope": "once_per_episode",
                "effect": "number of horizontal copies of the inverted periodic tile",
            },
        },
        "input_constraint": (
            "the selected generator's existing lawful 1..15 by 1..15 nontrivial "
            "zero/nonzero domain; all four settings remain within 30 by 30"
        ),
        "counts": counts,
        "canonical": {
            "default_setting": _setting_dict(proto.DEFAULT_SETTING),
            "program_exact": default_program == canonical_program,
            "normalized_rule_hash": proto.normalized_program_hash(
                *proto.DEFAULT_SETTING
            ),
            "canonical_pairs_racket_exact": canonical_pairs_racket_exact,
            "canonical_pair_count": len(canonical_pairs),
        },
        "settings": settings_rows,
        "boundary_checks": boundary_rows,
        "public_ids": public_ids,
        "public_directory": _display_path(public_dir),
        "source_hashes": source_hashes,
        "runtime_identity": runtime_identity,
        "all_racket_exact": global_racket_exact,
        "all_rival_racket_python_exact": global_rival_python_exact,
        "all_demos_refute_all_rivals": global_demos_refute,
        "all_queries_identifiable_from_demos": global_queries_identifiable,
        "all_queries_setting_sensitive": global_queries_sensitive,
        "all_public_challenges_masked": global_public_masked,
        "public_ids_sorted_unique": unique_public_ids,
        "all_boundary_racket_exact": global_boundary_exact,
        "limitations": [
            "This is a task-local proposed prototype; production remains canonical (2,2).",
            "Evidence covers four retained episodes, one per setting, not every seed.",
            "The rival set is exactly the other three repeat-count settings, not all possible rules.",
            "Repeat counts above two are intentionally out of scope to preserve the existing 30x30 input/output bound without narrowing inputs.",
        ],
        "replay": {
            "cwd": "repo",
            "argv": [
                "python3",
                "generators/11c53dabb028/workspace/parametric/verify.py",
                "--seed-base",
                str(seed_base),
                "--artifact-dir",
                _display_path(artifact_dir),
            ],
        },
    }
    return report


def _report_ok(report: dict[str, Any]) -> bool:
    return all(
        (
            report["canonical"]["program_exact"],
            report["canonical"]["normalized_rule_hash"] == "573d7b5ea64c",
            report["canonical"]["canonical_pairs_racket_exact"],
            report["all_racket_exact"],
            report["all_rival_racket_python_exact"],
            report["all_demos_refute_all_rivals"],
            report["all_queries_identifiable_from_demos"],
            report["all_queries_setting_sensitive"],
            report["all_public_challenges_masked"],
            report["public_ids_sorted_unique"],
            report["all_boundary_racket_exact"],
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-base", type=int, default=20261023)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(seed_base=args.seed_base, artifact_dir=args.artifact_dir)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if _report_ok(report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
