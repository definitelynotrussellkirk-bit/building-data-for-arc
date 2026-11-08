# Working notes: 323fded12174

## Current parametric proposal

The separate `workspace/parametric/` family preserves the exact Catalog source
for `rank_by=occupancy`. For `rank_by=anchor_color`, first measure nonzero row
occupancies and select the unique densest row; its unique most frequent nonzero
color becomes the scoring cue. Count that color in every original row and
stable-sort descending, preserving each complete row and its column positions.
The final highest-scoring row can differ from the anchor. This is an
input-derived selection dependency, not iterative physical simulation.

This proposal extends the input grammar separately from production: 3–30 rows,
5–30 columns, at least three nonzero colors, foreground and background in every
row, and a unique densest anchor with at least two foreground colors and a unique
nonzero mode. Lower-row occupancy ties and target-count ties are permitted and
explicitly taught. Ambiguous anchor or anchor-mode ties are outside this declared
grammar. The production tie restriction described below remains intact.

The API supports 3–6 demos and 1–4 queries, defaulting to three and four. Every
request first constructs the same six-demo/four-query input bank for its seed;
settings and requested counts do not affect sampling. Three constructed core
scenes teach the selected reference, modal foreground cue, stable ties, count
versus presence or exact fraction, and complete-row preservation. Positions,
palettes, layouts and count profiles vary. Seed zero retains a literal 3×5
minimum query; first queries vary elsewhere. Every fourth query is substantive
30×30 content, with 517–624 foreground cells in the bounded sampler.

Final focused checks comprise 31 family tests, 12 independent audit tests and
52 export tests. The independent audit checks executable Python/Racket meanings,
freezes demonstration fits before comparing queries, and fails closed on errors.
Its six episodes (seeds 0/17 with three demos, 101 with six; both settings) used
407 protected evaluations and verified 48 intended labels against 20 extra
interpretations. Every anchor-color rival is refuted within the first three
demos. Eleven default-setting interpretations are equivalent and agree on all
queries. No supported lesson defect was observed in this finite audit, and no
synthetic failure is claimed. These checks do not prove unrestricted uniqueness.

The Python sampler completed 144/144 requests across seeds 0–23, yielding 240
unique inputs, 96 unique queries, 41 core count profiles and all nine target
colors. Maximum observed retries were two of 128 for teaching construction and
two of 32 for novelty. Its 480 claim-labeled pairs are Python observations;
native qualification and execution remain the separate label authority.

`checks/323fded12174/` retains the bounded sampler, independent audit, exact
public/private exports, native qualification/execution, causal witnesses and
final source-binding comparison. Two controller examples hold four queries
each; eight actor files each contain one masked query and the unchanged demos,
without total-count hints. Public IDs depend only on exact visible bytes.
Reusable task-local tools include the independent audit, strict exporter and
native example builder; checks-only tools replay the canonical shortcut,
inspect sampler diversity and compare export/qualification/witness bindings.

### Assigned canonical shortcut question

The strongest tested original shortcut is to stable-sort rows first by the
number of different nonzero colors, then by their dominant-color frequency.
It agrees with all four canonical training demonstrations because those rows
are monochromatic. `checks/323fded12174/canonical-shortcut.json` retains ten
protected Racket evaluations: both complete programs on the four demonstrations,
then one exact real production draw. Fitting is frozen before the witness.

That generated 5×8 input is
`[[0,0,0,7,7,7,7,7],[7,7,7,3,2,5,0,0],[0,0,0,0,0,7,0,0],`
`[0,0,0,0,7,7,7,0],[0,7,7,3,3,2,2,5]]`.
Its row occupancies are `[5,6,1,3,7]`. Canonical sorting returns original row
indices `[4,1,0,3,2]`; the rival returns `[1,4,0,3,2]`. Rows 1 and 4 both use
four foreground colors, but their dominant counts are three and two. The
witness is emitted by production with seed 323, sample index 0, medium
difficulty, profile `5x8x4`, and layout `runs`; `self_check` returns no errors.
The existing declaration-driven `workspace/rival_probe.py` also passed a fresh
bounded 12-draw/12-cyclic-lesson check of all three declared rivals. Its old
108-draw result below is inherited evidence and was not rerun.
The proposed family also emits distinguishing color-priority cases, as its
default-setting native audit confirms. Its unique-anchor-mode grammar excludes
this particular historical-style 5×8 literal, whose densest row has a modal tie;
the exact proposed examples are retained separately in the audit and exports.

### Authority and handoff

