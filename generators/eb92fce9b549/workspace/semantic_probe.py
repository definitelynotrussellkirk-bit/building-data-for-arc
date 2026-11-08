#!/usr/bin/env python3
"""Source-bound long-run lesson census for eb92fce9b549.

The official semantic gate intentionally uses a small smoke sample.  This probe
runs the *actual shared runner and Racket authority* for at least 100 lessons
per difficulty band, measures whether the declared cell-count rival survives
any three-demo lesson, and records uniqueness, profile coverage, witness rates,
and the exact sampler.  It is reusable after later generator edits because the
report is bound to the generator and probe SHA-256 digests.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
from typing import Any

HERE = Path(__file__).resolve().parent
HOME = HERE.parent
REPO = HERE.parents[2]
RUNTIME = REPO / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))
sys.path.insert(0, str(HERE))

from reference_probe import canonical_pairs, load_generator  # noqa: E402
from puzzle_generators import runner  # noqa: E402

TASK_ID = "eb92fce9b549"
BANDS = ("easy", "medium", "hard")
SEED_DOMAIN = "sha256('eb92fce9b549|semantic-probe-v1|<band>|<lesson-index>')[:8]"
SAMPLE_STRIDE = 11


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_seed(band: str, index: int) -> int:
    payload = f"{TASK_ID}|semantic-probe-v1|{band}|{index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def install_generator(gen: Any) -> None:
    """Expose the reviewed source under the runtime import path runner expects."""
    package_name = f"puzzle_generators.per_puzzle.{TASK_ID}"
    package = types.ModuleType(package_name)
    package.__path__ = []  # type: ignore[attr-defined]
    package.__package__ = package_name
    sys.modules[package_name] = package
    sys.modules[f"{package_name}.generator"] = gen
    setattr(package, "generator", gen)


def _canonical_program() -> str:
    ledger = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row.get("program_solution")
                if not isinstance(program, str) or not program.strip():
                    raise RuntimeError(f"{TASK_ID} has no canonical program_solution")
                return program.strip()
    raise KeyError(f"canonical task {TASK_ID} not found in {ledger}")


def _install_scripts_compat() -> None:
    """Expose the retained parser at the portable runtime's import name."""
    package = types.ModuleType("scripts")
    package.__path__ = []  # type: ignore[attr-defined]
    sys.modules.setdefault("scripts", package)
    module_name = "scripts.comment_solutions"
    if module_name in sys.modules:
        return
    source = REPO / "shared" / "tools" / "comment_solutions.py"
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load parser compatibility module from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    setattr(package, "comment_solutions", module)


def configure_runner() -> None:
    """Point the portable runner at this review packet's retained authority.

    ``runner._load_rule`` normally expects authority files underneath its own
    portable runtime root.  This task-local probe runs from the review repo, so
    it injects the exact canonical-ledger program while leaving all wrapping,
    bridge execution, validation, and episode materialization in the shared
    runner.
    """
    _install_scripts_compat()
    program = _canonical_program()
    runner._load_rule = lambda task_id: (
        program, "shared/data/canonical/puzzles.jsonl"
    ) if task_id == TASK_ID else (_ for _ in ()).throw(KeyError(task_id))
    runner.REJECT_DIR = HERE / "probe_rejections"


