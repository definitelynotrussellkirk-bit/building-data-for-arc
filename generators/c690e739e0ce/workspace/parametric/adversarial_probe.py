"""Bounded adversarial probe for the c690e739 row-scope family.

Searches a finite library of plausible row-mask and partial-intermediate rules
against the actual minimum lesson, then attacks certificates and public/private
projection.  It is a reusable authoring tool, not a universal uniqueness proof.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
from typing import Callable, Iterable

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_c690e739_probe_prototype", HERE / "prototype.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load task-local prototype")
p = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p)

Grid = list[list[int]]
Rule = Callable[[Grid], Grid]


def _mask(grid: Grid, rows: set[int]) -> Grid:
    return [row[::-1] if r in rows else row[:] for r, row in enumerate(grid)]


def _rows_with(grid: Grid, color: int) -> set[int]:
    return {r for r, row in enumerate(grid) if color in row}


def _candidate_predictions(grid: Grid) -> tuple[dict[str, frozenset[int]], dict[str, Grid]]:
    """Return row-mask and genuinely non-mask rival predictions.

    All family rows are asymmetric, so a row-reflection candidate is completely
    characterized by its selected-row mask.  Keeping masks compact makes the
    bounded audit fast enough to run across hundreds of 30x30 episodes; only
    wrong operations that cannot be represented as a mask materialize grids.
    """
    profile = p.input_profile(grid)
    counts = p._color_counts(grid)
    ordered = p._ordered_colors(grid)
    minority = profile["minority_color"]
    h, w = len(grid), len(grid[0])
    all_rows = set(range(h))

    masks: dict[str, frozenset[int]] = {
        "named:identity": frozenset(),
        "named:odd_rows": frozenset(r for r in range(h) if r % 2 == 1),
        "named:even_rows": frozenset(r for r in range(h) if r % 2 == 0),
        "named:top_half": frozenset(range(h // 2)),
        "named:bottom_half": frozenset(range(h // 2, h)),
        "named:top_left_color_rows": frozenset(_rows_with(grid, grid[0][0])),
        "named:lowest_numeric_color_rows": frozenset(_rows_with(grid, min(counts))),
        "named:most_frequent_rows": frozenset(
            _rows_with(grid, max(counts, key=lambda value: (counts[value], -value)))
        ),
        "named:second_rarest_rows": frozenset(_rows_with(grid, ordered[1])),
        "named:first_selected_row_only": frozenset({min(profile["selected_rows"])}),
    }
    grids: dict[str, Grid] = {
        "named:vertical_reflection": p._apply_named("vertical_reflection", grid),
        "named:minority_cells_only": p._apply_named("minority_cells_only", grid),
        "named:selected_rows_vertical": p._apply_named("selected_rows_vertical", grid),
    }

    for color in range(10):
        masks[f"fixed_color:{color}"] = frozenset(_rows_with(grid, color))
    for rank, color in enumerate(ordered):
        masks[f"frequency_rank:{rank}"] = frozenset(_rows_with(grid, color))
    for target_count in range(1, 41):
        matching = sorted(color for color, count in counts.items() if count == target_count)
        exact_rows = _rows_with(grid, matching[0]) if matching else set()
        masks[f"frequency_exact:{target_count}"] = frozenset(exact_rows)
        threshold_colors = {color for color, count in counts.items() if count <= target_count}
        threshold_rows = {
            r for r, row in enumerate(grid) if any(color in threshold_colors for color in row)
        }
        masks[f"frequency_leq:{target_count}"] = frozenset(threshold_rows)

    selected = list(profile["selected_rows"])
    for n in range(1, 9):
        masks[f"first_n_minority_rows:{n}"] = frozenset(selected[:n])
        masks[f"last_n_minority_rows:{n}"] = frozenset(selected[-n:])

    masks.update(
        {
            "minority_count_exactly_one": frozenset(
                r for r, row in enumerate(grid) if row.count(minority) == 1
            ),
            "minority_count_odd": frozenset(
                r for r, row in enumerate(grid) if row.count(minority) % 2 == 1
            ),
            "minority_in_left_half": frozenset(
                r for r, row in enumerate(grid) if minority in row[: (w + 1) // 2]
            ),
            "minority_in_right_half": frozenset(
                r for r, row in enumerate(grid) if minority in row[w // 2 :]
            ),
            "minority_at_edge": frozenset(
                r
                for r, row in enumerate(grid)
                if row[0] == minority or row[-1] == minority
            ),
            "first_cell_is_global_minority": frozenset(
                r for r, row in enumerate(grid) if row[0] == minority
            ),
            "last_cell_is_global_minority": frozenset(
                r for r, row in enumerate(grid) if row[-1] == minority
            ),
            "fewest_distinct_colors": frozenset(
                r
                for r, row in enumerate(grid)
                if len(set(row)) == min(len(set(other)) for other in grid)
            ),
            "most_distinct_colors": frozenset(
                r
                for r, row in enumerate(grid)
                if len(set(row)) == max(len(set(other)) for other in grid)
            ),
            "boundary_rows": frozenset({0, h - 1}),
            "interior_rows": frozenset(all_rows - {0, h - 1}),
        }
    )

    partial = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == minority:
                partial[r][w - 1 - c] = minority
    grids["paint_mirrored_minority_only"] = partial

    outer = [row[:] for row in grid]
    for r in profile["selected_rows"]:
        outer[r][0], outer[r][-1] = outer[r][-1], outer[r][0]
    grids["swap_outer_pair_only"] = outer

    represented_named = {
        name.removeprefix("named:")
        for name in set(masks) | set(grids)
        if name.startswith("named:")
    }
    if represented_named != set(p.EXTRA_RIVALS):
        raise AssertionError(
            f"adversarial named-rule inventory drift: {represented_named ^ set(p.EXTRA_RIVALS)}"
        )
    return masks, grids


def _mask_prediction(
    name: str,
    masks: dict[str, frozenset[int]],
) -> frozenset[int] | None:
    if name in masks:
        return masks[name]
    # A rank can be absent on a smaller palette. Treat it as identity rather
    # than silently dropping the candidate between demonstrations.
    if name.startswith("frequency_rank:"):
        return frozenset()
    return None


def _search_episode(episode: dict) -> tuple[list[dict], list[dict]]:
    truth_train = episode["train"]
    truth_test = episode["test"]
    bundles = [
        _candidate_predictions(pair["input"])
        for pair in truth_train + truth_test
    ]
    train_bundles = bundles[: len(truth_train)]
    test_bundles = bundles[len(truth_train) :]
    names = sorted(
        set().union(
            *(set(masks) | set(grids) for masks, grids in bundles)
        )
    )

    def truth_mask(pair: dict) -> frozenset[int]:
        grid = pair["input"]
        if episode["settings"] == {"reflection_scope": "all_rows"}:
            mask = frozenset(range(len(grid)))
        else:
            mask = frozenset(p.input_profile(grid)["selected_rows"])
        if _mask(grid, set(mask)) != pair["output"]:
            raise AssertionError("episode output is not the declared row-mask transform")
        return mask

    train_truth_masks = [truth_mask(pair) for pair in truth_train]
    test_truth_masks = [truth_mask(pair) for pair in truth_test]

    def matches(
        name: str,
        bundle: tuple[dict[str, frozenset[int]], dict[str, Grid]],
        pair: dict,
        target: frozenset[int],
    ) -> bool:
        masks, grids = bundle
        mask = _mask_prediction(name, masks)
        if mask is not None:
            return mask == target
        return grids[name] == pair["output"]

    query_changing: list[dict] = []
    equivalent: list[dict] = []
    for name in names:
        if not all(
            matches(name, bundle, pair, target)
            for bundle, pair, target in zip(
                train_bundles, truth_train, train_truth_masks
            )
        ):
            continue
        disagreements = [
            index
            for index, (bundle, pair, target) in enumerate(
                zip(test_bundles, truth_test, test_truth_masks)
            )
            if not matches(name, bundle, pair, target)
        ]
        record = {
            "seed": episode["seed"],
            "settings": episode["settings"],
            "demos": len(truth_train),
            "rival": name,
            "query_disagreements": disagreements,
        }
        if disagreements:
            query_changing.append(record)
        elif not (
            episode["settings"] == {"reflection_scope": "minority_rows"}
            and name == "frequency_rank:0"
        ):
            equivalent.append(record)
    return query_changing, equivalent

def _expect_rejected(call: Callable[[], object]) -> bool:
    try:
        call()
    except (ValueError, TypeError, AssertionError):
        return True
    return False


def _tamper_checks() -> dict:
    episode = p.generate(1103, {"reflection_scope": "minority_rows"}, 2, 4)
    checks: dict[str, bool] = {}

    stale = copy.deepcopy(episode)
    stale["program_solution"] = p.program({"reflection_scope": "all_rows"})
    checks["stale_program"] = _expect_rejected(lambda: p.certify(stale))

    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    checks["duplicate_input"] = _expect_rejected(lambda: p.certify(duplicate))

    wrong = copy.deepcopy(episode)
    wrong["train"][0]["output"][0][0] = (wrong["train"][0]["output"][0][0] + 1) % 10
    checks["wrong_label"] = _expect_rejected(lambda: p.certify(wrong))

    short = copy.deepcopy(episode)
    short["test"].pop()
    checks["wrong_query_count"] = _expect_rejected(lambda: p.certify(short))

    malformed = copy.deepcopy(episode)
    malformed["train"][0]["input"][0][0] = True
    checks["boolean_cell"] = _expect_rejected(lambda: p.certify(malformed))

    forged = copy.deepcopy(episode)
    forged["certificate"] = {"survivors": [forged["settings"]]}
    forged["train"][0]["output"] = [[9]]
    checks["forged_certificate_ignored"] = _expect_rejected(lambda: p.certify(forged))

    return {"checks": checks, "all_rejected": all(checks.values())}


def _public_projection_checks() -> dict:
    episode = p.generate(1907, {"reflection_scope": "minority_rows"}, 3, 4)
    original = p.public_turn(episode, 0)
    original_bytes = p.public_challenge_bytes(original)
    original_id = p.public_challenge_id(original)

    private = copy.deepcopy(episode)
    private["settings"] = {"reflection_scope": "all_rows"}
    private["program_solution"] = "forged-private-program"
    private["test"][0]["output"] = [[9]]
    private["test"][1]["input"] = [[9]]
    private_unchanged = (
        p.public_challenge_bytes(p.public_turn(private, 0)) == original_bytes
        and p.public_challenge_id(p.public_turn(private, 0)) == original_id
    )

    visible = copy.deepcopy(episode)
    visible["test"][0]["input"][0][0] = (visible["test"][0]["input"][0][0] + 1) % 10
    visible_changed = p.public_challenge_id(p.public_turn(visible, 0)) != original_id
    single_query_shape = set(original) == {"train", "test"} and len(original["test"]) == 1
    no_query_answer = set(original["test"][0]) == {"input"}
    no_private_keys = all(
        key not in original_bytes
        for key in (b"settings", b"program_solution", b"query_count", b"query_index")
    )
    checks = {
        "private_and_future_changes_do_not_change_first_turn": private_unchanged,
        "visible_query_change_changes_id": visible_changed,
        "single_query_shape": single_query_shape,
        "no_query_answer": no_query_answer,
        "no_private_keys": no_private_keys,
    }
    return {"checks": checks, "all_passed": all(checks.values())}


def audit(
    *,
    seeds: Iterable[int] = range(64),
    demo_counts: tuple[int, ...] = (2, 3, 6),
    use_racket: bool = False,
) -> dict:
    seeds = tuple(seeds)
    query_changing: list[dict] = []
    equivalent: list[dict] = []
    profile_failures: list[dict] = []
    cases = 0
    minority_colors: set[int] = set()
    selected_masks: set[tuple[int, ...]] = set()

    for seed in seeds:
        for demos in demo_counts:
            for setting in p.SETTINGS:
                cases += 1
                try:
                    episode = p.generate(seed, setting, demos, 4)
                    for pair in episode["train"] + episode["test"]:
                        profile = p.input_profile(pair["input"])
                        minority_colors.add(profile["minority_color"])
                        selected_masks.add(profile["selected_rows"])
                    found, same = _search_episode(episode)
                    query_changing.extend(found)
                    equivalent.extend(same)
                except Exception as exc:  # retained report, not silent retry
                    profile_failures.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "settings": setting,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )

    racket = {
        "requested": use_racket,
        "checked_pairs": 0,
        "causal_witness": None,
        "runtime_identity": None,
    }
    if use_racket:
        with p.RacketRunner() as execute:
            racket["runtime_identity"] = execute.identity
            for setting in p.SETTINGS:
                episode = p.generate(seeds[0] if seeds else 0, setting, 2, 4)
                p.certify(episode, execute)
                racket["checked_pairs"] += len(episode["train"]) + len(episode["test"])
            grid = p._scene(seeds[-1] if seeds else 0, "query", 3)
            racket["causal_witness"] = p.causal_witness(grid, execute)

    return {
        "schema": "c690e739-adversarial-probe-v1",
        "finite_scope": {
            "seeds": list(seeds),
            "demo_counts": list(demo_counts),
            "settings": p.SETTINGS,
            "candidate_rule_family": "row masks from color ranks, fixed colors, exact/threshold frequencies 1..40, first/last 1..8 selected rows, positions, parity, halves, row statistics, and partial intermediates",
        },
        "cases": cases,
        "profile_failures": profile_failures,
        "query_changing_survivors": query_changing,
        "distribution_equivalent_survivors": equivalent,
        "coverage": {
            "minority_colors": sorted(minority_colors),
            "distinct_selected_masks": len(selected_masks),
        },
        "certificate_tamper_checks": _tamper_checks(),
        "public_projection_checks": _public_projection_checks(),
        "racket": racket,
        "limits": "Finite candidate search; absence of a survivor is not universal uniqueness.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=64, help="audit seeds 0..N-1")
    parser.add_argument("--demo-count", type=int, action="append", dest="demo_counts")
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds < 1:
        raise SystemExit("--seeds must be positive")
    counts = tuple(args.demo_counts or (2, 3, 6))
    report = audit(seeds=range(args.seeds), demo_counts=counts, use_racket=args.racket)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    summary = {
        "out": str(args.out),
        "cases": report["cases"],
        "profile_failures": len(report["profile_failures"]),
        "query_changing_survivors": len(report["query_changing_survivors"]),
        "distribution_equivalent_survivors": len(report["distribution_equivalent_survivors"]),
        "tamper_checks_passed": report["certificate_tamper_checks"]["all_rejected"],
        "projection_checks_passed": report["public_projection_checks"]["all_passed"],
        "racket_checked_pairs": report["racket"]["checked_pairs"],
    }
    print(json.dumps(summary, sort_keys=True))
    if report["profile_failures"] or report["query_changing_survivors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
