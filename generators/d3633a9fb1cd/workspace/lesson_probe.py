#!/usr/bin/env python3
"""Source-bound lesson audit for d3633a9fb1cd.

Builds the same 3-demo + 1-query lessons used by the semantic gate through
``puzzle_generators.runner.run_one`` and the canonical Racket authority.  It
scores every rival declared by the generator, records unique-input counts and
observable-axis limits, and retains the exact deterministic sampler policy.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TASK = "d3633a9fb1cd"
LESSON_STRIDE = 11
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "shared" / "runtime"))
# The runtime keeps legacy imports such as ``scripts.comment_solutions`` while
# this review packet stores those modules in shared/tools.  Bind a namespace
# package explicitly so this standalone probe uses the packet's exact sources.
_scripts = types.ModuleType("scripts")
_scripts.__path__ = [str(ROOT / "shared" / "tools")]
sys.modules.setdefault("scripts", _scripts)

from reference_probe import canonical, canonical_pairs, load_generator  # noqa: E402


def pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK}:lesson:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def grid_hash(grid) -> str:
    blob = json.dumps(grid, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _axis_summary(rows):
    result = {}
    for name in sorted(rows[0]) if rows else []:
        values = [row[name] for row in rows]
        if all(type(value) is int for value in values):
            result[name] = {
                "min": min(values),
                "max": max(values),
                "counts": {str(key): value for key, value in sorted(Counter(values).items())},
            }
        else:
            result[name] = {
                "counts": {str(key): value for key, value in sorted(Counter(values).items(), key=lambda x: str(x[0]))}
            }
    return result


def run(count_per_band: int = 100, n_demos: int = 3) -> dict:
    from puzzle_generators import runner

    generator_path = ROOT / "generators" / TASK / "generator.py"
    gen = load_generator(generator_path)
    row = canonical()
    rule_source = row.get("program_solution")
    if not isinstance(rule_source, str) or not rule_source.strip():
        raise RuntimeError("canonical row has no program_solution")
    rule_file = "shared/data/canonical/puzzles.jsonl:program_solution"
    bundle = runner.GeneratorBundle(
        task_id=TASK,
        rule_task_id=TASK,
        rule_source=rule_source,
        rule_callable_text=runner.wrap_rule(rule_source),
        rule_file=rule_file,
        generator_module=gen,
        allow_identity_output=bool(getattr(gen, "ALLOW_IDENTITY_OUTPUT", False)),
        kind="per_puzzle",
    )
    bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)

    competitor_names = sorted(getattr(gen, "LESSON_COMPETITORS", {}))
    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", {})
    shortcut_checks = {}
    for name, fn in shortcuts.items():
        matches = []
        for index, pair in enumerate(canonical_pairs()):
            try:
                matches.append(fn(deepcopy(pair["input"])) == pair["output"])
            except Exception:
                matches.append(False)
        shortcut_checks[name] = {
            "matches_all": all(matches),
            "matches": sum(matches),
            "canonical_pairs": len(matches),
        }

    report = {
        "schema": "d3633a9fb1cd-lesson-audit-v1",
        "task_id": TASK,
        "generator_path": str(generator_path.relative_to(ROOT)),
        "generator_sha256": source_hash(generator_path),
        "generator_version": gen.VERSION,
        "declared_rule_hash": gen.RULE_HASH,
        "sampler": {
            "bands": ["easy", "medium", "hard"],
            "lessons_per_band": count_per_band,
            "n_demos": n_demos,
            "n_queries": 1,
            "seed": "sha256('profile-floor:v1:TASK:lesson:BAND:INDEX')[:12] as int",
            "sample_index": f"lesson_index * {LESSON_STRIDE}",
            "pair_indices": "runner.run_one sequential indices with its documented rejection slack",
            "outputs": "canonical Racket authority through one persistent runner bridge",
        },
        "declared_competitors": competitor_names,
        "canonical_shortcuts": shortcut_checks,
        "bands": {},
        "errors": [],
    }

    try:
        for band in ("easy", "medium", "hard"):
            unique_inputs = set()
            unique_lessons = set()
            axis_rows = []
            witness_input_hits = Counter()
            witness_lesson_hits = Counter()
            competitor_stats = {
                name: Counter(
                    lessons=0,
                    survived_demos=0,
                    refuted_by_demos=0,
                    survived_and_query_match=0,
                    survived_but_query_wrong=0,
                    errors=0,
                )
                for name in competitor_names
            }
            complete_refutation = 0
            lessons_built = 0
            pair_count = 0

            for lesson_index in range(count_per_band):
                seed = pinned_seed(band, lesson_index)
                sample_index = lesson_index * LESSON_STRIDE
                try:
                    instance = runner.run_one(
                        TASK,
                        seed=seed,
                        sample_index=sample_index,
                        n_train=n_demos,
                        n_test=1,
                        bundle=bundle,
                        bridge=bridge,
                        fn_name=fn_name,
                        difficulty=band,
                    )
                except Exception as exc:
                    report["errors"].append(
                        f"band={band} lesson={lesson_index} seed={seed} sample_index={sample_index}: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    continue

                lessons_built += 1
                demos = instance["train"]
                query = instance["test"][0]
                pairs = demos + [query]
                pair_count += len(pairs)
                lesson_hashes = []
                lesson_witnesses = set()
                for pair in pairs:
                    digest = grid_hash(pair["input"])
                    unique_inputs.add(digest)
                    lesson_hashes.append(digest)
                    axes = gen.observe_overrides(pair["input"])
                    axis_rows.append(axes)
                    for name, predicate in gen.SEMANTIC_WITNESSES.items():
                        try:
                            if predicate(deepcopy(pair["input"])):
                                witness_input_hits[name] += 1
                                lesson_witnesses.add(name)
                        except Exception as exc:
                            report["errors"].append(
                                f"witness={name} band={band} lesson={lesson_index}: "
                                f"{type(exc).__name__}: {exc}"
                            )
                unique_lessons.add(tuple(lesson_hashes))
                for name in lesson_witnesses:
                    witness_lesson_hits[name] += 1

                all_refuted = True
                for name, competitor in gen.LESSON_COMPETITORS.items():
                    stats = competitor_stats[name]
                    stats["lessons"] += 1
                    try:
                        survives = all(
                            competitor(deepcopy(pair["input"])) == pair["output"]
                            for pair in demos
                        )
                    except Exception:
                        stats["errors"] += 1
                        survives = False
                    if survives:
                        all_refuted = False
                        stats["survived_demos"] += 1
                        try:
                            query_match = competitor(deepcopy(query["input"])) == query["output"]
                        except Exception:
                            stats["errors"] += 1
                            query_match = False
                        stats[
                            "survived_and_query_match" if query_match else "survived_but_query_wrong"
                        ] += 1
                    else:
                        stats["refuted_by_demos"] += 1
                complete_refutation += all_refuted

            report["bands"][band] = {
                "lessons_requested": count_per_band,
                "lessons_built": lessons_built,
                "pairs": pair_count,
                "unique_inputs": len(unique_inputs),
                "unique_lessons": len(unique_lessons),
                "observable_axes": _axis_summary(axis_rows),
                "witness_input_hits": dict(witness_input_hits),
                "witness_lesson_hits": dict(witness_lesson_hits),
                "lessons_refuting_every_declared_competitor": complete_refutation,
                "competitors": {name: dict(stats) for name, stats in competitor_stats.items()},
            }
    finally:
        bridge.close()

    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count-per-band", type=int, default=100)
    parser.add_argument("--n-demos", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.count_per_band, args.n_demos)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": str(args.out),
        "generator_sha256": report["generator_sha256"],
        "errors": len(report["errors"]),
        "bands": {
            band: {
                "lessons": row["lessons_built"],
                "unique_inputs": row["unique_inputs"],
                "all_competitors_refuted": row["lessons_refuting_every_declared_competitor"],
            }
            for band, row in report["bands"].items()
        },
    }, indent=2))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
