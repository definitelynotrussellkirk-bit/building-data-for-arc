"""Search generated lessons for plausible shortcut rules that still survive.

The ordinary scan scores the task's explicitly declared rivals. ``--compound``
also enumerates a finite cross-product of connectivity/grouping, raw-vs-masked
crops, ordering, alignment, and separator choices. This is a mirror-scored
adversarial design tool, not label authority. Run authoritative Racket parity
separately with ``review_probe.py``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("rival_search_subject", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _by_color_components(grid):
    colors = sorted({value for row in grid for value in row if value})
    return [
        (
            color,
            [
                (row, column)
                for row, values in enumerate(grid)
                for column, value in enumerate(values)
                if value == color
            ],
        )
        for color in colors
    ]


def _compound_space(generator):
    extractors = {
        "mono4": lambda grid: generator._components(grid),
        "mono8": lambda grid: generator._components(grid, connectivity=8),
        "multicolor4": lambda grid: generator._components(grid, multicolor=True),
        "by_color": _by_color_components,
    }
    orderings = (
        ("left", "left", False),
        ("right", "right", False),
        ("top", "top", False),
        ("color", "color", False),
        ("area", "area", False),
        ("left_bottom", "left_bottom", False),
        ("reverse_left", "left", True),
    )
    specs = []
    for extractor, mask, (order_name, order, reverse), align, gap in itertools.product(
        extractors,
        (False, True),
        orderings,
        ("center", "ceil", "left"),
        (0, 1, 2),
    ):
        # Exact intended mirror: monochromatic 4-components, raw crops,
        # left/top order, floor centering, one separator row.
        if (extractor, mask, order_name, align, gap) == (
            "mono4",
            False,
            "left",
            "center",
            1,
        ):
            continue
        name = "|".join(
            (
                extractor,
                "mask" if mask else "raw",
                order_name,
                align,
                f"gap{gap}",
            )
        )
        specs.append(
            {
                "name": name,
                "extractor": extractor,
                "mask": mask,
                "order": order,
                "reverse": reverse,
                "align": align,
                "gap": gap,
            }
        )
    return extractors, specs


def _scan_compound_windows(generator, grids, outputs, *, band, seed, start_count):
    extractors, specs = _compound_space(generator)
    extracted = {
        name: [extractor(grid) for grid in grids]
        for name, extractor in extractors.items()
    }
    fit_counts: dict[str, int] = {}
    first_fit: dict[str, dict] = {}
    survivors = []

    for spec in specs:
        candidate = [
            generator._render(
                grid,
                extracted[spec["extractor"]][index],
                mask=spec["mask"],
                order=spec["order"],
                reverse=spec["reverse"],
                align=spec["align"],
                gap=spec["gap"],
            )
            for index, grid in enumerate(grids)
        ]
        for start in range(start_count):
            stop = start + generator.EXAMPLES_NEEDED
            if all(candidate[index] == outputs[index] for index in range(start, stop)):
                name = spec["name"]
                fit_counts[name] = fit_counts.get(name, 0) + 1
                first_fit.setdefault(
                    name,
                    {
                        "band": band,
                        "seed": seed,
                        "start_index": start,
                        "query_index": stop,
                        "profiles": [
                            generator.schedule_profile(seed, index, band)
                            for index in range(start, stop + 1)
                        ],
                    },
                )
                if candidate[stop] != outputs[stop]:
                    survivors.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start_index": start,
                            "query_index": stop,
                            "rival": name,
                            "profiles": [
                                generator.schedule_profile(seed, index, band)
                                for index in range(start, stop + 1)
                            ],
                        }
                    )
    return specs, fit_counts, first_fit, survivors


def scan(generator, *, seeds: int, compound: bool = False) -> dict:
    bands = ("easy", "medium", "hard")
    rivals = generator.LESSON_COMPETITORS
    refutations = {name: 0 for name in rivals}
    first_witness = {}
    survivors = []
    generated = 0
    schedule_len = len(generator._SCHEDULE)

    compound_fit_counts: dict[str, int] = {}
    compound_first_fit: dict[str, dict] = {}
    compound_survivors = []
    compound_specs = None

    for band in bands:
        for seed in range(seeds):
            # Two complete cycles plus the query suffix cover every possible
            # contiguous start phase for a periodic teaching schedule.
            count = 2 * schedule_len + generator.EXAMPLES_NEEDED
            grids = [
                generator.generate(seed, index, difficulty=band)
                for index in range(count)
            ]
            outputs = [generator.rule_mirror(grid) for grid in grids]
            generated += len(grids)
            for index, (grid, target) in enumerate(zip(grids, outputs)):
                for name, rival in rivals.items():
                    candidate = rival(grid)
                    if candidate != target:
                        refutations[name] += 1
                        first_witness.setdefault(
                            name,
                            {
                                "band": band,
                                "seed": seed,
                                "sample_index": index,
                                "profile": generator.schedule_profile(seed, index, band),
                                "input": grid,
                                "intended_output": target,
                                "rival_output": candidate,
                            },
                        )
            for start in range(schedule_len):
                stop = start + generator.EXAMPLES_NEEDED
                query_index = stop
                for name, rival in rivals.items():
                    if (
                        all(
                            rival(grids[index]) == outputs[index]
                            for index in range(start, stop)
                        )
                        and rival(grids[query_index]) != outputs[query_index]
                    ):
                        survivors.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start_index": start,
                                "query_index": query_index,
                                "rival": name,
                                "profiles": [
                                    generator.schedule_profile(seed, index, band)
                                    for index in range(start, query_index + 1)
                                ],
                            }
                        )

            if compound:
                specs, fit_counts, first_fit, found = _scan_compound_windows(
                    generator,
                    grids,
                    outputs,
                    band=band,
                    seed=seed,
                    start_count=schedule_len,
                )
                compound_specs = specs
                for name, count_found in fit_counts.items():
                    compound_fit_counts[name] = (
                        compound_fit_counts.get(name, 0) + count_found
                    )
                for name, witness in first_fit.items():
                    compound_first_fit.setdefault(name, witness)
                compound_survivors.extend(found)

    missing_witnesses = [name for name, count in refutations.items() if count == 0]
    report = {
        "schema": "f99263121e8a-rival-search-v2",
        "task_id": generator.TASK_ID,
        "version": generator.VERSION,
        "generator_sha256": sha256(HOME / "generator.py"),
        "mirror_scored": True,
        "bands": list(bands),
        "seed_range": [0, seeds - 1],
        "examples_needed": generator.EXAMPLES_NEEDED,
        "schedule": list(generator._SCHEDULE),
        "rivals": sorted(rivals),
        "generated_examples_with_overlap": generated,
        "rival_refutations": refutations,
        "first_witness": first_witness,
        "missing_witnesses": missing_witnesses,
        "surviving_windows": survivors,
        "limitations": [
            "Python mirror only; use the Racket differential census for authority parity.",
            "Declared and compound rival libraries are finite and do not prove unique inference.",
            "Generated-example count includes overlap across teaching windows.",
        ],
    }
    if compound:
        assert compound_specs is not None
        fitting = sorted(compound_fit_counts)
        report["compound_search"] = {
            "enabled": True,
            "candidate_space": {
                "extractors": ["mono4", "mono8", "multicolor4", "by_color"],
                "crop_modes": ["raw", "mask"],
                "orderings": [
                    "left",
                    "right",
                    "top",
                    "color",
                    "area",
                    "left_bottom",
                    "reverse_left",
                ],
                "alignments": ["center_floor", "center_ceil", "left"],
                "separator_rows": [0, 1, 2],
            },
            "candidate_count": len(compound_specs),
            "evaluated_candidate_outputs": len(compound_specs) * generated,
            "candidates_fitting_any_complete_window": len(fitting),
            "fitting_window_total": sum(compound_fit_counts.values()),
            "fit_window_counts": {
                name: compound_fit_counts[name] for name in fitting
            },
            "first_fitting_window": {
                name: compound_first_fit[name] for name in fitting
            },
            "surviving_windows": compound_survivors,
            "passed": not fitting and not compound_survivors,
        }
    else:
        report["compound_search"] = {"enabled": False}
    report["passed"] = (
        not survivors
        and not missing_witnesses
        and (not compound or report["compound_search"]["passed"])
    )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument(
        "--compound",
        action="store_true",
        help="also enumerate 503 cross-axis rival combinations",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    if args.out.exists():
        parser.error(f"refusing to overwrite retained evidence: {args.out}")
    report = scan(load_generator(), seeds=args.seeds, compound=args.compound)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    summary = {
        "report": str(args.out),
        "passed": report["passed"],
        "rivals": len(report["rivals"]),
        "surviving_windows": len(report["surviving_windows"]),
        "missing_witnesses": report["missing_witnesses"],
        "compound": report["compound_search"]["enabled"],
    }
    if args.compound:
        summary.update(
            {
                "compound_candidates": report["compound_search"]["candidate_count"],
                "compound_fitting": report["compound_search"][
                    "candidates_fitting_any_complete_window"
                ],
                "compound_survivors": len(
                    report["compound_search"]["surviving_windows"]
                ),
            }
        )
    print(json.dumps(summary))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
