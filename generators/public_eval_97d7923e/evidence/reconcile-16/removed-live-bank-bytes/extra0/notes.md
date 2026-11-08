# Current design — public_eval_97d7923e

Canonical rule: nonzero vertical runs with equal endpoint colors and a uniform
other-colored interior are rods. Non-rod foreground cells form the detached
legend. For each legend color, its multiplicity is a one-based rank among rods
of that endpoint color ordered by interior length descending; recolor the chosen
rod's interior to the endpoint color. All three official demonstrations and the
official test gold match the general Python engine and protected Racket source;
there is no stored-grid lookup.

Episode parameter: `finish=rank_only|highlight_longest_selected`. The alternate
first derives the complete legend-ranked selected-rod set, then selects its
unique longest member and recolors that whole rod 9. The retained counterfactual
uses the globally longest raw rod, which the sampler constructively keeps outside
the selected set. This is a real A → selected rods/lengths → B dependency.

Sampler: three endpoint colors, three rods per color, different ranks, varied
palette/columns/vertical positions, and a multi-row legend that defeats counting
only the first row. It covers 24–30 dimensions, independently shuffled query
presentation, and an exact 30×30 final stress query. Selected lengths are
unique. The globally longest rod is unselected. Two demonstrations distinguish
the finite settings. Supported counts are 2–6 demonstrations and 1–4 returned
queries from an always-materialized four-query private bank.

Evidence is bounded to the official labels, ten executable rival rules, task-local
regressions, public-projection mutation checks and finite generated seeds. It is not a universal uniqueness claim.
Owner registration, native qualification, exact-source acceptance and any
training admission remain pending.
