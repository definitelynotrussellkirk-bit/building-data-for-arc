# Current public-parent creation: 7b5033c1

Reviewer-ready authoring prototype, not an approved or accepted family. Owner registration, source review, native qualification and explicit acceptance remain required. Training admission is false. Immutable parent linkage is in workspace/public-parent.json.

## General rule
The modal color is background. Foreground cells form one induced four-neighbor open path. Start at its reading-order-first endpoint and follow adjacency to the other endpoint. Emit each visited cell's color as one row of a vertical column. Preserve separate runs of a repeated color; sorting by coordinates, components or color is not equivalent. Both original demonstrations and the supplied test gold match protected Racket execution. No stored input/answer lookup is used.

The inferred reading-order endpoint convention is an explicit extension consistent with all supplied labels, not a proof that the parent examples uniquely specify all possible orientations. Sampled grids have a unique modal background, an induced unbranched connected path, at least two color runs and no more than 30 path cells. Cycles, branches, disconnected fragments and longer-column outputs are outside this grammar.

## Meaningful fixed parameter
`mode=straighten` is byte-exact canonical. `mode=anchor_indexed_run` first traces and segments the path, measures the first run length k, and selects subsequent run (k-1) modulo the number of subsequent runs. It emits only that selected run as a vertical column. Both k and candidate order are input-dependent; repeated colors cannot be merged.

The source-bound witness has k=3 and run lengths [3,4,4,4,3,7,5]. Candidate index 2 yields four cells of color 2. Substituting k modulo count selects index 3 instead, yielding three cells of color 6. Union-canvas comparison counts four changed/missing cells. The two programs were executed through protected Racket and independently replayed.

## Sampling and exposure
Two minimum demonstrations constructively distinguish all twelve declared executable rivals. Counts support 2–6 demonstrations and 1–4 prefix-stable queries. Four distinct queries are always sampled before private presentation shuffling. Inputs are matched across settings; no settings, programs, seeds, answers, future inputs or total-count hints appear in public one-query views.

Ordinary profiles vary canvas geometry, endpoints, induced nonmonotone routes, run lengths/counts, repeated colors and nonzero backgrounds. Color zero may be foreground. The 30×30 query uses the full lawful 30-cell path/answer budget and spans an entire row or column, with multiple runs and repeated colors. It cannot span both full axes: that would need at least 59 path cells and hence an illegal 59×1 answer. The hard profile is a length-boundary stress case; nonmonotone topology is exercised by the other profiles, not claimed for this straight full-span boundary case.

## Checks and limits
36 task-local tests pass, including a literal nonmonotone example, original labels, negative inputs/counts, relocation, deterministic matched inputs, copy isolation and public first-turn invariance. Final bounded audit: 32 seeds × two settings, 640 visible pairs, 768 rival-lesson checks, 256 public-view checks and 64 full-size profiles. Protected audit: 40 generated labels plus 72 executable rival labels, then causal execution/replay. Four unapproved authoring-preflight jobs pass, and all 16 saved one-query public views pass independent validation. Eight ordinary-generator cases also match protected Racket.

Rivals cover alternate setting, row-major cells/components, reverse traversal, numeric color sort, merged global color counts, fixed first/last candidate, largest/smallest run, off-by-one modulo and anchor-only rendering. These are finite checks, not universal rule identifiability. Author self-review only; no independent reviewer agent was available. Owner acceptance remains pending.

## Current repeated-parent reconciliation

Preserve exact straighten/anchor-indexed programs, add exact length-addressed-run program and second constructor. Three demos retain incumbent first two and select an incoming demonstration rejecting all fixed run-address rivals without consulting queries. Queries alternate constructors by seed; strict one-query public projection and randomized prefix are added. Current evidence resides in evidence/repeat-fifth-union. Private native acceptance and root publication are separate.
