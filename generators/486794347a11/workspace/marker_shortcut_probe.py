#!/usr/bin/env python3
"""Deterministic no-count shortcut census for task 486794347a11.

The probe intentionally excludes the number of marker cells.  It measures
whether simpler geometry features (span, adjacency, contiguous runs, edge
contact, and small combinations of those features) can recover the answer.
Run it against either a prepared before/after runtime by setting PYTHONPATH.
"""
from __future__ import annotations

import argparse
import importlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

DEFAULT_MODULE = "puzzle_generators.per_puzzle.486794347a11.generator"
DIFFICULTIES = (None, "easy", "medium", "hard")


def marker_features(
    grid: Sequence[Sequence[int]],
    analyze: Callable[[Any], Mapping[str, Any]],
) -> dict[str, int]:
    """Return deliberately no-count marker geometry features for one grid."""
    analysis = analyze(grid)
    markers = list(analysis["markers"])
    width = int(analysis["width"])
    if len(markers) < 2:
        raise ValueError("probe expects at least two markers")
    gaps = [right - left for left, right in zip(markers, markers[1:])]
    return {
        "width": width,
        "left": markers[0],
        "right": markers[-1],
        "span": markers[-1] - markers[0],
        "touch_left": int(markers[0] == 0),
        "touch_right": int(markers[-1] == width - 1),
        "touch_edges": int(markers[0] == 0) + int(markers[-1] == width - 1),
        "full_span": int(markers[0] == 0 and markers[-1] == width - 1),
        "has_adjacent": int(any(gap == 1 for gap in gaps)),
        "components": 1 + sum(gap > 1 for gap in gaps),
        "min_gap": min(gaps),
        "max_gap": max(gaps),
        "gap_span": max(gaps) - min(gaps),
        "sum_positions": sum(markers),
        "sum_mod2": sum(markers) % 2,
        "right_mod2": markers[-1] % 2,
        "span_mod2": (markers[-1] - markers[0]) % 2,
    }


def exact_univariate_features(
    rows: Sequence[Mapping[str, int]], labels: Sequence[int]
) -> dict[str, dict[str, int]]:
    """Return features whose value alone maps deterministically to the label."""
    if len(rows) != len(labels):
        raise ValueError("rows and labels must have equal length")
    if not rows:
        return {}
    result: dict[str, dict[str, int]] = {}
    for name in rows[0]:
        observed: dict[int, set[int]] = defaultdict(set)
        for row, label in zip(rows, labels):
            observed[int(row[name])].add(int(label))
        if observed and all(len(values) == 1 for values in observed.values()):
            result[name] = {
                str(value): next(iter(values)) for value, values in sorted(observed.items())
            }
    return result


def _confusion(
    rows: Sequence[Mapping[str, int]],
    labels: Sequence[int],
    predict: Callable[[Mapping[str, int]], int],
) -> dict[str, Any]:
    counts = Counter((int(actual), int(predict(row))) for row, actual in zip(rows, labels))
    correct = sum(count for (actual, predicted), count in counts.items() if actual == predicted)
    return {
        "accuracy": correct / len(labels) if labels else None,
        "confusion": {
            f"actual_{actual}_predicted_{predicted}": count
            for (actual, predicted), count in sorted(counts.items())
        },
    }


def named_rival_results(
    rows: Sequence[Mapping[str, int]], labels: Sequence[int]
) -> dict[str, Any]:
    return {
        "adjacent_or_full_span": _confusion(
            rows,
            labels,
            lambda row: 3 if row["has_adjacent"] or row["full_span"] else 2,
        ),
        "marker_components": _confusion(
            rows,
            labels,
            lambda row: 2 if row["components"] == 2 else 3,
        ),
        "span_min_gap_depth2": _confusion(
            rows,
            labels,
            lambda row: 3 if row["span"] > 2 and row["min_gap"] <= 2 else 2,
        ),
        "rightmost_stride2": _confusion(
            rows,
            labels,
            lambda row: max(1, row["right"] // 2 + 1),
        ),
    }


def _shallow_tree_results(
    rows: Sequence[Mapping[str, int]], labels: Sequence[int], seed_groups: Sequence[int]
) -> dict[str, Any]:
    """Fit reproducible shallow trees when scikit-learn is available."""
    try:
        from sklearn.tree import DecisionTreeClassifier, export_text
    except ImportError:
        return {"available": False, "reason": "scikit-learn is not installed"}

    names = list(rows[0]) if rows else []
    unique_seeds = sorted(set(seed_groups))
    if len(unique_seeds) >= 2:
        holdout_count = max(1, len(unique_seeds) // 4)
        test_seeds = set(unique_seeds[-holdout_count:])
        train = [index for index, seed in enumerate(seed_groups) if seed not in test_seeds]
        test = [index for index, seed in enumerate(seed_groups) if seed in test_seeds]
    else:
        train = [index for index in range(len(rows)) if index % 4 != 3]
        test = [index for index in range(len(rows)) if index % 4 == 3]
    x = [[int(row[name]) for name in names] for row in rows]
    result: dict[str, Any] = {"available": True, "features": names, "depths": {}}
    for depth in (1, 2, 3, 4):
        model = DecisionTreeClassifier(
            max_depth=depth,
            min_samples_leaf=max(2, len(train) // 1000),
            random_state=0,
        )
        model.fit([x[index] for index in train], [labels[index] for index in train])
        result["depths"][str(depth)] = {
            "train_accuracy": float(model.score(
                [x[index] for index in train], [labels[index] for index in train]
            )),
            "test_accuracy": float(model.score(
                [x[index] for index in test], [labels[index] for index in test]
            )),
            "leaves": int(model.get_n_leaves()),
            "rule": export_text(model, feature_names=names, max_depth=depth),
        }
    return result


def run_probe(module_name: str, seeds: int, samples: int) -> dict[str, Any]:
    generator = importlib.import_module(module_name)
    rows: list[dict[str, int]] = []
    labels: list[int] = []
    seed_groups: list[int] = []
    phase_rows: list[dict[str, Any]] = []

    for difficulty in DIFFICULTIES:
        for seed in range(seeds):
            for sample_index in range(samples):
                grid = generator.generate(seed, sample_index, difficulty=difficulty)
                analysis = generator._analysis_or_raise(grid)
                features = marker_features(grid, generator._analysis_or_raise)
                label = int(analysis["n_markers"])
                rows.append(features)
                labels.append(label)
                seed_groups.append(seed)
                if seed == 0 and sample_index < 8:
                    phase_rows.append(
                        {
                            "difficulty": difficulty,
                            "sample_index": sample_index,
                            "markers": analysis["markers"],
                            "label": label,
                            "features": features,
                        }
                    )

    return {
        "task_id": getattr(generator, "TASK_ID", None),
        "version": getattr(generator, "VERSION", None),
        "module": module_name,
        "sample_count": len(rows),
        "seeds": seeds,
        "samples_per_difficulty": samples,
        "difficulties": list(DIFFICULTIES),
        "feature_names": list(rows[0]) if rows else [],
        "exact_univariate_features": exact_univariate_features(rows, labels),
        "named_rivals": named_rival_results(rows, labels),
        "shallow_trees": _shallow_tree_results(rows, labels, seed_groups),
        "phase_examples": phase_rows,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", default=DEFAULT_MODULE)
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.seeds < 1 or args.samples < 1:
        parser.error("--seeds and --samples must be positive")

    result = run_probe(args.module, args.seeds, args.samples)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
