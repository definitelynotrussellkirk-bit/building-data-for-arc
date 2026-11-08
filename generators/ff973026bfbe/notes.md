# Working notes: ff973026bfbe

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `0148254f12ff4bfc72a1e9968ed38bff74039f965e3f345777a66cf66647bcea`.

# Decisions for `ff973026bfbe`

## D1 — Keep the executable authority unchanged

The selected Racket rule was internally consistent with all canonical labels
and passed rule smoke and authority synchronization before repair. The apparent
"left border" language in legacy prose is a canonical-fitting shortcut, not a
reason to narrow the executable rule: the rule activates every row containing a
colour-1 cell at any column. I therefore pinned its existing hash
`0f7e32eb6ec7` and changed no Racket/canonical data.

Rejected alternative: rewrite the rule to use only column-0 blue markers. That
would make the prose self-consistent but would alter established executable
authority and discard the more general rule without evidence of a label defect.

## D2 — Replace metadata-only axes with recoverable controls

The baseline listed palette, density, position, and texture controls that did
not independently affect or recover from the returned grid. Degenerate texture
paths also bypassed dimension overrides. I replaced them with eight exact axes:

`grid_h`, `grid_w`, `n_row_marks`, `n_col_marks`, `n_red_decoys`, `n_neutral`,
`row_marker_mode`, and `distractor_color`.

Every one is reconstructed by `observe_overrides`; all legal boundary values
are accepted in every difficulty band, invalid types and unknown names raise
`ValueError`, and the generator verifies its own realized overrides before
returning. The exhaustive public override stage is green.

Rejected alternative: retain texture aliases for compatibility. They had no
honest independent semantics and multiplied impossible joint combinations, so
removing them was clearer than documenting exceptions around dead controls.

## D3 — Restore canonical palette and size support

Every canonical input uses four colours: background 0, marker colours 1 and 2,
and one unrelated colour. The baseline emitted only three. The repair places
1–3 cells of one selected neutral colour 4–9 on inactive non-top rows. This
keeps the distractor inert while making the input role visible and exact.

A linked canonical `(height, width)` profile is selected every fourth default
sample, cycling through `(8,9)`, `(7,10)`, `(9,8)`, `(8,11)`, and `(7,9)`.
Other samples retain difficulty-aware dimensions over the declared 7–14 by
8–14 domain. Final profile-floor evidence found 18 exact canonical profiles in
60 draws and at least one in each band.

Rejected alternative: force every sample to canonical dimensions. That would
pass the profile floor but unnecessarily collapse size diversity.

## D4 — Schedule semantic counterexamples, not merely random ones

Two rules fit all 5 canonical pairs:

1. `left_border_rows_only`: only rows with blue at column 0 are active.
2. `all_red_columns`: every column containing red anywhere is active.

The source-bound schedule repeats three profiles:

1. border blue markers plus an off-top red distractor;
2. scattered blue markers with no off-top red distractor;
3. scattered blue markers plus an off-top red distractor.

Thus any three examples retained from four consecutive pairs include an
off-border-blue witness and an off-top-red witness. The task test exhaustively
checks starts 0–11 and all four query positions. `lesson_identifiable` repeats
that requirement on materialized labelled demonstrations.

Rejected alternative: rely on independent random draws. Witness frequency can
look healthy while a complete lesson still omits one condition; source-bound
scheduling makes the lesson guarantee inspectable.

## D5 — Keep the grammar strict enough to be observable

Blue markers use distinct non-top rows. In `border` mode every blue is at
column 0; in `scattered` mode every blue is strictly off-border. Top-row red
markers use distinct columns. Off-top reds use distinct non-active columns, so
they produce a clean counterexample to the all-red-columns rival without being
painted by the intended rule. Neutral cells sit on inactive rows so their role
is unambiguous. Colour 3 is output-only.

The minimum shape 7×8 leaves enough space for the hardest legal joint override:
five blue rows, five active columns, two red distractors, and three neutral
cells. The construction was tested at those exact boundaries in every band.

Rejected alternative: keep caller-opt-in no-marker/no-wall degenerates. They do
not teach the selected rule and make advertised counts and exact overrides
unobservable.

## D6 — Testing and reusable tooling

I wrote task tests before changing production code. Against the baseline they
produced 17 expected failures and 7 passes (`checks/task-tests-red.log`); after
the repair all 24 pass. The tests cover canonical acceptance, independent
oracle parity, exact overrides, invalid requests, canonical profiles/palette,
cyclic lesson retention, executable rival witnesses, malformed inputs, and
determinism.

