"""Reusable bounded self-audit for the 86af5978a32a parametric family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parent
TASK_ID = "86af5978a32a"


def _load_adapter():
    path = HOME / "adapter.py"
    name = "_parametric_probe_86af5978a32a_" + hashlib.sha256(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _keys(episode):
    return [
        json.dumps(pair["input"], separators=(",", ":"))
        for split in ("train", "test")
        for pair in episode[split]
    ]


def build_report(*, seeds, demos: int, queries: int):
    adapter = _load_adapter()
    settings = [{"finish": value} for value in adapter.FINISHES]
    episodes = []
    checks = {
        "canonical_program_exact": (
            adapter.program({"finish": "stamp_only"}).encode("utf-8")
            == (HOME / "rules" / "canonical.rkt").read_bytes()
        ),
        "deterministic": True,
        "count_prefix_invariant": True,
        "same_inputs_across_settings": True,
        "every_demo_identifies_setting": True,
        "bounded_rivals_refuted": True,
        "contains_25x25_max_lawful_query": True,
        "covers_source_axes": True,
        "unique_largest_binary_component": True,
    }
    total_cases = 0

    for seed in seeds:
        by_finish = {
            value: adapter.generate(seed, {"finish": value}, demos=demos, queries=queries)
            for value in adapter.FINISHES
        }
        repeated = adapter.generate(
            seed, {"finish": "highlight_largest_component"}, demos=demos, queries=queries
        )
        checks["deterministic"] &= repeated == by_finish["highlight_largest_component"]
        checks["same_inputs_across_settings"] &= (
            _keys(by_finish["stamp_only"]) == _keys(by_finish["highlight_largest_component"])
        )

        prefix = adapter.generate(
            seed, {"finish": "highlight_largest_component"}, demos=2, queries=1
        )
        checks["count_prefix_invariant"] &= (
            prefix["train"] == by_finish["highlight_largest_component"]["train"][:2]
            and prefix["test"] == by_finish["highlight_largest_component"]["test"][:1]
        )

        alternate = by_finish["highlight_largest_component"]
        canonical = by_finish["stamp_only"]
        checks["every_demo_identifies_setting"] &= all(
            left["output"] != right["output"]
            for left, right in zip(canonical["train"], alternate["train"])
        )

        rival_mismatches = {}
        for name, rival in adapter.RIVALS.items():
            mismatch = sum(
                rival(pair["input"]) != pair["output"]
                for pair in alternate["train"]
            )
            rival_mismatches[name] = mismatch
            checks["bounded_rivals_refuted"] &= mismatch > 0

        all_pairs = alternate["train"] + alternate["test"]
        total_cases += len(all_pairs)
        facts = [adapter.input_facts(pair["input"]) for pair in all_pairs]
        checks["covers_source_axes"] &= (
            {row["orientation"] for row in facts} == {"horizontal", "vertical"}
            and {row["layout_position"] for row in facts} == {"first", "second"}
            and {row["color_role"] for row in facts} == {"shape_is_8", "layout_has_8"}
            and {row["half_size"] for row in facts} == {3, 4, 5}
        )
        checks["unique_largest_binary_component"] &= all(
            (lambda sizes: len(sizes) >= 2 and sizes[0] > sizes[1])(
                adapter.component_intermediate(pair["input"])["binary_component_sizes"]
            )
            for pair in all_pairs
        )
        max_pair = alternate["test"][-1]
        checks["contains_25x25_max_lawful_query"] &= (
            len(max_pair["output"]) == 25
            and len(max_pair["output"][0]) == 25
            and sum(value != 0 for row in max_pair["output"] for value in row) >= 120
        )
        episodes.append({
            "seed": seed,
            "visible_input_sha256": hashlib.sha256(
                "\n".join(_keys(alternate)).encode("utf-8")
            ).hexdigest(),
            "rival_mismatches_on_demos": rival_mismatches,
            "max_query_output_shape": [
                len(max_pair["output"]), len(max_pair["output"][0])
            ],
        })

    return {
        "schema": "arcpuzzles-parametric-authoring-probe-v1",
        "task_id": TASK_ID,
        "seeds": list(seeds),
        "counts": {"demos": demos, "queries": queries, "cases": total_cases},
        "settings": settings,
        "checks": checks,
        "episodes": episodes,
        "limits": {
            "finite_rivals_only": list(adapter.RIVALS),
            "maximum_lawful_output": "25x25 because source half_size is 3..5 and output side is k^2",
        },
    }


def write_report(path: Path, report) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--demos", type=int, default=6)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = build_report(seeds=args.seeds or [0, 17, 97], demos=args.demos, queries=args.queries)
    write_report(args.out, report)
    print(json.dumps({"out": str(args.out), "checks": report["checks"]}, sort_keys=True))
    return 0 if all(report["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
