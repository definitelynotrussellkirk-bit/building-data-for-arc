# Working notes: `54b040e4bd08`

## Intended rule and authority

Infer the smallest complete two-dimensional period from all visible nonzero
cells, then replace every zero with the corresponding tile residue. Nonzero
cells are preserved. The selected canonical Racket program was not changed;
normalized rule hash `55b239af8777` is pinned in generator `3.0.0`.

## Baseline findings

The imported `2.0.1` generator had no `RULE_HASH`, declared an unprobeable
`tile_w` axis, exposed dead/overlapping texture controls, and used an
acceptance-only validator. The retained before run rejected 0/56 destructive
mutations and the defect lint reported four dead helpful textures plus unlawful
negative fixtures in the normal texture domain. That before aggregate was
interrupted after recording the decisive failures; it is not reported as a
completed battery.

## Repaired distribution

The prior random rectangle sampler was replaced by a deterministic four-profile
teaching schedule. Two `2x3` profiles erase a row band and two `3x2` profiles
erase a column band. Every profile intersects the top-left period block. This
makes each four-pair window—and every choice of one held-out query—contain
visible counterexamples to:

1. repairing each row independently;
2. repairing each column independently; and
3. inferring the period globally but reading values only from the top-left
   period block.

The public contract is now five strict, reconstructible axes:
`grid_h`, `grid_w`, `tile_shape`, `vertical_margin`, and
`horizontal_margin`. All legal joint settings construct successfully; unknown,
wrong-type, and out-of-range controls fail loudly. Difficulty changes the
nonzero palette by a bijective rotation while leaving geometry and override
meaning unchanged.

## Validator and semantic contract

`self_check` requires a rectangular integer ARC grid, dimensions in the public
domain, exactly one solid interior zero rectangle, an allowed smallest complete
period (`2x2`, `2x3`, or `3x2`), and distinct nonzero tile residues.
`SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS` expose the
three executable rivals above. `lesson_identifiable` rejects a lesson whenever
any rival fits all demonstrations.

The strongest canonical-fitting shortcut is `top_left_tile`. The retained 6x9
counterexample under `counterexamples/top_left_tile_*` passes `self_check`; the
selected Racket output and an independent Python oracle fill all seven missing
cells, while the shortcut leaves five wrong cells. The first hand-authored
attempt with an incorrect right endpoint is intentionally retained as
`authoring_failure_wrong_endpoint.json` because the real Racket execution
rejected the mistaken expectation.

## Final evidence

Final generator SHA-256:
`cda17d37aca36d09fee0d424e3d959f19048f7c5f65e15637fc4d73fd20a835f`.

- portable focused task tests: 69/69 passed;
- source-bound battery with required query rotations: 12/12 stages green;
- exact-axis probe: 960/960 joint cases and 64/64 cyclic lesson cases passed;
- lesson census: 300/300 lessons, 1,200 unique pairs, and all 1,200 held-out
  query rotations had no surviving declared rival or execution error;
- final visible-only solve: 3/3 demonstrations on one revision, with earlier
  rule exposure declared `yes` and no reference consulted during solving.

## Remaining limits

The default production schedule intentionally favors thin adversarial bands and
does not default-sample `2x2`, although `2x2` is supported by exact overrides
and canonical validation. The declared rivals are high-value finite hypotheses,
not a proof of universal identifiability. Broader central rectangles and
additional learner hypotheses are the clearest future distribution extensions.
## Current reviewer considerations

Source SHA-256: `cda17d37aca36d09fee0d424e3d959f19048f7c5f65e15637fc4d73fd20a835f`.

# Decisions for `54b040e4bd08`

## D1 — Preserve the selected Racket authority

**Choice.** Keep the canonical transformation unchanged and pin rule hash
`55b239af8777`.

**Reason.** The authority reproduces all labeled canonical pairs. The observed
failures were generator-contract, validation, and teaching-distribution defects,
not a rule mismatch.

**Rejected alternative.** Rewriting the rule around a fixed `2xN` tile would
hide the `3x2` canonical case and change accepted behavior.

**Evidence.** Final rule smoke and authority-sync stages are green in
`checks/after-final/`; the exact Racket counterexample receipt is under the task
counterexample directory.

## D2 — Replace descriptive/aliased controls with five exact axes

**Choice.** Expose only `grid_h`, `grid_w`, `tile_shape`, `vertical_margin`, and
`horizontal_margin`, each strictly validated and recoverable from pixels.

