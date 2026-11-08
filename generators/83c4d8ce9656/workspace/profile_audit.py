"""Small reusable census for future reviewers of generator 83c4d8ce9656."""
from __future__ import annotations

from collections import Counter


def audit_census(generator, *, seeds: int = 10) -> dict[str, object]:
    """Exercise one full four-profile block per seed and difficulty band.

    The report is deliberately plain JSON-compatible data so future agents can
    call it from tests, a REPL, or a review script without importing the full
    repository checker stack.
    """
    profile_counts: Counter[str] = Counter()
    self_check_failures: list[dict[str, object]] = []
    observer_mismatches: list[dict[str, object]] = []
    lesson_failures: list[dict[str, object]] = []
    canonical_profile_hits = 0
    rival_refuted = {name: False for name in generator.LESSON_COMPETITORS}
    draws = 0

    for band in ("easy", "medium", "hard"):
        for seed in range(seeds):
            demos = []
            for sample_index in range(generator.EXAMPLES_NEEDED):
                grid = generator.generate(seed, sample_index, difficulty=band)
                draws += 1
                expected_profile = generator.schedule_profile(seed, sample_index, band)
                observed_profile = generator.observe_overrides(grid)["scene_profile"]
                profile_counts[str(observed_profile)] += 1
                errors = generator.self_check(grid, difficulty=band)
                if errors:
                    self_check_failures.append(
                        {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "errors": errors,
                        }
                    )
                if observed_profile != expected_profile:
                    observer_mismatches.append(
                        {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "expected": expected_profile,
                            "observed": observed_profile,
                        }
                    )
                if not generator.strict_canonical_like(grid):
                    canonical_profile_hits += 1
                output = generator.rule_mirror(grid)
                pair = {"input": grid, "output": output}
                demos.append(pair)
                for name, rival in generator.LESSON_COMPETITORS.items():
                    rival_refuted[name] = rival_refuted[name] or rival(grid) != output

            query_grid = generator.generate(
                seed, generator.EXAMPLES_NEEDED, difficulty=band
            )
            query = {"input": query_grid, "output": generator.rule_mirror(query_grid)}
            reasons = generator.lesson_identifiable(demos, query)
            if reasons:
                lesson_failures.append(
                    {"band": band, "seed": seed, "reasons": reasons}
                )

    return {
        "draws": draws,
        "profile_counts": dict(profile_counts),
        "self_check_failures": self_check_failures,
        "observer_mismatches": observer_mismatches,
        "lesson_failures": lesson_failures,
        "unrefuted_rivals": sorted(
            name for name, was_refuted in rival_refuted.items() if not was_refuted
        ),
        "canonical_profile_hits": canonical_profile_hits,
    }
