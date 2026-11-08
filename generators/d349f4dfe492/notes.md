# Working notes: d349f4dfe492

## Review `review-0bad157f45c8660d`

Baseline generator SHA-256:
`a7075795e626809b45f12a910c794d2dfe52b2c8c0ae2d9c61a9afe41bd7355e`.
Final generator SHA-256:
`9a66f07f38847dc9e4bda120c7679107dde7ce63fda7e52963e71849d276e6ca`.

The baseline lacked `RULE_HASH`, declared inert/aliased axes, restricted
advertised seed-count overrides by difficulty, did not enforce its stated
non-overlapping-shell invariant, rejected repeated colors, and had no executable
semantic rivals or lesson-identifiability hook.

The replacement pins the existing authority, exposes only exact observable
dimensions/count, constructs separated seed anchors without retry loss, allows
repeated colors, mirrors the rule in Python, and cycles three teaching profiles
so every three-demo window refutes the retained rival family. A one-seed input
is deliberately a border-clipping lesson; this is a bounded teaching grammar,
not a restriction on where the selected authority is mathematically defined.

Final retained evidence:

- 12/12 after-battery stages green;
- 9/9 task tests passed;
- 2,880/2,880 complete exact-axis combinations passed;
- 90/90 cyclic lesson starts had no surviving declared rival;
- 27/27 generated examples matched supported Racket execution;
- 300/300 production lessons had no declared ambiguity and contained 644 unique inputs.

Reusable probes and their commands are documented in `workspace/README.md`.
## Current reviewer considerations

Source SHA-256: `9a66f07f38847dc9e4bda120c7679107dde7ce63fda7e52963e71849d276e6ca`.

# Design decisions for `d349f4dfe492`

Final generator SHA-256:
`9a66f07f38847dc9e4bda120c7679107dde7ce63fda7e52963e71849d276e6ca`.
Selected authority hash: `e47d7c8767c3`.

## D1 — Preserve the selected authority

The canonical outputs consistently implement this rule: visit each nonzero seed
in row-major order, preserve the input, and paint each original-empty,
still-empty cell at Manhattan distance exactly two with that seed's color. The
Racket authority and canonical data were not changed. Instead, the generator now
pins `RULE_HASH`, supplies a pure Python `rule_mirror`, and independently checks
that mirror against supported Racket execution.

Rejected alternative: rewriting the authority to fit the baseline generator.
The baseline's weaknesses were in validation, metadata, and curriculum, not in
the selected transformation. Final parity was 27/27 generated inputs, and all
four canonical pairs match the mirror.

## D2 — Use a narrow, explicit teaching grammar

Ordinary inputs are rectangular ARC grids with background 0 and 1–5 nonzero
singleton seeds. Every pair of seeds must have Manhattan distance at least five,
which makes their closed radius-two influence zones disjoint. Repeated seed
colors are legal because the rule is per seed, not per distinct color.

The baseline described this separation but never checked it, and its
`_diamond_zone` helper was a 5x5 Chebyshev square. The replacement checker tests
the actual L1 geometry and rejects malformed/ragged/non-ARC cells. It also
requires the transformation to change at least one cell in the strict teaching
profile.

A one-seed input is intentionally restricted to a border seed. The selected
rule itself also makes sense for a centered singleton, but the current canonical
set has no singleton example, and the shared defect linter correctly demanded
semantic evidence for that minimal shape. Making the single-seed branch a named
clipping lesson keeps the advertised exact control while preventing an
unconstrained minimal-impostor path. This is a teaching-domain restriction, not
a statement that the authority is undefined elsewhere.

## D3 — Expose only exact, observable controls

The public axes are:

- `grid_h`: every integer 7–18;
- `grid_w`: every integer 7–18;
- `n_seeds`: every integer 1–5.

`observe_overrides` reconstructs all three from the returned grid. Unknown keys
reject, and no incompatibility declarations are needed: the minimum 7x7 board
can realize the four corners plus center with pairwise L1 distance at least six.
The complete Cartesian product was tested in `None`, `easy`, `medium`, and
`hard`: 2,880/2,880 draws passed.