Production version 2.1.0 and SHA-256
`035b7441095f4343524ddf1b8f6dee67e9b5ab013024dc530a1d43d69eb6785e`
remain unchanged. Catalog rule fingerprint is `d6c95e66f9b7`; the exact canonical
program's SHA-256 is
`57d3652e70f204f02b9196f6c7715a2272f00d9757051e42c4075117203cfa97`.
There are no open findings in the imported source's review index. This review
does not change its approval or run the old production test battery. The proposed
family has its own tests, source inventory and protected execution evidence.

After reviewing and integrating the chosen bytes, the owner must run native
qualification and fresh acceptance on the exact integrated source. Reviewer
readiness does not grant owner acceptance or training admission. Counts, seeds,
retry bounds and finite rival coverage remain explicit in the current evidence.

## Final repair (generator 2.1.0)

The Racket authority remains unchanged: stable-sort complete rows by descending
count of nonzero cells. The imported 1.2.0 generator varied row occupancy but
fixed dimensions/palette behavior, advertised dead and overlapping axes,
accepted unknown overrides, had no `RULE_HASH`, and had no executable semantic
contract. Its baseline battery finished with 7 green, 2 advisory, and 3 failed
stages (`lint`, `defect_lint`, `override`).

The repaired generator exposes only two truthful controls:

- `profile`: one of the five exact canonical `(height, width, nonzero colors)`
  profiles;
- `cell_layout`: recoverable `runs` or `scattered` occupied-cell placement.

Every draw has pairwise-distinct occupancies, is not already sorted, matches an
exact canonical profile, and contains two full-palette top rows. The densest row
is color-balanced; the second-densest row is color-skewed and occurs first in
the input. This constructively refutes all declared canonical-fitting rivals:

1. dominant nonzero-color frequency;
2. mixed rows first, then dominant frequency;
3. distinct nonzero-color count first, then dominant frequency.

A first repair mixed only the densest row. Self-audit found that this admitted
rival 2 exactly, so that version and its solve were retained only as prior
evidence under `checks/`; 2.1.0 uses the adversarial top pair instead.

## Reusable probe

`workspace/rival_probe.py` discovers rival declarations from the generator,
checks all five canonical pairs, samples every difficulty band, and tests all
cyclic two-demo lesson starts. It exits nonzero if a declared rival survives,
a witness misses, a generated input is invalid, or a lesson is unidentifiable.

## Deliberate restriction

Generated occupancies are unique, matching the available canonical curriculum.
The unchanged authority is stable under ties, but tie behavior is not separately
taught by this generator because no canonical pair establishes that extension.
## Current reviewer considerations

Source SHA-256: `035b7441095f4343524ddf1b8f6dee67e9b5ab013024dc530a1d43d69eb6785e`.

# Decisions for `323fded12174`

## D1 — Preserve the Racket authority

**Decision.** Leave the canonical Racket rule unchanged and pin `RULE_HASH = "d6c95e66f9b7"` in the generator.

**Rationale.** Rule smoke, grammar, Racket lint, and authority-sync were already green at baseline. The defects were in the Python generator contract and lesson distribution, not in the stable descending occupancy sort. Changing the authority would have enlarged scope without evidence.

**Rejected alternative.** Modify the rule to break occupancy ties or to use color statistics. Canonical outputs and the selected bank already establish row occupancy as the authority; such a change would be unjustified.

## D2 — Use one composite canonical profile axis

**Decision.** Replace independent height, width, palette-size, and color-count controls with one `profile` axis containing the five exact canonical `(height, width, nonzero colors)` tuples:

- `5x8x4`
- `5x8x5`
- `6x10x3`
- `7x8x4`
- `7x9x5`

**Rationale.** The original independent axes implied a Cartesian product the generator could not honor. A composite profile is truthful, keeps every advertised value constructive, and guarantees support for each canonical shape/palette regime. Difficulty changes probabilities only; every band retains full support.

**Rejected alternatives.** Keeping independent dimensions and declaring hundreds of incompatibilities would be hard to audit and would preserve a misleading API. Randomly choosing arbitrary shapes outside the canonical envelope would increase nominal diversity while weakening task anchoring.

## D3 — Retain one observable layout axis

**Decision.** Keep only `cell_layout = runs|scattered`. `runs` places each row’s occupied cells contiguously. `scattered` uses a left run plus a last-column outlier, so at least one row has a visible gap and the value can be recovered from pixels.

**Rationale.** Layout does not change the rule but creates meaningful visual diversity. Both values are constructive for every profile and reachable in every difficulty band. `observe_overrides` can distinguish them exactly.

