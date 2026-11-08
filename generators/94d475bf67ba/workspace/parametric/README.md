# Nested frames: native ownership-count family

`mode=all` returns the exact canonical Racket program, byte for byte.
`mode=largest_owned` first assigns each original zero to its smallest enclosing
operative frame, then counts those disjoint ownership regions. It fills only
the regions with the largest positive count, including every tied maximum.
Colored borders, exterior zeros and losing regions are preserved.

## Supported inputs and teaching

The separate parametric grammar contains two or three distinct-color exact
rectangular outlines, strictly nested with a full zero ring between them.
Grid dimensions are 7..30. The outer two frames are operative (both dimensions
at least three). A terminal two-wide outline is allowed and owns no zeros.
The existing production generator and canonical rule are unchanged.

Requests support 2..6 demonstrations and 1..4 queries independently; ordinary
lessons use three demonstrations and four queries. The first two demonstrations
construct an outer/middle tie and an innermost sole winner. Their dimensions,
rectangular aspect, translation, gaps and palettes vary by seed. At least one
palette is descending by nesting to distinguish color rank from geometric role.
Further demonstrations vary geometry and frame count. The queries cover the
7x7 minimum, a thin terminal outline, a large rectangular scene, and a full-canvas
30x30 scene with outer, middle, inner or terminal variants. No duplicate filler
or silently shortened batch is used; a collision fails explicitly.

The input streams are independent of setting and requested counts. With the
same seed, modes receive identical inputs; changing demonstration/query counts
preserves the corresponding prefixes. The two-demo context separates twelve
declared executable hypotheses, including the two actual settings. This is a
finite-rival guarantee, not unique induction against all possible programs.
Largest enclosed-zero-component selection is equivalent on this strict grammar.
No extra broken, touching or disconnected borders are admitted as distractors.

## Run the retained review/export tool

From an issued packet's outer directory, using its configured Python environment:

```bash
python3 review.py run python3 -m pytest -q generators/94d475bf67ba/tests/test_parameters.py
python3 review.py run python3 generators/94d475bf67ba/workspace/parametric/audit.py --out ../checks/94d475bf67ba/new-self-review
```

`audit.py` builds four episodes (two settings, seeds 0 and 17), executes every
label through the protected Racket runtime, checks finite teaching at the
two-demo minimum, and writes content-hashed public projections separately from
private settings, programs and answers. It retains an actual weak lesson in
which a single-tie-winner rule fits the only demonstration, plus the constructive
tie demonstration that repairs it. A cheap 36-request Python API sweep checks
counts and determinism separately; it is not reported as Racket execution.
Use a new output directory for every source revision.

`public_first/` contains only the demonstrations and the first query input.
This is the same first-turn content as a one-query request. The existing consumer
can call `public_challenge(episode, query_index=i)` to reveal the next input after
each answer, without a total-count, final-turn or future-input hint. No training
loop or turn controller is introduced. `public_grouped/` stores all four masked
queries for controller-side export checks. Never provide the private JSON to a
model acting as a solver.

## Native qualification and owner handoff

`adapter.py` loads only the adjacent `prototype.py`; `promotion.json` declares
the finite settings and exact resources. Python outputs are claims until the
native worker executes them through protected Racket. Build the source inventory
with the repository's existing `parametric manifest` helper, then qualify:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify 94d475bf67ba --out ../checks/94d475bf67ba/qualification --summary
```

After source integration, the owner reruns qualification and accepts those exact
live bytes through the existing native acceptance command. Neither this prototype
nor reviewer qualification grants acceptance or training admission. Once owner
acceptance is current, a normal four-query dataset command is:

```bash
python3 -m arcpuzzles parametric export 94d475bf67ba --count 4 --seed 17 --demos 3 --queries 4 --out var/datasets/nested-frame-owned
python3 -m arcpuzzles parametric verify-export var/datasets/nested-frame-owned
```

The causal witness uses the qualified `largest_owned` program and an executable
counterfactual that scores all contained zeros before subtracting inner ownership.
Both retain the true ownership write mask. On an innermost-winner example these
intermediates select different frames, and protected replay checks their different
final outputs. Intermediate descriptions remain authored explanations.
