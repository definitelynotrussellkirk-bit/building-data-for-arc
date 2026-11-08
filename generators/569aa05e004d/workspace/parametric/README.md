# Parametric row/column closure for `569aa05e004d`

`closure_axis=rows_only` is the exact selected canonical program. It fills each
row/color interval only when that color occurs exactly twice in the input row,
starting from a fresh zero grid.

`closure_axis=rows_then_columns` performs that same row pass, then inspects the
resulting grid column by column. For each column/color occurring exactly twice
in the intermediate, it fills background cells of the inclusive vertical interval while preserving
the horizontal bars and any other Stage-A foreground. Three-occurrence columns are controls and are not filled.

The first two demonstrations are the supported minimum. They jointly contain a
multi-pair row, erased singleton/triple/blocker controls, two-row positive
closures, a three-row exact-count control, and a raw-input vertical decoy that
becomes three occurrences after Stage A. Inputs are identical across settings;
four private queries include wide, tall, boundary, dense, and 30x30 profiles.

`adversarial_audit.py` is the reusable bounded checker. Owner qualification and
acceptance remain separate from this reviewer-authored prototype.
