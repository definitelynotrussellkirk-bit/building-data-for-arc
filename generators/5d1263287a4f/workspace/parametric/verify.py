#!/usr/bin/env python3
"""Build exact Racket-backed evidence for the output-transform prototype."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

HERE = Path(__file__).resolve().parent
REPORT_SCHEMA = "5d1263287a4f-output-transform-evidence-v1"


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location(
        "parametric_5d1263287a4f_output_transform", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import prototype from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load_prototype()


def _install_packet_scripts_namespace(root: Path) -> None:
    """Expose the parser namespace required lazily by ``wrap_rule``.

    Source packets retain the parser at ``shared/tools`` while staged runtimes
    expose it at ``scripts``.  Bind either source to the exact qualified name
    expected by the shared wrapper, without changing parser or wrapper code.
    """
    qualified = "scripts.comment_solutions"
    if qualified in sys.modules:
        return
    candidates = (
        root / "scripts" / "comment_solutions.py",
        root / "shared" / "tools" / "comment_solutions.py",
    )
    source = next((path for path in candidates if path.is_file()), None)
    if source is None:
        raise FileNotFoundError(
            "missing packet parser source; checked "
            + ", ".join(str(path) for path in candidates)
        )
    package = sys.modules.get("scripts")
    if package is None:
        package = types.ModuleType("scripts")
        package.__path__ = [str(source.parent)]
        sys.modules["scripts"] = package
    spec = importlib.util.spec_from_file_location(qualified, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load packet parser source: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(qualified, None)
        raise


def _callable_rule(program: str) -> str:
    _install_packet_scripts_namespace(find_root(__file__))
    return PROTOTYPE.rule_callable(program)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def prepare_public_exports(
    episodes: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Project, deduplicate, and deterministically order a public batch."""
    rows: list[dict[str, Any]] = []
    seen_payloads: dict[bytes, str] = {}
    seen_ids: dict[str, bytes] = {}
    for setting, episode in episodes.items():
        public = PROTOTYPE.public_challenge(episode)
        visible_bytes = public_challenge_bytes(public)
        public_id = public_challenge_id(public)
        filename = PROTOTYPE.public_filename(episode)
        expected_filename = f"challenge-{public_id}.json"
        if filename != expected_filename:
            raise AssertionError(
                f"public filename mismatch: {filename!r} != {expected_filename!r}"
            )
        if visible_bytes in seen_payloads:
            first = seen_payloads[visible_bytes]
            raise ValueError(
                "duplicate visible payload for "
                f"settings {first!r} and {setting!r}"
            )
        prior = seen_ids.get(public_id)
        if prior is not None and prior != visible_bytes:
            raise ValueError(f"public ID collision for {public_id}")
        seen_payloads[visible_bytes] = setting
        seen_ids[public_id] = visible_bytes
        rows.append(
            {
                "setting": setting,
                "public_id": public_id,
                "filename": filename,
                "visible_bytes": visible_bytes,
            }
        )
    return sorted(rows, key=lambda row: row["public_id"])


def _grid_symbol(grid: list[list[int]], suffix: str = "") -> str:
    digest = _sha256_json(grid)[:16]
    return f"__output_transform_grid_{digest}_{suffix}".rstrip("_")


def execute_program(
    bridge: RacketBridge,
    program: str,
    grid: list[list[int]],
) -> list[list[int]]:
    """Execute one exact program against one grid in the protected bridge."""
    symbol = _grid_symbol(grid, _sha256_bytes(program.encode("utf-8"))[:8])
    bridge.define_grid(symbol, grid)
    return bridge.eval_text(f"({_callable_rule(program)} {symbol})")


def seed_for(setting: str, start_seed: int) -> int:
    PROTOTYPE._validate_setting(setting)
    PROTOTYPE._validate_seed(start_seed)
    for seed in range(start_seed, start_seed + 100_000):
        if PROTOTYPE.choose_setting(seed) == setting:
            return seed
    raise RuntimeError(f"could not find deterministic seed for setting {setting!r}")


def _retain_bytes(
    out_dir: Path,
    relative: str,
    data: bytes,
    records: dict[str, dict[str, Any]],
    *,
    kind: str,
) -> None:
    path = out_dir / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    records[relative] = {
        "sha256": _sha256_bytes(data),
        "bytes": len(data),
        "kind": kind,
    }


def _retain_json(
    out_dir: Path,
    relative: str,
    value: Any,
    records: dict[str, dict[str, Any]],
    *,
    kind: str,
) -> None:
    data = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    _retain_bytes(out_dir, relative, data, records, kind=kind)