`workspace/reference_probe.py` is intentionally independent of the generator's
rule helpers. It loads canonical pairs portably, spells the intended rule and
two rivals in Python, provides exact witnesses, and emits a compact per-band
distribution audit. Its final 40-sample-per-band run used seeds `1700+i` and
sample indices `i` for `i=0..39`; all 120 grids passed `self_check`, every input
used four colours, and both witnesses appeared in every band
(`checks/reference-probe-final.json`).

## D7 — Lesson assembly and evidence boundaries

Production lessons use three demonstrations and one query. The large census
requested starts 0–99 separately for easy, medium, and hard, using the report's
SHA-derived seed recipe. It checked 300 lessons, 1,200 unique inputs, and every
hold-one-pair-out rotation. Production ambiguities: 0/300. Rotation ambiguities:
0/1,200. Materialization, hook, and scoring errors: all zero.

This establishes the declared rivals over the measured sampler only. It does
not prove unique induction against every possible rule, and it does not enumerate
new draws beyond the report's starts.

## D8 — Remaining domain restriction

The grammar does not emit a single scene containing both a border blue marker
and an off-border blue marker. A mode-conditioned rival could therefore agree
with every canonical and generated example yet ignore border markers only when
an off-border marker is present. This is a genuine coverage limitation, but it
does not create ambiguity on generated queries because those queries share the
same observable mode. Supporting an exact `mixed` axis would require either a
joint constraint (`n_row_marks >= 2`) or a different recoverable parameterization;
I left that expansion explicit rather than weakening the exact-override contract.

## D9 — Source and provenance

Final changed task paths are:

- `repo/generators/ff973026bfbe/generator.py`
- `repo/generators/ff973026bfbe/tests/test_generator.py`
- `repo/generators/ff973026bfbe/workspace/reference_probe.py`

No shared source, audit-target source, Racket rule, or canonical row changed.
The initial full after-battery process was interrupted by the command-interface
duration ceiling after three green stages; the public hash-bound `--resume`
path completed the remaining nine stages, yielding a 12/12-green aggregate.

## D10 — Native parametric column-policy family (review-22c1c41413475c9e)

The production generator and selected canonical Racket authority remain
unchanged.  A native sidecar under `workspace/parametric/` now exposes one
meaningful episode-fixed parameter:

- `all_top_markers` is the byte-exact canonical default: collect every row
  containing blue (`1`), collect every top-row red (`2`) column, and paint the
  full Cartesian product green (`3`).
- `signal_ranked_marker` first identifies the unique neutral-colour object,
  counts its cells, treats that count as a one-based rank among the top-row red
  markers, then paints only the ranked column across the blue-marked rows.

This is a real sequential dependency: **A** measures the signal object;
**intermediate** is its input-dependent cell count/rank; **B** cannot select the
output column until that rank is known.  The protected-Racket counterfactual in
`checks/ff973026bfbe/causal/witness.json` changes the rank from 3 to 4 on the
same input and changes 12 final cells.

The family uses matched inputs across settings, supports 2–6 demonstrations
and independently prefix-stable 1–4 queries, and always has four distinct query
constructions.  Query dimensions are 14×18, 19×23, 24×27 and 30×30; the 30×30
case has twelve active rows, fourteen candidate columns, a bottom-touching
signal object, and left/right/top boundary contacts rather than padded empty
space.

The first two demonstrations use signal ranks 2 and 5, with row counts 4 and 3,
so they distinguish the two settings and reject the measured shortcut set:
first/last/middle marker, rank from right, rank+1, blue-row-count rank, fixed
ranks 2/5, all-red-columns, and left-border-rows-only.  The reusable
`workspace/parametric/audit_lessons.py` checked 128 seeds, both settings and
2/3/6 demonstrations: 768 episodes, 5,888 labelled pairs, 768 exact 30×30
stress pairs, and no harmful survivor among those finite rivals.

Native qualification covered both settings at seeds 0 and 17 with three demos
and four queries: four jobs, 28 retained labels and 40 protected-Racket
executions.  Qualification execution SHA-256 is
`3cf0013029bb89eced69dfd1c6c249622adeaf8b03eceb93dfa6001679682a54`.
The source inventory remains reviewer-reported and training admission remains
false.  Exact-byte owner integration, native requalification and fresh
acceptance are still required.