**Reason.** The imported controls included an unprobeable `tile_w`, dead palette
aliases, and negative textures mixed into the ordinary domain. Exact controls
make failures measurable and portable.

**Rejected alternative.** Keeping `texture`, `density`, or `position_bias` as
single-token metadata would preserve labels that do not change the generated
input.

**Evidence.** `workspace/contract_probe.py` exhausts all 960 joint axis/band
settings; `observe_overrides` recovers every requested value. The final override
battery stage and 69-test suite are green.

## D3 — Use distinct tile residues

**Choice.** Give every tile residue a distinct nonzero ARC color.

**Reason.** Distinct residues make the smallest complete period observable and
prevent accidental smaller periods from aliasing the requested tile shape.

**Rejected alternative.** Repeated tile colors add visual variety but make an
axis value such as `3x2` potentially collapse to a smaller semantic period.

**Failure mode checked.** `self_check` rejects repeated residues; the exact-axis
probe verifies the observed smallest period equals the requested shape.

## D4 — Use a four-profile adversarial lesson schedule

**Choice.** Alternate two wide-tile row gaps with two tall-tile column gaps; all
four holes overlap the top-left period block. A lesson has three demonstrations
and one query.

**Reason.** The canonical examples admit three plausible shortcuts. A complete
four-pair window supplies a row-only counterexample, a column-only
counterexample, and a top-left-readout counterexample. Holding out any one pair
still leaves all three rivals refuted by the demonstrations.

**Rejected alternatives.** Pure random hole geometry can produce lessons where
a rival survives all demonstrations. A schedule containing only row gaps or only
column gaps teaches a one-dimensional repair. Merely checking each pair's label
does not establish lesson identifiability.

**Evidence.** The exhaustive local schedule probe checked 64 band/start/query
combinations. The source-bound census materialized 300 lessons and held out each
of 1,200 pairs once; production and rotations both reported
`no_ambiguity_found`.

## D5 — Keep the zero region non-modal with thin adversarial bands

**Choice.** Default profiles erase a thin row or column band ending one cell
before the far edge.

**Reason.** This makes the missing region visually secondary, keeps the instance
close to the canonical color statistics, and removes exactly the evidence needed
by the relevant one-dimensional shortcut.

**Rejected alternative.** Large central holes looked more canonical but often
left enough per-row and per-column residues for both one-dimensional shortcuts,
so demonstration labels alone did not teach the global rule.

**Known limit.** Default production does not cover the full canonical rectangle
shape distribution. Broader central rectangles remain a useful future extension
once they are scheduled with equally strong semantic witnesses.

## D6 — Make difficulty observable without changing the rule

**Choice.** Apply a fixed bijective rotation of colors 1–9 for easy, medium, and
hard, while keeping geometry and exact overrides identical.

**Reason.** `GenCtx` keyed draws did not include difficulty, so an intermediate
version produced byte-identical bands and failed the defect census. A palette
bijection avoids geometry drift and preserves distinct residues.

**Rejected alternative.** Difficulty-specific grid dimensions would conflict
with exact overrides and make semantic comparisons harder.

**Evidence.** The regression test verifies all three bands differ in pixels but
share observed geometry; defect lint is green.

## D7 — Replace the acceptance-only validator with a semantic validator

**Choice.** Validate dimensions, cell types/range, one solid interior zero
rectangle, an inferable allowed smallest period, nonzero residues, and residue
uniqueness.

**Reason.** The baseline accepted all 56 destructive mutations and every minimal
impostor sampled by the shared checks.

**Rejected alternative.** Checking only rectangular shape and legal colors gives
no evidence that generated examples belong to the task.

**Evidence.** Focused destructive-mutation tests pass; final self-check and
defect-lint stages are green.

## D8 — Retain an independent oracle and a real-Racket counterexample

**Choice.** Keep `workspace/reference_probe.py`, `workspace/contract_probe.py`,
and the `top_left_tile_*` counterexample family.

**Reason.** Tests should not establish correctness only by calling production
helpers. The retained Racket receipt binds the most important semantic claim to
the selected authority.

**Rejected alternative.** A hand-computed expected output was initially wrong at
the right endpoint. That failed attempt is preserved rather than silently
rewritten, and the corrected witness was regenerated from the real authority.

## D9 — Treat finite rival checks as evidence, not proof

**Choice.** Report exact declared-rival counts and the scope limit explicitly.

**Reason.** Three executable rivals cover the strongest shortcuts found, but no
finite list proves universal induction.

**Evidence.** The contract probe and lesson census name every tested rival,
sample count, query policy, and source hash. No broader uniqueness claim is made.
