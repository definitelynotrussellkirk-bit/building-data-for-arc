# ec9340d27f7e

Version `3.0.0`; rule hash `80ec61287499`.

## Rule

For every zero cell whose immediate horizontal neighbors are the same nonzero color, fill the zero with that color. Read matches from the original grid. Unequal endpoints, vertical matches, wider gaps, and occupied midpoints remain unchanged.

## Ordinary distribution

The deterministic eight-profile curriculum contains four canonical anchors and four contrast profiles. Across every three consecutive examples, at least one complete contrast bundle appears. The anchors cover all four canonical dimension/target signatures; contrast scenes jointly expose equality, horizontal orientation, one-cell adjacency, zero-center, exhaustive application, and color independence.

Public exact axes are only:

- `grid_h` in 5..8,
- `grid_w` in 7..10,
- `n_gaps` in 3..5.

All Cartesian combinations are feasible and observable. Unknown or invalid controls fail closed.

## Contracts

- `self_check`: recomputes structural invariants from cells.
- `observe_overrides`: recovers all exact axis values.
- `strict_canonical_like`: recognizes empirical canonical profiles.
- `rule_mirror`: Python mirror of the immutable rule.
- `SEMANTIC_WITNESSES`: nine named teaching witnesses.
- `SEMANTIC_RIVALS`: seven executable rival rules.
- `lesson_identifiable`: checks that demonstrations eliminate every declared competitor.
- `schedule_profile`: auditable deterministic curriculum schedule.

## Evidence

The official after battery is 12/12 green. The semantic gate reports 299/600 strict anchors, 9/9 witnesses firing, 9/9 rival claims verified, and 12/12 lessons identifiable. The override gate accepted 4,860/4,860 draws with zero findings. Task-local pytest has 14 passing tests.

Use `workspace/semantic_probe.py` for a fast machine-readable census; see `workspace/README.md`.
