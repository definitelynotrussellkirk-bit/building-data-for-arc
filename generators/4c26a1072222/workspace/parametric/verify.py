#!/usr/bin/env python3
"""Execute and export the proposed forward/inverse settings with Racket."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
for dependency in (REPO, REPO / "shared" / "runtime", HERE):
    text = str(dependency)
    if text not in sys.path:
        sys.path.insert(0, text)

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.rule_wrap import strip_rule_wrapper  # noqa: E402
from reviewer_support import public_challenge_bytes  # noqa: E402
import prototype  # noqa: E402


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_public(path: Path, payload: Any) -> bytes:
    """Write the exact canonical bytes whose SHA-256 is the public ID."""
    path.parent.mkdir(parents=True, exist_ok=True)
    canonical = public_challenge_bytes(payload)
    path.write_bytes(canonical)
    return canonical


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    )
    return f"'({rows})"


def _application(program: str, grid: list[list[int]]) -> str:
    body = strip_rule_wrapper(program)
    if not body.lstrip().startswith("(lambda"):
        raise ValueError("prototype program must contain an exact lambda rule")
    return f"({body} {_grid_literal(grid)})"


def _parse_setting(value: str) -> str:
    try:
        return prototype.validate_setting(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _selected_settings(args: argparse.Namespace) -> tuple[str, ...]:
    if args.all_settings:
        return prototype.SETTINGS
    if args.setting is not None:
        return (args.setting,)
    return (prototype.choose_setting(args.seed),)


def _candidate_outputs(
    bridge: RacketBridge,
    programs: dict[str, str],
    grid: list[list[int]],
) -> dict[str, list[list[int]]]:
    outputs: dict[str, list[list[int]]] = {}
    for setting, program in programs.items():
        racket_output = bridge.eval_text(_application(program, grid))
        python_output = prototype.apply_setting(grid, setting)
        if racket_output != python_output:
            raise RuntimeError(f"Racket/Python mismatch for candidate {setting}")
        outputs[setting] = racket_output
    return outputs


def _racket_survivors(
    checks: list[dict[str, Any]],
    selected: str,
) -> list[str]:
    return [
        candidate
        for candidate in prototype.SETTINGS
        if all(
            row["candidate_outputs"][candidate]
            == row["candidate_outputs"][selected]
            for row in checks
            if row["split"] == "train"
        )
    ]


def _prepare_output_dir(path: Path, *, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not overwrite:
            raise FileExistsError(
                f"output directory is not empty: {path}; use --overwrite"
            )
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _input_schedule(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [
        pair["input"]
        for split in ("train", "test")
        for pair in episode[split]
    ]


def _sort_manifest_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return batch metadata in opaque public-ID order without mutating input."""
    return sorted(entries, key=lambda row: row["public_id"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--train-count", type=int, default=prototype.MIN_TRAIN)
    parser.add_argument("--query-count", type=int, default=prototype.MIN_TEST)
    parser.add_argument("--output-dir", required=True)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all-settings", action="store_true")
    group.add_argument("--setting", type=_parse_setting)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    settings = _selected_settings(args)
    programs = {
        setting: prototype.program_for(setting) for setting in prototype.SETTINGS
    }
    if programs[prototype.DEFAULT_SETTING] != prototype.canonical_program():
        raise SystemExit("default setting no longer exactly matches canonical authority")
    program_hashes = {_sha256_bytes(source.encode()) for source in programs.values()}
    if len(program_hashes) != len(programs):
        raise SystemExit("two declared settings materialize the same Racket program")

    output_dir = Path(args.output_dir).resolve()
    _prepare_output_dir(output_dir, overwrite=args.overwrite)

    episodes = {
        setting: prototype.build_episode(
            args.seed,
            application_direction=setting,
            n_train=args.train_count,
            n_test=args.query_count,
        )
        for setting in settings
    }
    for setting, episode in episodes.items():
        errors = prototype.episode_errors(episode)
        if errors:
            raise SystemExit(f"invalid {setting} episode: {errors}")
    schedules = {_sha256_bytes(json.dumps(_input_schedule(episode), separators=(",", ":")).encode()) for episode in episodes.values()}
    if len(schedules) != 1:
        raise SystemExit("selected settings did not share the same input schedule")

    manifest_entries: list[dict[str, Any]] = []
    total_racket_calls = 0
    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        runtime_identity = bridge.runtime_identity
        if not runtime_identity.get("protected"):
            raise SystemExit("Racket bridge did not pass the protected-runtime canary")
        for selected, provisional in episodes.items():
            episode = deepcopy(provisional)
            checks: list[dict[str, Any]] = []
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    outputs = _candidate_outputs(bridge, programs, pair["input"])
                    total_racket_calls += len(programs)
                    pair["output"] = outputs[selected]
                    checks.append(
                        {
                            "split": split,
                            "pair_index": index,
                            "sampling": pair["sampling"],
                            "candidate_outputs": outputs,
                        }
                    )

            errors = prototype.episode_errors(episode)
            if errors:
                raise SystemExit(f"Racket-labeled {selected} episode invalid: {errors}")
            survivors = _racket_survivors(checks, selected)
            if survivors != [selected]:
                raise SystemExit(
                    f"Racket demonstrations do not identify {selected}: {survivors}"
                )

            public = prototype.public_projection(episode)
            public_id = prototype.public_identifier(episode)
            episode_dir = output_dir / public_id
            episode_dir.mkdir(parents=True, exist_ok=False)
            canonical_public = _write_public(episode_dir / "public.json", public)
            if _sha256_bytes(canonical_public) != public_id:
                raise RuntimeError("public ID does not hash the exact visible public file")
            (episode_dir / "rule.rkt").write_text(
                programs[selected] + "\n", encoding="utf-8"
            )
            private = {
                "schema": "4c26a1072222-parametric-private-evidence-v1",
                "scope": "proposed task-local prototype; not canonical approval",
                "public_id": public_id,
                "public_canonical_bytes_sha256": _sha256_bytes(canonical_public),
                "episode": episode,
                "demonstration_survivors": survivors,
                "all_candidate_programs": {
                    setting: {
                        "source": source,
                        "sha256": _sha256_bytes(source.encode()),
                    }
                    for setting, source in programs.items()
                },
                "execution_checks": checks,
            }
            _write_json(episode_dir / "private.json", private)

            files = {}
            for name in ("public.json", "private.json", "rule.rkt"):
                path = episode_dir / name
                files[name] = {
                    "sha256": _sha256_file(path),
                    "bytes": path.stat().st_size,
                }
            manifest_entries.append(
                {
                    "public_id": public_id,
                    "setting": selected,
                    "train_count": len(episode["train"]),
                    "query_count": len(episode["test"]),
                    "demonstration_survivors": survivors,
                    "files": files,
                }
            )

    manifest_entries = _sort_manifest_entries(manifest_entries)

    generator_hashes = {episode["generator_sha256"] for episode in episodes.values()}
    if len(generator_hashes) != 1:
        raise SystemExit("episodes used different selected generator bytes")

    manifest = {
        "schema": "4c26a1072222-parametric-verification-v1",
        "status": "passed",
        "scope": "proposed task-local prototype; not canonical approval",
        "task_id": prototype.TASK_ID,
        "prototype_version": prototype.PROTOTYPE_VERSION,
        "seed": args.seed,
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "parameterization": {
            "application_direction": {
                "values": list(prototype.SETTINGS),
                "default": prototype.DEFAULT_SETTING,
            },
            "chosen_once_per_episode": True,
            "input_schedule_independent_of_setting": True,
            "demonstration_only_identification": True,
        },
        "counts": {
            "episodes": len(manifest_entries),
            "settings_available": len(prototype.SETTINGS),
            "train_pairs_per_episode": args.train_count,
            "query_pairs_per_episode": args.query_count,
            "racket_executions": total_racket_calls,
        },
        "input_schedule_sha256": next(iter(schedules)),
        "canonical_program_sha256": _sha256_bytes(
            prototype.canonical_program().encode()
        ),
        "candidate_program_sha256": {
            setting: _sha256_bytes(source.encode())
            for setting, source in programs.items()
        },
        "generator_sha256": next(iter(generator_hashes)),
        "prototype_source_sha256": {
            name: _sha256_file(HERE / name)
            for name in ("prototype.py", "verify.py", "README.md")
            if (HERE / name).is_file()
        },
        "racket_runtime": runtime_identity,
        "episodes": manifest_entries,
        "limitations": [
            "This is a proposed task-local prototype and is not wired into production generation or approval metadata.",
            "The retained verification covers one deterministic seed per setting, not every lawful input.",
            "Demonstrations eliminate the one declared alternative setting, not every imaginable transformation.",
            "Prototype inputs force a quarter-turn band so forward and inverse are observable; production sampling remains broader.",
        ],
    }
    _write_json(output_dir / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "status": "passed",
                "output_dir": str(output_dir),
                "counts": manifest["counts"],
                "public_ids": [row["public_id"] for row in manifest_entries],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
