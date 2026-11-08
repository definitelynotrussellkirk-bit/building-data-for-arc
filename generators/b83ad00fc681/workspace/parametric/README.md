# Parametric keyed-dictionary stamped clusters

Settings:

- `finish=stamp_only` — exact selected canonical Racket bytes.
- `finish=highlight_largest_stamped_cluster` — stamp every visible keyed prototype,
  binarize the produced occupancy, select its unique largest 4-connected cluster,
  and recolor that complete cluster 9.

The sampler supports 2–6 demonstrations and 1–4 queries; production use for this
round always requests four queries. Inputs are setting-neutral, count-prefix
stable, and include an exact 30×30 query. `audit.py` performs protected-Racket
label parity, finite-rival teaching checks, public one-query projection checks,
and emits source-bound evidence.

The causal counterfactual uses same-color components of the stamped output
instead of binary occupancy. It selects only a color fragment and changes the
final grid on the retained qualified witness.