**Rejected alternatives.** The old “texture” labels did not affect generated pixels. A probabilistic scatter pattern could accidentally look contiguous, making exact override checking flaky; the chosen construction is deterministic at the semantic level while retaining random placement/palette variation.

## D4 — Construct unique occupancies and an unsorted input

**Decision.** Use pairwise-distinct occupancies. Pin the largest two legal values to `width-1` and `width-2`, sample the remainder from `1..width-3`, shuffle, and then ensure the second-densest row precedes the densest row.

**Rationale.** Distinct counts eliminate accidental tie ambiguity. Pinning the top two values guarantees enough occupied cells to use the full palette in every canonical profile. The source-order constraint guarantees the input is not already sorted and is essential for defeating stable color-priority rivals when their keys tie.

**Rejected alternatives.** Rejection-sampling random occupancy lists would make coverage and determinism harder to reason about. Allowing identity inputs would teach nothing. Generating ties would assert an extension not demonstrated by the canonical curriculum.

## D5 — Use an adversarial full-palette top pair

**Decision.** Make the densest row use every palette color with frequencies as balanced as possible. Make the second-densest row use every palette color but maximize the first color’s frequency. Lower rows are monochromatic.

**Rationale.** All canonical rows are monochromatic, so color-frequency rules fit them. The adversarial top pair separates occupancy from:

1. dominant nonzero-color frequency;
2. “mixed rows first, then dominant frequency”;
3. “number of distinct nonzero colors first, then dominant frequency.”

Both top rows have the same maximum color diversity. The skewed second row either has a larger dominant count than the densest row or ties it and wins by stable source order, while the intended occupancy rule must put the densest row first.

**Rejected alternatives.** Mixing only the densest row was tried first and retained as failed evidence; it admitted “mixed rows first, then dominant count.” Random multicolor assignment could occasionally agree with a rival. The final construction refutes the rivals by design on every draw.

## D6 — Make the semantic contract executable

**Decision.** Declare the three rivals in `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`; declare `top_pair_refutes_color_priority` in `SEMANTIC_WITNESSES`; require two demonstrations; and validate labels plus rival elimination in `lesson_identifiable`.

**Rationale.** Narrative notes are not enforceable. These hooks let the shared semantic gate and lesson census measure the claimed curriculum. All three rivals are first checked to fit all five canonical pairs, then checked against generated data.

**Rejected alternatives.** Declaring only the easiest dominant-count rival would have hidden the stronger mixed-row shortcuts found during self-audit. Treating individual witness frequency as sufficient would not verify complete lesson assembly.

## D7 — Strictly validate the advertised grammar

**Decision.** `self_check` requires a nonempty rectangular ARC grid, one exact canonical profile, at least one zero and one nonzero per row, pairwise-distinct occupancies, and a non-identity row order. Unknown or malformed override values raise `ValueError`.

**Rationale.** The target rule is trivial on already sorted inputs and can be obscured by empty/full rows, malformed cells, or tied counts. The validator prevents those cases and makes the contract falsifiable. Unknown-key rejection prevents typos from silently reading as successful overrides.

**Rejected alternatives.** Silently ignoring extra keys was a baseline defect. Returning invalid “negative textures” from the production generator conflates adversarial testing with training data; malformed negatives belong in tests, not the lawful distribution.

## D8 — Build a declaration-driven reusable probe

**Decision.** Add `workspace/rival_probe.py`. It imports the current generator, discovers all current shortcut/competitor/witness declarations, verifies each shortcut on all canonical pairs, samples all bands, and checks every cyclic two-demo lesson start.

**Rationale.** A copied rival-name list would drift as the generator evolves. The probe’s failure conditions match the intended maintenance contract and give future agents a fast semantic check independent of the larger battery.

**Measured final result.** With `--samples-per-band 36 --seed-base 323`, it checked 108 unique inputs and 108 cyclic windows with no invalid input, rival agreement, witness miss, or unidentifiable lesson (`checks/rival-probe-v2.json`).

## D9 — Preserve the tie limitation explicitly

**Decision.** Do not generate equal-occupancy rows in version 2.1.0.

**Rationale.** The Racket authority is stable under ties, but the five canonical pairs do not establish that behavior. Teaching only what the canonical evidence supports is safer than broadening the inferred rule. This is a distribution restriction, not an authority change.

**Future extension.** If canonical or policy evidence explicitly confirms stable tie behavior as teachable, add a separate profile/witness for ties and a rival that reverses equal-count rows; do not silently mix ties into the current curriculum.
