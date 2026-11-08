# 71fd3c801ee1

Five separated, distinctly colored nonzero objects appear on a canonical 12×18 background-0 grid. For each object, compute the complete feature triple `(area, enclosed-hole count, reflection-symmetry class)`, where symmetry is `0=neither`, `1=row only`, `2=column only`, and `3=both`. Recolor every object whose **complete triple** is shared by another object to cyan (`8`); leave unique-triple objects unchanged.

The v3 curriculum makes the rule identifiable rather than teaching exact-shape duplication. Every ordinary generated grid has exactly one repeated complete triple represented by two different normalized outlines, plus one same-area/same-holes decoy with different symmetry and one same-area/same-symmetry decoy with different holes. Consequently, exact-shape, area-only, area+holes, and area+symmetry rivals each make an observable error on every sample.

Kind: `per_puzzle`. Version: `3.0.0`. Rule hash: `12f0cca6ed07`.

Validation evidence:

- `checks/after-final/checks/71fd3c801ee1_after_battery_summary.json`: 12/12 stages green against generator SHA-256 `84c5209072ace3fc80b87f45b23a08ce7ec313992d7e320e0923b2e97e119b5e`.
- `checks/lesson-census-final.json`: 300 lessons, 100 per difficulty band; zero ambiguous lessons, hook warnings, scoring errors, or declared-rival survivors.
- `generators/71fd3c801ee1/tests/test_generator_71fd3c801ee1.py`: 15 task-local regression tests.
- `generators/71fd3c801ee1/workspace/feature_probe.py`: independent feature/rival probe for future reviews.

Approval remains catalog-controlled and is not changed by this repair.
