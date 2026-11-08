# Working notes: dc382c7da9a9

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 native parametric completion

Built a native matched-input `distance_scope` family. The default
`all_equidistant` setting is the exact selected canonical Racket source. The
`shortest_path_midpoints` setting preserves the same wall-constrained BFS but
adds one global relay: stage A computes the input-dependent shortest distance
`L` between the red and green seeds; stage B paints an equidistant blank only
when its two distances also sum to `L`.

The sampler provides separate deterministic pools for 2–6 demonstrations and
1–4 queries, identical visible inputs across settings, stable prefixes, and a
true 30×30 fourth query. The first two demonstrations refute the opposite
setting, Manhattan distance, painting every shortest-path cell, first-tie-only,
one-step offset, and identity. A 16-seed bounded audit passed 160 lesson
prefixes and 960 executable-rival checks.

The retained counterfactual changes only the intermediate shortest distance
from `L` to `L+2` before stage B. It produces a different protected-Racket
output on a qualified query, directly demonstrating that the final mask depends
on the computed global relay. Production `generator.py` and canonical authority
remain unchanged.

The inherited regression test was made portable with `reviewer_support` rather
than fixed parent depth. Its 520-sample per-band census was reduced to four
complete 13-profile cycles (52 samples), preserving balance, uniqueness, oracle,
and cross-band checks while fitting the copied-runtime controller budget.
