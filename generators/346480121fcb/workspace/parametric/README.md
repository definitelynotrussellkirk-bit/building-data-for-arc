# Selector interpretation family

The header and transform semantics remain those of canonical `346480121fcb`.
One episode-fixed parameter changes only how the upper-left selector is read:

- `selection_mode=color` (canonical): select the unique object whose color equals
  the selector marker.
- `selection_mode=area`: select the unique object whose cell count equals the
  selector marker.

Every scene contains both candidates and makes them different. The selected
object's cropped grid is the input-dependent intermediate; the upper-right key
then transforms that exact crop. Inputs are generated without consulting the
setting, so both settings receive byte-identical demonstrations and queries.

The first two demonstrations cross candidate scan order, size relation and color
rank, use distinct nonidentity transform keys, and uniquely identify either
setting. Query keys are drawn only from those demonstrated keys. Counts are
independent: 2–6 demonstrations and 1–4 prefix-stable queries are supported; the
qualification path uses two demonstrations and four queries. One query is a
substantive 30×30 scene spanning every body boundary with eight objects.

`public_turn()` exposes all demonstrations plus one unlabeled query and no
setting, program, future query, answer or total-count metadata. This source is an
authoring candidate only; owner native qualification/acceptance and training
admission remain separate.
