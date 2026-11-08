#!/usr/bin/env python3
"""Protected-Racket verification for the current 78ab57735469 native family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

HERE = Path(__file__).resolve()
ROOT = next(
    parent
    for parent in HERE.parents
    if (parent / "shared" / "runtime" / "arc_repl" / "racket_bridge.py").is_file()
)
for path in (ROOT / "shared" / "runtime", ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.generic.concepts.extraction import _program_body  # noqa: E402

TASK_ID = "78ab57735469"
REPORT_SCHEMA = "78ab57735469-parametric-component-v2"


def _load_prototype():
    path = HERE.with_name("prototype.py")
    name = "_arc_78_verify_proto_" + hashlib.sha256(str(path).encode()).hexdigest()
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _validated_settings(proto: Any, settings: Iterable[tuple[str, str, str]] | None) -> list[tuple[str, str, str]]:
    selected = list(proto.SETTINGS if settings is None else settings)
    if not selected:
        raise ValueError("settings must not be empty")
    normalized = [proto._setting(*setting) for setting in selected]
    if len(normalized) != len(set(normalized)):
        raise ValueError("settings must be unique")
    return normalized


def _racket_outputs(bridge: RacketBridge, program: str, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    body = _program_body(program)
    outputs: list[list[list[int]]] = []
    for grid in grids:
        bridge.define_grid("g", grid)
        outputs.append(bridge.eval_text(body))
    return outputs


def build_report(
    *,
    seed_base: int = 20261025,
    artifact_dir: Path | str,
    settings: Iterable[tuple[str, str, str]] | None = None,
) -> dict[str, Any]:
    """Replay current programs and labels through protected Racket.

    ``settings`` exists for focused regression tests. The CLI verifies all eight
    native settings by default.
    """
    if type(seed_base) is not int or seed_base < 0:
        raise ValueError("seed_base must be a nonnegative exact integer")
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    proto = _load_prototype()
    selected = _validated_settings(proto, settings)
    rows: list[dict[str, Any]] = []
    pair_count = 0
    max_height = max_width = 0

    with RacketBridge() as bridge:
        runtime = bridge.runtime_identity
        if not runtime.get("protected"):
            raise RuntimeError("Racket runtime did not pass its protection canary")
        for offset, setting in enumerate(selected):
            seed = seed_base + offset
            episode = proto.generate_episode(seed, *setting, demos=3, queries=4)
            pairs = episode["train"] + episode["test"]
            grids = [pair["input"] for pair in pairs]
            expected = [pair["output"] for pair in pairs]
            program = proto.program_for(*setting)
            actual = _racket_outputs(bridge, program, grids)
            exact = actual == expected
            certificate = proto.teaching_certificate(episode, setting)
            public = proto.public_turn(episode, 0)
            one_query = proto.generate_episode(seed, *setting, demos=3, queries=1)
            prefix_stable = public == proto.public_turn(one_query, 0)
            masked = (
                set(public) == {"train", "test"}
                and len(public["test"]) == 1
                and set(public["test"][0]) == {"input"}
                and all(set(pair) == {"input", "output"} for pair in public["train"])
            )
            for grid in actual:
                max_height = max(max_height, len(grid))
                max_width = max(max_width, len(grid[0]))
            pair_count += len(pairs)
            rows.append(
                {
                    "setting": {
                        "row_flip_phase": setting[0],
                        "column_flip_phase": setting[1],
                        "finish": setting[2],
                    },
                    "seed": seed,
                    "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                    "episode_sha256": _sha_json(episode),
                    "pairs": len(pairs),
                    "racket_exact": exact,
                    "public_masked": masked,
                    "first_turn_prefix_stable": prefix_stable,
                    "teaching": certificate,
                }
            )

    passed = all(
        row["racket_exact"]
        and row["public_masked"]
        and row["first_turn_prefix_stable"]
        and not row["teaching"]["surviving_rivals"]
        and not row["teaching"]["query_changing_survivors"]
        for row in rows
    )
    report = {
        "schema": REPORT_SCHEMA,
        "task_id": TASK_ID,
        "status": "passed" if passed else "failed",
        "protected_racket": bool(runtime.get("protected")),
        "runtime": runtime,
        "settings_checked": len(rows),
        "pairs_checked": pair_count,
        "max_output_shape": [max_height, max_width],
        "settings": rows,
        "limits": [
            "Bounded exact replay; this is not owner qualification or acceptance.",
            "The CLI default covers all eight current settings at three demonstrations and four queries.",
        ],
    }
    (artifact_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if not passed:
        raise AssertionError("current parametric verifier found a mismatch")
    return report


def _parse_setting(value: str) -> tuple[str, str, str]:
    parts = tuple(value.split(","))
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("setting must be ROW,COLUMN,FINISH")
    return parts  # validated against the prototype in build_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-base", type=int, default=20261025)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument(
        "--setting",
        action="append",
        type=_parse_setting,
        help="focused ROW,COLUMN,FINISH setting; repeatable (default: all eight)",
    )
    args = parser.parse_args(argv)
    report = build_report(
        seed_base=args.seed_base,
        artifact_dir=args.artifact_dir,
        settings=args.setting,
    )
    print(json.dumps({key: report[key] for key in ("status", "settings_checked", "pairs_checked", "max_output_shape")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