def build_evidence(
    *,
    out_dir: Path,
    start_seed: int = 0,
    demo_count: int = 4,
    query_count: int = 4,
) -> dict[str, Any]:
    """Verify every setting in Racket and materialize private/public evidence."""
    out_dir = Path(out_dir).resolve()
    if out_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing evidence: {out_dir}")
    PROTOTYPE._validate_seed(start_seed)
    PROTOTYPE._validate_count("demo_count", demo_count)
    PROTOTYPE._validate_count("query_count", query_count)
    out_dir.mkdir(parents=True)

    programs = {
        setting: PROTOTYPE.program_for(setting)
        for setting in PROTOTYPE.ALLOWED_SETTINGS
    }
    if programs[PROTOTYPE.DEFAULT_SETTING] != PROTOTYPE.canonical_program():
        raise AssertionError("default setting is not exact canonical Racket source")

    seeds: dict[str, int] = {}
    cursor = start_seed
    for setting in PROTOTYPE.ALLOWED_SETTINGS:
        seed = seed_for(setting, cursor)
        seeds[setting] = seed
        cursor = seed + 1

    episodes = {
        setting: PROTOTYPE.build_episode(
            seeds[setting],
            setting=setting,
            demo_count=demo_count,
            query_count=query_count,
        )
        for setting in PROTOTYPE.ALLOWED_SETTINGS
    }

    bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
    runtime_identity = bridge.runtime_identity
    application_count = 0
    setting_rows: dict[str, dict[str, Any]] = {}
    all_exact = True
    all_sensitive = True
    all_demo_identifying = True
    all_query_sensitive = True
    disagreement_input: list[list[int]] | None = None
    disagreement_outputs: dict[str, list[list[int]]] | None = None
    try:
        rule_names: dict[str, str] = {}
        for index, setting in enumerate(PROTOTYPE.ALLOWED_SETTINGS):
            name = f"__output_transform_rule_{index}"
            bridge.eval_text(
                f"(define {name} {_callable_rule(programs[setting])})"
            )
            rule_names[setting] = name

        for setting in PROTOTYPE.ALLOWED_SETTINGS:
            episode = episodes[setting]
            pair_rows = []
            pairs = [
                (split, index, pair)
                for split in ("train", "test")
                for index, pair in enumerate(episode[split])
            ]
            demo_refutations = {
                rival: 0
                for rival in PROTOTYPE.ALLOWED_SETTINGS
                if rival != setting
            }
            query_sensitive = True
            for global_index, (split, split_index, pair) in enumerate(pairs):
                grid_name = _grid_symbol(
                    pair["input"], f"{setting}_{global_index}"
                )
                bridge.define_grid(grid_name, pair["input"])
                outputs: dict[str, list[list[int]]] = {}
                output_rows: dict[str, dict[str, Any]] = {}
                for candidate in PROTOTYPE.ALLOWED_SETTINGS:
                    actual = bridge.eval_text(
                        f"({rule_names[candidate]} {grid_name})"
                    )
                    application_count += 1
                    python_output = PROTOTYPE.apply_python(
                        pair["input"], candidate
                    )
                    exact = actual == python_output
                    all_exact = all_exact and exact
                    outputs[candidate] = actual
                    output_rows[candidate] = {
                        "sha256": _sha256_json(actual),
                        "racket_python_exact": exact,
                    }

                pairwise = len(
                    {_sha256_json(value) for value in outputs.values()}
                ) == len(PROTOTYPE.ALLOWED_SETTINGS)
                all_sensitive = all_sensitive and pairwise
                selected_exact = outputs[setting] == pair["output"]
                all_exact = all_exact and selected_exact
                for rival in demo_refutations:
                    if split == "train" and outputs[rival] != pair["output"]:
                        demo_refutations[rival] += 1
                if split == "test":
                    query_sensitive = query_sensitive and pairwise

                pair_rows.append(
                    {
                        "split": split,
                        "index": split_index,
                        "input_sha256": _sha256_json(pair["input"]),
                        "stored_output_sha256": _sha256_json(pair["output"]),
                        "selected_racket_matches_stored": selected_exact,
                        "outputs": output_rows,
                        "settings_pairwise_distinct": pairwise,
                    }
                )
                if disagreement_input is None:
                    disagreement_input = pair["input"]
                    disagreement_outputs = outputs

            demos_identify = all(value > 0 for value in demo_refutations.values())
            all_demo_identifying = all_demo_identifying and demos_identify
            all_query_sensitive = all_query_sensitive and query_sensitive
            setting_rows[setting] = {
                "seed": seeds[setting],
                "program_sha256": _sha256_bytes(
                    programs[setting].encode("utf-8")
                ),
                "program_exact_canonical": (
                    setting == PROTOTYPE.DEFAULT_SETTING
                    and programs[setting] == PROTOTYPE.canonical_program()
                ),
                "demo_rival_refutations": demo_refutations,
                "demos_identify_setting": demos_identify,
                "queries_setting_sensitive": query_sensitive,
                "pairs": pair_rows,
            }
    finally:
        bridge.shutdown()

    if disagreement_input is None or disagreement_outputs is None:
        raise AssertionError("no retained input available for disagreement evidence")

    file_records: dict[str, dict[str, Any]] = {}
    public_map: dict[str, dict[str, Any]] = {}
    public_exports = prepare_public_exports(episodes)
    for row in public_exports:
        setting = row["setting"]
        episode = episodes[setting]
        rule_relative = f"private/rules/output-transform-{setting}.rkt"
        episode_relative = f"private/episode-{setting}.json"
        public_relative = f"public/{row['filename']}"
        _retain_bytes(
            out_dir,
            rule_relative,
            (programs[setting] + "\n").encode("utf-8"),
            file_records,
            kind="private_exact_racket_program",
        )
        _retain_json(
            out_dir,
            episode_relative,
            episode,
            file_records,
            kind="private_labeled_episode",
        )
        _retain_bytes(
            out_dir,
            public_relative,
            row["visible_bytes"],
            file_records,
            kind="public_answer_free_challenge",
        )
        public_map[row["filename"]] = {
            "setting": setting,
            "seed": seeds[setting],
            "visible_bytes_sha256": _sha256_bytes(row["visible_bytes"]),
        }
        setting_rows[setting].update(
            {
                "private_rule": rule_relative,
                "private_episode": episode_relative,
                "public_challenge": public_relative,
            }
        )

    disagreement = {
        "schema": "5d1263287a4f-output-transform-disagreement-v1",
        "input": disagreement_input,
        "input_sha256": _sha256_json(disagreement_input),
        "outputs": disagreement_outputs,
        "output_sha256": {
            setting: _sha256_json(output)
            for setting, output in disagreement_outputs.items()
        },
        "pairwise_distinct": len(
            {_sha256_json(value) for value in disagreement_outputs.values()}
        ) == len(PROTOTYPE.ALLOWED_SETTINGS),
    }
    _retain_json(
        out_dir,
        "private/same-input-disagreement.json",
        disagreement,
        file_records,
        kind="private_same_input_counterfactual",
    )
    _retain_json(
        out_dir,
        "private/public-name-map.json",
        public_map,
        file_records,
        kind="private_public_setting_map",
    )

    source_paths = {
        "prototype.py": HERE / "prototype.py",
        "verify.py": HERE / "verify.py",
        "production_generator.py": Path(PROTOTYPE.GENERATOR_PATH),
    }
    readme = HERE / "README.md"
    if readme.is_file():
        source_paths["README.md"] = readme

    report = {
        "schema": REPORT_SCHEMA,
        "status": "passed" if all(
            (
                all_exact,
                all_sensitive,
                all_demo_identifying,
                all_query_sensitive,
                disagreement["pairwise_distinct"],
            )
        ) else "failed",
        "scope": "proposed task-local prototype; canonical production authority unchanged",
        "task_id": PROTOTYPE.TASK_ID,
        "parameter": {
            "name": PROTOTYPE.PARAMETER_NAME,
            "allowed_values": list(PROTOTYPE.ALLOWED_SETTINGS),
            "original_default": PROTOTYPE.DEFAULT_SETTING,
            "selection_scope": "once per complete episode",
            "input_constraints": list(PROTOTYPE.INPUT_CONSTRAINTS),
        },
        "counts": {
            "settings": len(PROTOTYPE.ALLOWED_SETTINGS),
            "episodes": len(episodes),
            "demonstrations_per_episode": demo_count,
            "queries_per_episode": query_count,
            "racket_program_applications": application_count,
        },
        "settings": setting_rows,
        "public_batch": [
            {
                "public_id": row["public_id"],
                "filename": row["filename"],
                "public_challenge": f"public/{row['filename']}",
            }
            for row in public_exports
        ],
        "all_racket_exact": all_exact,
        "all_inputs_pairwise_setting_sensitive": all_sensitive,
        "all_demos_identify_setting": all_demo_identifying,
        "all_queries_setting_sensitive": all_query_sensitive,
        "public_filename_policy": (
            "challenge-<sha256 of exact visible demos and query inputs>.json; "
            "independent of setting, seed, program and query answers"
        ),
        "runtime_identity": runtime_identity,
        "source_hashes": {
            name: _sha256_bytes(path.read_bytes())
            for name, path in source_paths.items()
        },
        "limitations": [
            "Evidence covers one retained episode per setting, not all seeds.",
            "The extension is proposed and task-local; it is not catalog approval.",
            "Only the output orientation varies; production input semantics stay fixed.",
        ],
    }
    _retain_json(
        out_dir,
        "report.json",
        report,
        file_records,
        kind="verification_report",
    )

    manifest = {
        "schema": "5d1263287a4f-output-transform-manifest-v1",
        "status": report["status"],
        "task_id": PROTOTYPE.TASK_ID,
        "public_order": [row["filename"] for row in public_exports],
        "files": file_records,
    }
    _write_json(out_dir / "manifest.json", manifest)
    if report["status"] != "passed":
        raise AssertionError("Racket-backed evidence did not satisfy all checks")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--start-seed", type=int, default=0)
    parser.add_argument("--demo-count", type=int, default=4)
    parser.add_argument("--query-count", type=int, default=4)
    args = parser.parse_args(argv)
    report = build_evidence(
        out_dir=args.out,
        start_seed=args.start_seed,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "out": str(args.out),
                "settings": len(report["settings"]),
                "queries_per_episode": report["counts"]["queries_per_episode"],
                "racket_program_applications": report["counts"][
                    "racket_program_applications"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
