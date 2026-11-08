# Task workspace

- `reference_probe.py` is an independent parser, label oracle, override observer,
  and reproducer for the `color_sort` and `row_sort` canonical shortcuts.
- `parametric/` contains the isolated proposed `gallery_gap` Racket prototype.

Neither tool is imported by the production generator. They exist so future
reviewers can reproduce the structural and lesson-level claims without trusting
production helpers.
