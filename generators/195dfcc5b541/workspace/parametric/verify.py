#!/usr/bin/env python3
"""Materialize and exact-Racket-verify all symmetry/order prototype settings."""
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

REPORT_SCHEMA = "195dfcc5b541-parametric-symmetry-order-v1"
TASK_ID = "195dfcc5b541"


def _load_prototype():
    path = HERE.with_name("prototype.py")
    spec = importlib.util.spec_from_file_location(
        "verify_parametric_prototype_195dfcc5b541", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import prototype from {path}")
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


def _setting_dict(setting: tuple[str, str]) -> dict[str, str]:
    return {
        "reflection_mode": setting[0],
        "column_order": setting[1],
    }


def _setting_slug(setting: tuple[str, str]) -> str:
    return f"reflection-{setting[0]}__order-{setting[1]}"


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    for base in (ROOT, ROOT.parent):
        try:
            return str(resolved.relative_to(base.resolve()))
        except ValueError:
            continue
    return str(resolved)


def _public_is_masked(public: dict[str, Any]) -> bool:
    return (
        set(public) == {"train", "test"}
        and len(public["train"]) == 3
        and len(public["test"]) == 4
        and all(set(pair) == {"input", "output"} for pair in public["train"])
        and all(set(pair) == {"input"} for pair in public["test"])
    )


def build_report(
    *,
    seed_base: int = 20261023,
    artifact_dir: Path | str,
) -> dict[str, Any]:
    """Write bounded private/public artifacts and return exact verification."""
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
    generator, source_path, source_sha256 = proto.selected_generator()

    settings_rows: list[dict[str, Any]] = []
    pending_public: list[tuple[str, bytes]] = []
    global_intended_exact = True
    global_racket_python_exact = True
    global_demo_rejection = True
    global_query_identifiable = True
    global_query_sensitive = True
    global_public_masked = True

    bridge = RacketBridge()
    runtime_identity = bridge.runtime_identity
    try:
        canonical_outputs = _racket_apply_many(
            bridge,
            default_program,
            [pair["input"] for pair in canonical_pairs],
        )
        canonical_racket_exact = all(
            got == pair["output"]
            for pair, got in zip(canonical_pairs, canonical_outputs, strict=True)
        )

        for setting_index, setting in enumerate(proto.SETTINGS):
            seed = seed_base + setting_index
            episode = proto.generate_episode(
                seed,
                reflection_mode=setting[0],
                column_order=setting[1],
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
                        reflection_mode=candidate[0],
                        column_order=candidate[1],
                    )
                    for grid in inputs
                ]
                for candidate in proto.SETTINGS
            }

            intended_outputs = racket_by_setting[setting]
            intended_exact = all(
                got == stored
                for got, stored in zip(intended_outputs, stored_outputs, strict=True)
            )
            racket_python_exact = all(
                racket_by_setting[candidate] == python_by_setting[candidate]
                for candidate in proto.SETTINGS
            )

            rival_demo_rows = []
            demos_refute_all_rivals = True
            for rival in proto.SETTINGS:
                if rival == setting:
                    continue
                fits_all_demos = all(
                    racket_by_setting[rival][demo_index]
                    == stored_outputs[demo_index]
                    for demo_index in range(3)
                )
                demos_refute_all_rivals &= not fits_all_demos
                rival_demo_rows.append(
                    {
                        "setting": _setting_dict(rival),
                        "fits_all_demos": fits_all_demos,
                    }
                )

            query_rows = []
            all_queries_identifiable = True
            all_queries_sensitive = True
            for query_index in range(4):
                pair_position = 3 + query_index
                fitted_changing_rivals = []
                differing_rivals = []
                for rival_row in rival_demo_rows:
                    rival = (
                        rival_row["setting"]["reflection_mode"],
                        rival_row["setting"]["column_order"],
                    )
                    differs = (
                        racket_by_setting[rival][pair_position]
                        != stored_outputs[pair_position]
                    )
                    if differs:
                        differing_rivals.append(rival_row["setting"])
                    if rival_row["fits_all_demos"] and differs:
                        fitted_changing_rivals.append(rival_row["setting"])
                identifiable = not fitted_changing_rivals
                sensitive = len(differing_rivals) == len(proto.SETTINGS) - 1
                all_queries_identifiable &= identifiable
                all_queries_sensitive &= sensitive
                query_rows.append(
                    {
                        "index": query_index,
                        "identifiable_from_demos": identifiable,
                        "setting_sensitive": sensitive,
                        "fitted_changing_rivals": fitted_changing_rivals,
                    }
                )

            pair_rows = []
            for pair_position, (split, index, pair) in enumerate(pair_refs):
                pair_rows.append(
                    {
                        "split": split,
                        "index": index,
                        "input_sha256": _sha_json(pair["input"]),
                        "stored_output_sha256": _sha_json(pair["output"]),
                        "racket_output_sha256": _sha_json(
                            intended_outputs[pair_position]
                        ),
                        "racket_matches_stored": (
                            intended_outputs[pair_position] == pair["output"]
                        ),
                        "all_rival_outputs_differ": all(
                            racket_by_setting[rival][pair_position] != pair["output"]
                            for rival in proto.SETTINGS
                            if rival != setting
                        ),
                    }
                )

            setting_status = all(
                (
                    intended_exact,
                    racket_python_exact,
                    demos_refute_all_rivals,
                    all_queries_identifiable,
                    all_queries_sensitive,
                    public_masked,
                )
            )
            settings_rows.append(
                {
                    "setting": _setting_dict(setting),
                    "seed": seed,
                    "program_sha256": _sha_bytes(program.encode()),
                    "normalized_program_hash": proto.normalized_program_hash(
                        *setting
                    ),
                    "program_path": _display_path(program_path),
                    "episode_path": _display_path(episode_path),
                    "public_id": public_id,
                    "public_masked": public_masked,
                    "racket_matches_stored": intended_exact,
                    "racket_matches_python_for_all_settings": racket_python_exact,
                    "demos_refute_all_rivals": demos_refute_all_rivals,
                    "all_queries_identifiable": all_queries_identifiable,
                    "all_queries_setting_sensitive": all_queries_sensitive,
                    "rival_demo_checks": rival_demo_rows,
                    "query_checks": query_rows,
                    "pairs": pair_rows,
                    "status": "pass" if setting_status else "fail",
                }
            )
            global_intended_exact &= intended_exact
            global_racket_python_exact &= racket_python_exact
            global_demo_rejection &= demos_refute_all_rivals
            global_query_identifiable &= all_queries_identifiable
            global_query_sensitive &= all_queries_sensitive
    finally:
        bridge.shutdown()

    public_ids = [public_id for public_id, _ in pending_public]
    unique_public_ids = len(public_ids) == len(set(public_ids))
    if not unique_public_ids:
        raise RuntimeError("duplicate visible public challenge payloads")
    for public_id, payload in sorted(pending_public):
        if _sha_bytes(payload) != public_id:
            raise RuntimeError("public ID does not hash the exact visible bytes")
        (public_dir / f"challenge-{public_id}.json").write_bytes(payload)

    canonical_default = {
        "program_byte_exact": default_program == canonical_program,
        "program_hash_exact": (
            proto.normalized_program_hash(*proto.DEFAULT_SETTING)
            == proto.CANONICAL_RULE_HASH
        ),
        "labeled_pairs": len(canonical_pairs),
        "racket_exact": canonical_racket_exact,
    }
    totals = {
        "settings": len(proto.SETTINGS),
        "episodes": len(settings_rows),
        "demonstrations": len(proto.SETTINGS) * 3,
        "queries": len(proto.SETTINGS) * 4,
        "stored_labels_checked_by_racket": len(proto.SETTINGS) * 7,
        "rival_labels_checked_by_racket": len(proto.SETTINGS) * 7 * 3,
        "query_rival_checks": len(proto.SETTINGS) * 4 * 3,
    }
    all_ok = all(
        (
            canonical_default["program_byte_exact"],
            canonical_default["program_hash_exact"],
            canonical_default["racket_exact"],
            global_intended_exact,
            global_racket_python_exact,
            global_demo_rejection,
            global_query_identifiable,
            global_query_sensitive,
            global_public_masked,
            unique_public_ids,
            all(row["status"] == "pass" for row in settings_rows),
        )
    )
    return {
        "schema": REPORT_SCHEMA,
        "status": "pass" if all_ok else "fail",
        "scope": "proposed_task_local_prototype",
        "task_id": TASK_ID,
        "prototype_version": proto.PROTOTYPE_VERSION,
        "parameters": {
            "reflection_mode": {
                "allowed_values": list(proto.REFLECTION_MODES),
                "original_default": proto.DEFAULT_SETTING[0],
                "selection_scope": "once_per_episode",
                "effect": "include only rotations or the full dihedral orbit",
            },
            "column_order": {
                "allowed_values": list(proto.COLUMN_ORDERS),
                "original_default": proto.DEFAULT_SETTING[1],
                "selection_scope": "once_per_episode",
                "effect": "resolve same-row overlapping candidates left-to-right or right-to-left",
            },
        },
        "canonical_default": canonical_default,
        "totals": totals,
        "settings": settings_rows,
        "public_ids": sorted(public_ids),
        "public_directory": _display_path(public_dir),
        "source": {
            "prototype_path": _display_path(HERE.with_name("prototype.py")),
            "prototype_sha256": _sha_bytes(
                HERE.with_name("prototype.py").read_bytes()
            ),
            "verifier_path": _display_path(HERE),
            "verifier_sha256": _sha_bytes(HERE.read_bytes()),
            "generator_path": _display_path(Path(source_path)),
            "generator_sha256": source_sha256,
            "canonical_ledger_sha256": _sha_bytes(canonical_path(ROOT).read_bytes()),
        },
        "runtime_identity": runtime_identity,
        "all_racket_matches_stored": global_intended_exact,
        "all_racket_matches_python_for_all_settings": global_racket_python_exact,
        "all_demos_refute_all_rivals": global_demo_rejection,
        "all_queries_identifiable_from_demos": global_query_identifiable,
        "all_queries_setting_sensitive": global_query_sensitive,
        "all_public_challenges_masked": global_public_masked,
        "public_ids_sorted_unique": unique_public_ids,
        "limitations": [
            "The production generator and canonical authority are unchanged.",
            "Evidence covers four retained episodes, one per setting, not every seed.",
            "The rival set is exactly the other three prototype settings, not every possible rule.",
            "Prototype inputs require a horizontal shape-0 stencil and add a controlled isolated 2x4 overlap motif.",
            "The proposed right-to-left setting is not approved or admitted to training.",
        ],
        "replay": {
            "cwd": "repo",
            "argv": [
                "python3",
                "generators/195dfcc5b541/workspace/parametric/verify.py",
                "--seed-base",
                str(seed_base),
                "--artifact-dir",
                _display_path(artifact_dir),
            ],
        },
    }


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
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