Rejected alternatives:

1. Keep palette, density, texture, position-bias, palette-size, and
   distinct-color axes. Several were aliases, fixed singletons, ignored, or not
   independently recoverable from the returned grid.
2. Keep band-local `n_seeds` limits. That made a declared exact control reject or
   clamp valid advertised values.
3. Use retry placement. A constructive five-anchor layout proves support and
   avoids silent partial placement.

Limitation: exact overrides use a small universal anchor family on tight boards,
so they prove contract support rather than broad spatial diversity. Ordinary
scheduled draws provide the curriculum diversity.

## D4 — Use a three-profile cyclic curriculum

`EXAMPLES_NEEDED = 3`, and `sample_index mod 3` selects:

1. `canonical_anchor`: canonical-sized, non-border, includes color 1;
2. `clipped_border`: outer-border seeds expose clipping and extra seed counts;
3. `repeated_colors`: at least three seeds by default, repeated colors, and a
   non-border/full-shell witness.

Every consecutive three-example window therefore contains all profiles,
regardless of starting residue. The profile schedule is deterministic because
lesson assembly is deterministic and needs reproducible witness coverage.
Difficulty changes dimensions and default counts, not the underlying rule.

Rejected alternative: random independent profile choice. It produced acceptable
marginal frequencies but allowed unlucky three-demo lessons to omit clipping or
repeated-color evidence. The cyclic schedule gives a direct per-lesson
guarantee.

## D5 — Separate clipping from the other profiles

An intermediate candidate used corner anchors as a universal fallback and made
every ordinary profile contain a border seed. That would teach an accidental
“all examples are clipped” prior. The final ordinary schedule reserves the outer
border for `clipped_border`; `canonical_anchor` and `repeated_colors` use
non-border seeds and include a fully visible shell.

Measured final 100-draw distribution per band:

- 34 canonical-anchor, 33 clipped-border, 33 repeated-colors;
- exactly 33 draws with clipping;
- exactly 33 draws with repeated colors;
- 100/100 strict inputs.

The exact-override path may fall back to universal anchors when a caller asks for
a tight board/count combination; that path serves control-contract coverage,
while ordinary lessons retain the profile distinction.

## D6 — Make plausible shortcuts executable

Seven named rivals are retained as callables:

- filled radius two;
- Chebyshev radius-two shell;
- axial-only distance two;
- skip border seeds;
- first two seeds only;
- deduplicate equal-colored seeds;
- ignore color 1.

The last four fit every canonical pair and are explicitly listed as
`CANONICAL_SHORTCUTS`. `lesson_identifiable` requires the demonstrations to
refute every declared rival. `SEMANTIC_WITNESSES` and `WITNESS_RIVALS` let the
shared gates verify the same contract rather than relying on prose.

Rejected alternative: count only witness frequency across a large sample. High
marginal frequency does not prove that each assembled lesson contains the
needed evidence. The task-local probe therefore tests every cyclic start in its
bounded schedule, and the production census checks 100 complete lessons per
band.

Limitation: this is finite adversarial coverage. A future plausible program
should be added to the declarations and probes; the current result is not a
proof against all hypotheses.

## D7 — Build reusable source-bound probes

`workspace/contract_probe.py` checks canonical parity without opening Racket,
full exact-axis support, deterministic/fresh/RNG-pure behavior, actual declared
shortcut calibration, every cyclic lesson start, and distribution/witness
counts. `workspace/racket_parity_probe.py` uses only the supported apply command
to compare generated examples with the selected Racket authority.

Both reports include the selected generator SHA-256. They are intended for
future agents to rerun after any source change; a stale green report cannot be
mistaken for evidence about new bytes.

## D8 — Audit targets remained unchanged

`702b86fcc04c` has a reproduced validator defect: a 2x2 color-2 block with no
singleton passes `self_check`. `db4cb6bcf6fe` has a qualified contract omission:
`row_closure_only` fits all canonical examples but is undeclared; current sampled
lessons refuted it in all 6,000 windows. These are audit findings only, not part
of the allowed selected-task patch.
