"""Replay complete lessons against the generator's *declared* rival rules.

Examples (run from the extracted packet root):
  python3 repo/generators/d01b33f4a589/workspace/lesson_probe.py \
    --library repo --seeds 256 --starts 8 --out checks/lesson-final.json
  python3 repo/generators/d01b33f4a589/workspace/lesson_probe.py \
    --library repo --oracle racket --seeds 16 --starts 8 \
    --runner-lessons 128 --out checks/lesson-racket.json

Set RACKET_PATH for the second command. --generator-source can replay a frozen
baseline while --contract-source selects the current rival declarations.
Every failing window's replay coordinates and rival names are retained. The
seed-661 reproducer additionally includes full input/reference/rival grids.
Python-mirror reports are explicitly NOT independent Racket validation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Callable

Grid = list[list[int]]
Rival = Callable[[Grid], Grid]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_key(grid: Grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot import generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def decode(grid) -> Grid:
    return [[int(value) for value in row] for row in grid]


def score_lesson(rivals: dict[str, Rival], demos: list[dict], query: dict) -> dict:
    """Keep refutation, harmless survival and answer ambiguity separate."""
    scored = {"refuted": [], "survived_all": [], "query_discriminates": []}
    for name, rival in sorted(rivals.items()):
        fits = all(rival(copy.deepcopy(demo["input"])) == demo["output"] for demo in demos)
        if not fits:
            scored["refuted"].append(name)
        elif rival(copy.deepcopy(query["input"])) == query["output"]:
            scored["survived_all"].append(name)
        else:
            scored["query_discriminates"].append(name)
    return scored


@contextmanager
def oracle_session(library: Path, task_id: str, source: str, generator, mode: str):
    """Reference runtime is a disposable independent copy, never edited in place."""
    if mode == "python":
        yield generator.rule_mirror, None
        return
    sys.path.insert(0, str(library / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    previous_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-lesson-probe-") as temp:
        runtime = Path(temp)
        prepare_runtime(Catalog(library), runtime, task_id)
        sys.path.insert(0, str(runtime))
        os.chdir(runtime)
        bridge = None
        try:
            from puzzle_generators import runner
            from puzzle_generators.rule_wrap import wrap_rule
            bridge, fn_name = runner._open_bridge_with_rule(wrap_rule(source))
            # The sampled source may be a frozen baseline, not the installed
            # per_puzzle package. Bind it explicitly instead of asking Python
            # to rediscover it through an already-loaded package's __path__.
            bundle = runner.GeneratorBundle(
                task_id=task_id, rule_task_id=task_id, rule_source=source,
                rule_callable_text=wrap_rule(source),
                rule_file="data/canonical/puzzles.jsonl",
                generator_module=generator,
            )

            def apply(grid):
                return runner._apply_rule(bridge, fn_name, grid)

            def assemble(seed, start, difficulty, count):
                return runner.run_one(task_id, seed, start, n_train=count, n_test=1,
                                      difficulty=difficulty, bundle=bundle,
                                      bridge=bridge, fn_name=fn_name)

            yield apply, assemble
        finally:
            if bridge is not None:
                bridge.shutdown()
            os.chdir(previous_cwd)
            sys.path.remove(str(runtime))


def run(args) -> dict:
    library = args.library.resolve()
    task_home = Path(__file__).resolve().parents[1]
    source_path = (args.generator_source or task_home / "generator.py").resolve()
    contract_path = (args.contract_source or source_path).resolve()
    sys.path.insert(0, str(library / "shared/runtime"))
    generator = load_module(source_path, "sampled_generator")
    contract = generator if source_path == contract_path else load_module(contract_path, "rival_contract")
    rivals = dict(getattr(contract, "LESSON_COMPETITORS", {}))
    shortcuts = dict(getattr(contract, "CANONICAL_SHORTCUTS", {}))
    for name, rival in shortcuts.items():
        if name in rivals and rivals[name] is not rival:
            raise ValueError(f"Inconsistent duplicate rival declaration: {name}")
        rivals[name] = rival
    if not rivals:
        raise ValueError("No declared rivals; supply a --contract-source with a measured contract")
    if args.runner_lessons and args.oracle != "racket":
        raise ValueError("--runner-lessons requires --oracle racket")
    bands = args.bands.split(",")
    if not bands or any(b not in ("default", "easy", "medium", "hard") for b in bands):
        raise ValueError("--bands must contain default/easy/medium/hard separated by commas")
    if len(set(bands)) != len(bands):
        raise ValueError("--bands must not repeat entries")
    task_id = generator.TASK_ID
    row = next(json.loads(line) for line in (library / "shared/data/canonical/puzzles.jsonl").open()
               if json.loads(line).get("task_id") == task_id)
    reference = row["program_solution"]
    canonical = row["train"] + (row["test"] if isinstance(row["test"], list) else [row["test"]])
    pairs = [{"input": decode(p["input"]), "output": decode(p["output"])} for p in canonical]
    shortcuts_checked = {}
    for name, rival in shortcuts.items():
        matches = [rival(copy.deepcopy(p["input"])) == p["output"] for p in pairs]
        shortcuts_checked[name] = {"matched": sum(matches), "total": len(matches),
                                   "failed_pair_indices": [i for i, value in enumerate(matches) if not value]}

    report = {
        "schema": "corner-command-lesson-probe-v1", "task_id": task_id,
        "generator_sha256": sha256(source_path), "generator_version": generator.VERSION,
        "contract_sha256": sha256(contract_path), "contract_version": contract.VERSION,
        "rule_sha256": hashlib.sha256(reference.encode()).hexdigest(),
        "normalized_rule_sha256": hashlib.sha256(" ".join(reference.split()).encode()).hexdigest(),
        "oracle": "canonical_racket" if args.oracle == "racket" else "python_mirror_not_independent",
        "declared_lesson_competitors": sorted(getattr(contract, "LESSON_COMPETITORS", {})),
        "declared_canonical_shortcuts": sorted(shortcuts),
        "canonical_shortcut_checks": shortcuts_checked,
        "population": {"seed_start": args.seed_start, "seed_count": args.seeds,
                       "sample_indices": [0, args.starts + generator.EXAMPLES_NEEDED - 1],
                       "cyclic_start_range": [0, args.starts - 1], "bands": bands,
                       "demos_per_lesson": generator.EXAMPLES_NEEDED,
                       "lesson_count": args.seeds * args.starts * len(bands),
                       "draw_count": args.seeds * (args.starts + generator.EXAMPLES_NEEDED) * len(bands),
                       "assembly": "overlapping consecutive windows, common seed and difficulty",
                       "counts_exclude": "seed-661 reproducer and separate actual-runner verification"},
        "per_band": {}, "failed_windows": [], "mirror_mismatches": [], "invalid_draws": [],
        "actual_runner": {"requested": args.runner_lessons, "checked": 0, "failed": []},
    }
    all_inputs, all_outputs = set(), set()
    ambiguous_total = 0
    with oracle_session(library, task_id, reference, generator, args.oracle) as (apply, assemble):
        for band in bands:
            difficulty = None if band == "default" else band
            stats = {"draws": 0, "lessons": 0, "query_discriminates": 0, "all_rivals_refuted": 0,
                     "literal_public": 0}
            axes, refuted, survived, discriminates = Counter(), Counter(), Counter(), Counter()
            unique_inputs, unique_outputs = set(), set()
            for seed in range(args.seed_start, args.seed_start + args.seeds):
                draws = []
                for sample_index in range(args.starts + generator.EXAMPLES_NEEDED):
                    grid = generator.generate(seed, sample_index, difficulty=difficulty)
                    output = apply(grid)
                    errors = generator.self_check(grid)
                    if errors:
                        report["invalid_draws"].append({"band": band, "seed": seed,
                                                         "sample_index": sample_index, "errors": errors})
                    if args.oracle == "racket" and generator.rule_mirror(grid) != output:
                        report["mirror_mismatches"].append({"band": band, "seed": seed,
                            "sample_index": sample_index, "input": grid, "actual_racket_output": output,
                            "python_output": generator.rule_mirror(grid)})
                    draws.append({"input": grid, "output": output})
                    observation = generator.observe_overrides(grid)
                    axes["|".join(str(observation[k]) for k in sorted(observation))] += 1
                    stats["literal_public"] += generator.exact_public_profile_index(grid) is not None
                    unique_inputs.add(grid_key(grid)); unique_outputs.add(grid_key(output))
                for start in range(args.starts):
                    n = generator.EXAMPLES_NEEDED
                    scored = score_lesson(rivals, draws[start:start + n], draws[start + n])
                    refuted.update(scored["refuted"]); survived.update(scored["survived_all"])
                    discriminates.update(scored["query_discriminates"])
                    stats["lessons"] += 1
                    stats["all_rivals_refuted"] += len(scored["refuted"]) == len(rivals)
                    if scored["query_discriminates"]:
                        stats["query_discriminates"] += 1
                        report["failed_windows"].append({"band": band, "seed": seed, "start": start,
                                                        "rivals": scored["query_discriminates"]})
                stats["draws"] += len(draws)
            stats.update({"unique_inputs": len(unique_inputs), "unique_outputs": len(unique_outputs),
                          "axis_counts": dict(sorted(axes.items())),
                          "rival_refutation_counts": dict(sorted(refuted.items())),
                          "rival_survived_all_counts": dict(sorted(survived.items())),
                          "rival_query_discriminating_counts": dict(sorted(discriminates.items()))})
            all_inputs.update(unique_inputs); all_outputs.update(unique_outputs)
            ambiguous_total += stats["query_discriminates"]
            report["per_band"][band] = stats
            print(f"{band}: {stats['query_discriminates']}/{stats['lessons']} ambiguous lessons", flush=True)

        reproduction = []
        for i in range(generator.EXAMPLES_NEEDED + 1):
            grid = generator.generate(args.repro_seed, i, difficulty="easy")
            reproduction.append({"input": grid, "output": apply(grid)})
        scored = score_lesson(rivals, reproduction[:-1], reproduction[-1])
        report["reproducer"] = {"seed": args.repro_seed, "difficulty": "easy",
                               "sample_index": 0, "demos": reproduction[:-1],
                               "query": reproduction[-1], "scores": scored,
                               "query_rival_outputs": {name: rivals[name](reproduction[-1]["input"])
                                                       for name in scored["query_discriminates"]}}

        for i in range(args.runner_lessons):
            band = bands[i % len(bands)]
            difficulty = None if band == "default" else band
            start = (i // len(bands)) % args.starts
            seed = args.seed_start + i // (len(bands) * args.starts)
            episode = assemble(seed, start, difficulty, generator.EXAMPLES_NEEDED)
            scored = score_lesson(rivals, episode["train"], episode["test"][0])
            report["actual_runner"]["checked"] += 1
            if scored["query_discriminates"]:
                report["actual_runner"]["failed"].append({"band": band, "seed": seed, "start": start,
                                                          "rivals": scored["query_discriminates"]})
        report["actual_runner"]["plan"] = "i: band=i%B; start=(i//B)%starts; seed=seed_start+i//(B*starts)"
    report["unique_inputs"] = len(all_inputs)
    report["unique_outputs"] = len(all_outputs)
    report["query_discriminating_lesson_count"] = ambiguous_total
    report["passed"] = not (ambiguous_total or report["invalid_draws"] or report["mirror_mismatches"]
                            or report["actual_runner"]["failed"] or
                            any(v["failed_pair_indices"] for v in shortcuts_checked.values()))
    return report


def positive(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--generator-source", type=Path)
    parser.add_argument("--contract-source", type=Path)
    parser.add_argument("--oracle", choices=("python", "racket"), default="python")
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seeds", type=positive, default=256)
    parser.add_argument("--starts", type=positive, default=8)
    parser.add_argument("--bands", default="default,easy,medium,hard")
    parser.add_argument("--repro-seed", type=int, default=661)
    parser.add_argument("--runner-lessons", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    args.out = args.out.resolve()
    if args.out.exists():
        parser.error(f"Refusing to overwrite retained evidence: {args.out}")
    if args.runner_lessons < 0:
        parser.error("--runner-lessons must be nonnegative")
    report = run(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"report": str(args.out), "passed": report["passed"],
                      "ambiguous": report["query_discriminating_lesson_count"]}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
