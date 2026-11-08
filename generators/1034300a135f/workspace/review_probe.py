#!/usr/bin/env python3
"""Portable, source-bound verification probe for generator 1034300a135f.

This is intentionally independent of the inherited frozen pytest fixture.  It
loads the selected generator from the current repository/runtime, exercises the
repair contract, and writes one machine-readable receipt.  It does not replace
the official battery or grant approval; it preserves focused evidence when an
unrelated frozen test fixture blocks pytest collection.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import traceback
from typing import Any, Callable

from reviewer_support import find_root, load_selected_generator


TASK_ID = "1034300a135f"
PROTOTYPE_LIBRARY_PATH = (
    f"generators/{TASK_ID}/workspace/parametric/prototype.py"
)


def _expect_raises(
    error_type: type[BaseException],
    text: str,
    call: Callable[[], Any],
) -> None:
    try:
        call()
    except error_type as exc:
        if text not in str(exc):
            raise AssertionError(
                f"expected {error_type.__name__} containing {text!r}, got {exc!r}"
            ) from exc
    except BaseException as exc:
        raise AssertionError(
            f"expected {error_type.__name__}, got {type(exc).__name__}: {exc}"
        ) from exc
    else:
        raise AssertionError(f"expected {error_type.__name__}, no exception raised")


def _resolve_manifest_file(root: Path, library_path: str, fallback: Path) -> Path:
    manifest = root / "RUNTIME_MANIFEST.json"
    if not manifest.is_file():
        return fallback
    rows = json.loads(manifest.read_text(encoding="utf-8")).get("files", [])
    matches = [row for row in rows if row.get("library_path") == library_path]
    # Prefer the execution-layout copy over a repository mirror, as the public
    # task-test harness does.
    matches.sort(key=lambda row: row.get("runtime_path") == library_path)
    if not matches:
        return fallback
    relative = Path(matches[0]["runtime_path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe runtime path for {library_path}: {relative}")
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"runtime path escapes root: {resolved}")
    return resolved


def _load_prototype(root: Path, generator_source: Path):
    fallback = generator_source.parent / "workspace/parametric/prototype.py"
    path = _resolve_manifest_file(root, PROTOTYPE_LIBRARY_PATH, fallback)
    if not path.is_file():
        raise FileNotFoundError(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(
        f"_review_probe_parametric_{digest}", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path, digest


def _pair(generator, grid: list[list[int]]) -> dict[str, Any]:
    return {"input": grid, "output": generator.rule_mirror(grid)}


def _check_public_contract(generator) -> dict[str, int]:
    bad_scalars = [True, False, 1.0, 1.75, "1", None]
    calls = 0
    for bad in bad_scalars:
        _expect_raises(TypeError, "seed", lambda bad=bad: generator.generate(bad, 0))
        _expect_raises(
            TypeError, "seed", lambda bad=bad: generator.schedule_profile(bad, 0)
        )
        _expect_raises(
            TypeError,
            "sample_index",
            lambda bad=bad: generator.generate(0, bad),
        )
        _expect_raises(
            TypeError,
            "sample_index",
            lambda bad=bad: generator.schedule_profile(0, bad),
        )
        calls += 4
    _expect_raises(ValueError, "nonnegative", lambda: generator.generate(0, -1))
    _expect_raises(
        ValueError, "nonnegative", lambda: generator.schedule_profile(0, -1)
    )
    calls += 2
    for bad in [True, False, 0, 1.0, "invalid", []]:
        _expect_raises(
            ValueError,
            "difficulty",
            lambda bad=bad: generator.generate(0, 0, difficulty=bad),
        )
        _expect_raises(
            ValueError,
            "difficulty",
            lambda bad=bad: generator.schedule_profile(0, 0, difficulty=bad),
        )
        calls += 2
    return {"rejection_calls": calls}


def _check_schedule(generator) -> dict[str, Any]:
    period = generator.LESSON_SCHEDULE_PERIOD
    assert generator.EXAMPLES_NEEDED == 3
    assert period == 2 * (len(generator.SCENE_PROFILES) - 1)
    assert set(generator.SCHEDULE_PROFILES) == set(generator.SCENE_PROFILES)
    scheduled = [
        generator.schedule_profile(17, index, difficulty="medium")
        for index in range(period)
    ]
    assert set(scheduled) == set(generator.SCENE_PROFILES)
    assert scheduled.count("teaching_combined") == period // 2
    windows = 0
    rotations = 0
    for start in range(period):
        profiles = [
            generator.schedule_profile(17, start + offset, difficulty="medium")
            for offset in range(generator.EXAMPLES_NEEDED + 1)
        ]
        windows += 1
        for held_out in range(len(profiles)):
            demos = profiles[:held_out] + profiles[held_out + 1 :]
            assert "teaching_combined" in demos, (start, held_out, profiles)
            rotations += 1
    return {
        "period": period,
        "profiles": len(set(scheduled)),
        "teaching_slots": scheduled.count("teaching_combined"),
        "windows": windows,
        "rotations": rotations,
    }


def _check_generation_and_teaching(generator) -> dict[str, int]:
    generated = 0
    overrides = 0
    teaching = 0
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(generator.LESSON_SCHEDULE_PERIOD):
            grid = generator.generate(29, index, difficulty=difficulty)
            assert generator.observe_overrides(grid) == {
                "scene_profile": generator.schedule_profile(29, index, difficulty)
            }
            generated += 1
        for profile in generator.SCENE_PROFILES:
            grid = generator.generate(
                29, 11, difficulty=difficulty, scene_profile=profile
            )
            assert generator.observe_overrides(grid) == {"scene_profile": profile}
            overrides += 1
        for seed in range(24):
            grid = generator.generate(
                seed,
                seed * 31,
                difficulty=difficulty,
                scene_profile="teaching_combined",
            )
            assert generator.self_check(grid) == []
            assert generator.strict_canonical_like(grid) == []
            truth = generator.rule_mirror(grid)
            assert all(
                predicate(grid)
                for predicate in generator.SEMANTIC_WITNESSES.values()
            )
            assert all(
                rival(grid) != truth for rival in generator.SEMANTIC_RIVALS.values()
            )
            facts = generator._analysis(grid)["facts"]
            assert any(
                marker["color"] != 0
                and truth[marker["row"]][marker["col"]] != marker["color"]
                for marker in facts["markers"]
            )
            teaching += 1
    return {
        "scheduled_instances": generated,
        "exact_overrides": overrides,
        "teaching_instances": teaching,
        "rivals_per_teaching_instance": len(generator.SEMANTIC_RIVALS),
    }


def _check_witnesses_and_canonical_shortcuts(generator) -> dict[str, Any]:
    assert set(generator.WITNESS_RIVALS) == set(generator.SEMANTIC_WITNESSES)
    seen = {name: 0 for name in generator.SEMANTIC_WITNESSES}
    generated = 0
    for difficulty in ("easy", "medium", "hard"):
        for index in range(generator.LESSON_SCHEDULE_PERIOD * 2):
            grid = generator.generate(53, index, difficulty=difficulty)
            truth = generator.rule_mirror(grid)
            generated += 1
            for witness_name, predicate in generator.SEMANTIC_WITNESSES.items():
                if predicate(grid):
                    seen[witness_name] += 1
                    for rival_name in generator.WITNESS_RIVALS[witness_name]:
                        assert generator.SEMANTIC_RIVALS[rival_name](grid) != truth
    assert all(seen.values()), seen

    fits = 0
    for profile in generator.PUBLIC_PROFILES:
        grid = generator.generate(7, 13, scene_profile=profile)
        truth = generator.rule_mirror(grid)
        for name, shortcut in generator.CANONICAL_SHORTCUTS.items():
            assert shortcut(grid) == truth, (profile, name)
            fits += 1
    return {
        "support_instances": generated,
        "witness_hits": seen,
        "canonical_shortcut_exact_fits": fits,
    }


def _check_lessons(generator) -> dict[str, int]:
    windows = 0
    rotations = 0
    rival_demo_refutations = 0
    for difficulty in ("easy", "medium", "hard"):
        for start in range(generator.LESSON_SCHEDULE_PERIOD):
            pairs = [
                _pair(
                    generator,
                    generator.generate(71, start + offset, difficulty=difficulty),
                )
                for offset in range(generator.EXAMPLES_NEEDED + 1)
            ]
            windows += 1
            for query_index in range(len(pairs)):
                demos = [
                    pair for index, pair in enumerate(pairs) if index != query_index
                ]
                query = pairs[query_index]
                assert generator.lesson_identifiable(demos, query) == [], (
                    difficulty,
                    start,
                    query_index,
                )
                rotations += 1
                for rival_name, rival in generator.LESSON_COMPETITORS.items():
                    assert any(
                        rival(pair["input"]) != pair["output"] for pair in demos
                    ), (difficulty, start, query_index, rival_name)
                    rival_demo_refutations += 1

    teaching = _pair(
        generator,
        generator.generate(5, 0, scene_profile="teaching_combined"),
    )
    ordinary = [
        _pair(
            generator,
            generator.generate(5, 1 + 2 * index, scene_profile=profile),
        )
        for index, profile in enumerate(generator.PUBLIC_PROFILES[:3])
    ]
    rival_name = "reverse_equal_distance_ties"
    rival = generator.LESSON_COMPETITORS[rival_name]
    assert all(rival(pair["input"]) == pair["output"] for pair in ordinary)
    assert rival(teaching["input"]) != teaching["output"]
    assert any(
        rival_name in reason
        for reason in generator.lesson_identifiable(ordinary, teaching)
    )
    return {
        "windows": windows,
        "rotations": rotations,
        "rival_demo_refutations": rival_demo_refutations,
        "negative_control_rivals_named": 1,
    }


def _check_prototype(root: Path, source: Path, generator) -> dict[str, Any]:
    prototype, path, digest = _load_prototype(root, source)
    assert prototype.PARAMETER_NAME == "marker_order"
    assert prototype.ALLOWED_MARKER_ORDERS == ("near_to_far", "far_to_near")
    assert prototype.DEFAULT_MARKER_ORDER == "near_to_far"
    assert {
        prototype.choose_parameters(seed)[prototype.PARAMETER_NAME]
        for seed in range(8)
    } == {"near_to_far", "far_to_near"}
    assert prototype.choose_parameters(17) == prototype.choose_parameters(17)
    _expect_raises(TypeError, "episode seed", lambda: prototype.choose_parameters(True))

    seen: set[tuple[tuple[int, ...], ...]] = set()
    for seed in range(6):
        for pair_index in range(3):
            grid = prototype.build_input(seed, pair_index)
            seen.add(tuple(map(tuple, grid)))
            assert generator.self_check(grid) == []
            near = prototype.python_reference(grid, marker_order="near_to_far")
            far = prototype.python_reference(grid, marker_order="far_to_near")
            assert near == generator.rule_mirror(grid)
            assert near != far
    assert len(seen) == 18

    episodes = 0
    for marker_order in prototype.ALLOWED_MARKER_ORDERS:
        episode = prototype.build_episode(19, marker_order=marker_order)
        public = prototype.public_challenge(episode)
        assert episode["parameter"] == {"marker_order": marker_order}
        assert set(public) == {"schema", "train", "test"}
        assert len(public["train"]) == 2
        assert len(public["test"]) == 1
        assert set(public["test"][0]) == {"input"}
        assert "parameter" not in repr(public)
        assert "marker_order" not in repr(public)
        other = next(
            value
            for value in prototype.ALLOWED_MARKER_ORDERS
            if value != marker_order
        )
        assert all(
            prototype.python_reference(pair["input"], marker_order=other)
            != pair["output"]
            for pair in episode["train"]
        )
        episodes += 1

    programs = {
        order: prototype.racket_program(order)
        for order in prototype.ALLOWED_MARKER_ORDERS
    }
    assert programs["near_to_far"] != programs["far_to_near"]
    for order, program in programs.items():
        assert f"MARKER-ORDER '{order}" in program
        assert prototype.rule_sha256(order) == prototype.sha256_text(program)
    return {
        "prototype_path": str(path),
        "prototype_sha256": digest,
        "distinct_shared_inputs": len(seen),
        "episode_settings_checked": episodes,
        "racket_program_sha256": {
            order: prototype.rule_sha256(order)
            for order in prototype.ALLOWED_MARKER_ORDERS
        },
    }


def run_probe() -> dict[str, Any]:
    root = find_root(__file__)
    generator, source, source_sha = load_selected_generator(TASK_ID, root=root)
    checks: list[dict[str, Any]] = []

    def run(name: str, operation: Callable[[], dict[str, Any]]) -> None:
        started = time.monotonic()
        try:
            details = operation()
        except BaseException as exc:
            checks.append(
                {
                    "name": name,
                    "status": "fail",
                    "elapsed_seconds": round(time.monotonic() - started, 6),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )
        else:
            checks.append(
                {
                    "name": name,
                    "status": "pass",
                    "elapsed_seconds": round(time.monotonic() - started, 6),
                    "details": details,
                }
            )

    run("public_call_contract", lambda: _check_public_contract(generator))
    run("rotation_safe_schedule", lambda: _check_schedule(generator))
    run(
        "generation_profiles_and_combined_teaching",
        lambda: _check_generation_and_teaching(generator),
    )
    run(
        "witnesses_and_canonical_shortcuts",
        lambda: _check_witnesses_and_canonical_shortcuts(generator),
    )
    run("rotated_lesson_identifiability", lambda: _check_lessons(generator))
    run("episode_parameter_prototype", lambda: _check_prototype(root, source, generator))

    failed = [row for row in checks if row["status"] != "pass"]
    return {
        "schema": "arcpuzzles-focused-review-probe-v1",
        "task_id": TASK_ID,
        "status": "fail" if failed else "pass",
        "selected_generator_path": str(source),
        "selected_generator_sha256": source_sha,
        "canonical_rule_hash": generator.RULE_HASH,
        "generator_version": generator.VERSION,
        "checks": checks,
        "summary": {
            "passed": len(checks) - len(failed),
            "failed": len(failed),
            "total": len(checks),
        },
        "scope_note": (
            "Focused source-bound evidence independent of the inherited frozen "
            "pytest fixture; it does not replace the official battery or confer approval."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run_probe()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "summary": result["summary"],
        "selected_generator_sha256": result["selected_generator_sha256"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