def score_pair(gen: Any, pair: dict[str, Any]) -> dict[str, Any]:
    grid = pair["input"]
    output = pair["output"]
    rival_output = gen.LESSON_COMPETITORS["cell_count_rank"](grid)
    strict_reasons = list(gen.strict_canonical_like(grid) or [])
    witness = bool(gen.SEMANTIC_WITNESSES["bbox_vs_cell_count"](grid))
    return {
        "hash": grid_hash(grid),
        "profile": profile(grid),
        "axes": gen.observe_overrides(grid),
        "strict_reasons": strict_reasons,
        "witness": witness,
        "rival_disagrees": rival_output != output,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_band < 100:
        print("warning: --per-band below the review contract's 100-lesson floor", file=sys.stderr)
    if args.per_band < 1:
        raise SystemExit("--per-band must be positive")

    generator_path = HOME / "generator.py"
    gen = load_generator(generator_path)
    install_generator(gen)
    configure_runner()

    canonical = canonical_pairs()
    canonical_rival_matches = [
        gen.CANONICAL_SHORTCUTS["cell_count_rank"](pair["input"]) == pair["output"]
        for pair in canonical
    ]

    report: dict[str, Any] = {
        "schema": "eb92fce9b549-semantic-probe-v1",
        "task_id": TASK_ID,
        "source_binding": {
            "generator_path": str(generator_path.relative_to(REPO)),
            "generator_sha256": sha256_file(generator_path),
            "generator_version": gen.VERSION,
            "rule_hash": gen.RULE_HASH,
            "probe_path": str(Path(__file__).resolve().relative_to(REPO)),
            "probe_sha256": sha256_file(Path(__file__).resolve()),
        },
        "actual_sampler": {
            "runner": "shared/runtime/puzzle_generators/runner.py::run_one",
            "authority": "selected Racket rule loaded by runner._load_bundle",
            "bands": list(BANDS),
            "lessons_per_band": args.per_band,
            "n_demos": gen.EXAMPLES_NEEDED,
            "n_queries": 1,
            "overrides": {},
            "seed_formula": SEED_DOMAIN,
            "sample_index_formula": f"lesson_index * {SAMPLE_STRIDE}",
            "pairs_within_lesson": "sequential accepted sample indices from run_one",
        },
        "domain_limits": {
            "axes": gen.AXES,
            "declared_incompatibilities": gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS,
            "strict_predicate": "generator.strict_canonical_like",
            "declared_rival": "cell_count_rank",
            "declared_witness": "bbox_vs_cell_count",
            "claim_limit": (
                "This census establishes coverage only for the sampled seed/index domain "
                "and declared rival; it is not a proof of universal induction."
            ),
        },
        "canonical_shortcut_fit": {
            "pairs": len(canonical),
            "matches": sum(canonical_rival_matches),
            "all_match": all(canonical_rival_matches),
        },
        "bands": {},
        "errors": [],
    }

    bundle = runner._load_bundle(TASK_ID)
    bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)
    all_hashes: set[str] = set()
    try:
        for band in BANDS:
            hashes: set[str] = set()
            layouts: Counter[str] = Counter()
            sizes: Counter[str] = Counter()
            counts: Counter[str] = Counter()
            colors: Counter[str] = Counter()
            profiles: Counter[str] = Counter()
            witness_pairs = 0
            rival_pair_disagreements = 0
            demo_disagreements = 0
            query_disagreements = 0
            identifiable = 0
            unidentifiable = 0
            strict_failures = 0
            lessons_materialized = 0
            first_witness: dict[str, Any] | None = None
            unidentifiable_examples: list[dict[str, Any]] = []

            for lesson_index in range(args.per_band):
                seed = stable_seed(band, lesson_index)
                sample_index = lesson_index * SAMPLE_STRIDE
                try:
                    episode = runner.run_one(
                        TASK_ID,
                        seed=seed,
                        sample_index=sample_index,
                        n_train=gen.EXAMPLES_NEEDED,
                        n_test=1,
                        bundle=bundle,
                        bridge=bridge,
                        fn_name=fn_name,
                        difficulty=band,
                    )
                except Exception as exc:
                    report["errors"].append(
                        {
                            "band": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": sample_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    continue

                lessons_materialized += 1
                demo_scores = [score_pair(gen, pair) for pair in episode["train"]]
                query_score = score_pair(gen, episode["test"][0])
                pair_scores = demo_scores + [query_score]

                for score in pair_scores:
                    hashes.add(score["hash"])
                    all_hashes.add(score["hash"])
                    profiles[str(tuple(score["profile"]))] += 1
                    axes = score["axes"]
                    layouts[str(axes["layout"])] += 1
                    sizes[str(axes["grid_size"])] += 1
                    counts[str(axes["n_objects"])] += 1
                    colors[str(axes["foreground_color"])] += 1
                    witness_pairs += int(score["witness"])
                    rival_pair_disagreements += int(score["rival_disagrees"])
                    strict_failures += int(bool(score["strict_reasons"]))
                    if score["witness"] and first_witness is None:
                        first_witness = {
                            "input_sha256": score["hash"],
                            "observed_axes": axes,
                            "profile": score["profile"],
                        }

                demo_disagreement_count = sum(score["rival_disagrees"] for score in demo_scores)
                demo_disagreements += demo_disagreement_count
                query_disagreements += int(query_score["rival_disagrees"])
                hook_reasons = list(gen.lesson_identifiable(episode["train"], episode["test"][0]) or [])
                rival_survives_demos = demo_disagreement_count == 0
                if not hook_reasons and not rival_survives_demos:
                    identifiable += 1
                else:
                    unidentifiable += 1
                    if len(unidentifiable_examples) < 8:
                        unidentifiable_examples.append(
                            {
                                "lesson_index": lesson_index,
                                "seed": seed,
                                "sample_index": sample_index,
                                "hook_reasons": hook_reasons,
                                "rival_survives_demos": rival_survives_demos,
                                "demo_hashes": [score["hash"] for score in demo_scores],
                            }
                        )

            pair_total = lessons_materialized * (gen.EXAMPLES_NEEDED + 1)
            report["bands"][band] = {
                "lessons_requested": args.per_band,
                "lessons_materialized": lessons_materialized,
                "identifiable_lessons": identifiable,
                "unidentifiable_lessons": unidentifiable,
                "pair_total": pair_total,
                "unique_inputs": len(hashes),
                "duplicate_inputs": pair_total - len(hashes),
                "strict_failures": strict_failures,
                "witness_pairs": witness_pairs,
                "witness_pair_rate": witness_pairs / pair_total if pair_total else 0.0,
                "rival_pair_disagreements": rival_pair_disagreements,
                "demo_disagreements": demo_disagreements,
                "query_disagreements": query_disagreements,
                "layout_counts": dict(sorted(layouts.items())),
                "grid_size_counts": dict(sorted(sizes.items(), key=lambda item: int(item[0]))),
                "n_object_counts": dict(sorted(counts.items(), key=lambda item: int(item[0]))),
                "foreground_color_counts": dict(sorted(colors.items(), key=lambda item: int(item[0]))),
                "profile_counts": dict(sorted(profiles.items())),
                "first_witness": first_witness,
                "unidentifiable_examples": unidentifiable_examples,
            }
    finally:
        bridge.shutdown()

    report["aggregate"] = {
        "lessons_requested": args.per_band * len(BANDS),
        "lessons_materialized": sum(row["lessons_materialized"] for row in report["bands"].values()),
        "identifiable_lessons": sum(row["identifiable_lessons"] for row in report["bands"].values()),
        "unidentifiable_lessons": sum(row["unidentifiable_lessons"] for row in report["bands"].values()),
        "pair_total": sum(row["pair_total"] for row in report["bands"].values()),
        "unique_inputs_across_bands": len(all_hashes),
        "strict_failures": sum(row["strict_failures"] for row in report["bands"].values()),
        "rival_pair_disagreements": sum(row["rival_pair_disagreements"] for row in report["bands"].values()),
        "errors": len(report["errors"]),
    }
    report["status"] = (
        "PASS"
        if report["canonical_shortcut_fit"]["all_match"]
        and not report["errors"]
        and report["aggregate"]["lessons_materialized"] == report["aggregate"]["lessons_requested"]
        and report["aggregate"]["unidentifiable_lessons"] == 0
        and report["aggregate"]["strict_failures"] == 0
        else "FAIL"
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "generator_sha256": report["source_binding"]["generator_sha256"],
        "aggregate": report["aggregate"],
        "output": str(args.out),
    }, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
