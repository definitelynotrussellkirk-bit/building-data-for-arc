# Working notes: 97d3714964b0

## Intended rule and calibrated domain

The selected rule processes each 4-connected color-7 component independently.
A component whose bounding-box interior contains a background cell is hollow and
is recolored 4; a completely occupied bounding box is solid and is recolored 2.
The reviewed generator intentionally samples a clean rectangular subdomain:
one or two hollow frames plus one or two solid rectangles on a zero background.
Only colors 0 and 7 occur in generated inputs.

## Decision reversal

The imported v2.1.0 design exposed many declared but inert controls, always added
an unrelated decoration color, could not support the canonical palette/profile,
and required exactly one hollow plus one solid object. Its `self_check` therefore
rejected the canonical test input containing two hollow frames. Object sizes and
positions also made simple size thresholds fit the canonical pairs and generated
lessons.

Version 3.0.0 replaces that design with four exact observable controls:
`grid_h` 7..14, `grid_w` 9..14, `n_hollow` 1..2, and `n_solid` 1..2. Unknown,
out-of-range, boolean, floating-point, and string overrides fail closed. A
constructive four-slot layout guarantees separation and always pairs one hollow
and one solid object with identical bbox dimensions. That witness refutes the
canonical-fitting `bbox_area_gt4`, `component_size_ge8`, and `bbox_height_ge3`
rivals on every generated grid.

## Canonical support and authority

`RULE_HASH = "3c6d01646411"`. All three canonical train/test inputs pass
`self_check`, including the two-hollow test scene. Dimensions are weighted toward
canonical profiles but every declared value remains available in every band.
The task-specific base `target_code` had only comment/beautification drift from
the canonical program; it was synchronized byte-for-byte. The canonical Racket
program and its behavior were not changed.

## Verification summary

Final generator SHA-256:
`7103c5f54a2596c16c7e68f5c1d113fad4aff0dd32259e5cf68cf8db0e2a9363`.
The completed after battery is 12/12 green with no advisories. Portable focused
tests pass 35/35, including 19 independent Python/Racket comparisons. The
source-bound lesson census materialized 300 lessons (100 per band), 1,200 pairs,
and all 1,200 query rotations with zero ambiguity, hook warning, or scoring
error against the three declared rivals.

## Known limits

The calibrated domain contains only rectangles, at most four objects, and the
fixed semantic colors 0/7→4/2. The same-bbox witness and finite rival census do
not prove uniqueness against every possible rule. The lesson census samples the
production sampler and every query rotation of those materialized lessons; it
does not enumerate every possible seed/schedule. These are explicit limits, not
claims of universal identifiability.
## Current reviewer considerations

Source SHA-256: `7103c5f54a2596c16c7e68f5c1d113fad4aff0dd32259e5cf68cf8db0e2a9363`.

# Decisions for 97d3714964b0

## D1 — Replace the inherited axis surface rather than patch inert controls

**Prior choice:** v2.1.0 advertised palette, anchor, asymmetry, texture, position,
and color-count controls, several with singleton domains or no observable effect.
Unknown keys were accepted. **Decision:** expose only `grid_h`, `grid_w`,
`n_hollow`, and `n_solid`, each exact and pixel-observable. **Why:** the before
override evidence showed widespread silent mismatch, while the final matrix and
focused tests show the reduced contract is enforceable. **Rejected alternative:**
retain aliases or diagnostic-only axes; that would preserve misleading API surface
without adding training value.

## D2 — Use constructive separated slots

**Decision:** split the canvas with one full blank row and column and place at
most one object in each of four slots. **Why:** generation cannot silently lose
objects through retry exhaustion, and 4-connected components remain independent.
**Failure mode considered:** free-form rejection sampling can return fewer objects
than requested or accidentally merge them. **Limit:** the resulting spatial
regularity is narrower than arbitrary layouts, so position is randomized within
slots and not treated as semantic.

## D3 — Make topology, not size, the decisive contrast

**Decision:** every generated input includes at least one hollow and one solid
object with identical bbox dimensions. **Why:** all three simple size rivals fit
the canonical pairs; without a same-size contrast a model can learn area/height
instead of interior occupancy. **Rejected alternative:** merely broaden the size
ranges. Overlapping ranges make shortcuts less reliable but do not guarantee a
counterexample in every lesson.

## D4 — Match canonical palette and profiles without hard-locking them

**Decision:** remove the unrelated decoration cell and use only `{0, 7}`; weight
height/width toward canonical 7x9, 8x9, and 11x10 profiles while retaining the
full declared ranges in every difficulty band. **Why:** the inherited generator
had zero exact canonical-profile support. **Rejected alternative:** emit only the
three canonical sizes, which would satisfy the floor but unnecessarily narrow
diversity.

## D5 — Accept canonical scenes while requiring stronger generated witnesses

**Decision:** `self_check` accepts lawful canonical inputs with one or two objects
of each class; the same-bbox requirement is asserted for generated scenes through
focused tests and semantic witnesses rather than imposed on canonical examples.
**Why:** canonical validity and curriculum contrast are different obligations.
**Failure mode considered:** rejecting official examples because they lack a
teaching witness would make the validator stricter than the task.

## D6 — Declare executable rivals and require three demonstrations

**Decision:** declare `bbox_area_gt4`, `component_size_ge8`, and
`bbox_height_ge3` as canonical-fitting rivals and set `EXAMPLES_NEEDED = 3`.
`lesson_identifiable` rejects a materialized lesson whenever a rival fits every
demonstration but changes the query. **Evidence:** 300 production lessons and
1,200 query rotations had zero ambiguity. **Limit:** this is finite declared-rival
evidence, not proof against undeclared hypotheses.

## D7 — Synchronize the selected authority without changing semantics

**Prior choice:** task-specific `target_code` contained comments absent from the
canonical program, so `defect_lint` warned and `authority_sync` failed despite
execution parity. **Decision:** replace only that stale textual copy with the
already-identical canonical/raw program. **Why:** exact authority binding is a
required after gate. The canonical Racket rule was not altered.

## D8 — Stop after the first successful visible-only solve

The final source was frozen before `solve prepare`. A flood-fill plus bbox-interior
hypothesis passed all three visible demonstrations on revision 1. Earlier rule
exposure is recorded as `yes`; no source, reference solution, or private labels
were consulted during the episode. Further revisions would have manufactured
failures rather than added evidence.

## D9 — Add a native largest-hollow threshold relay family

The native family keeps `solid_policy="independent"` as the byte-exact
canonical default and adds `solid_policy="largest_hollow_threshold"`.  Every
scene contains two hollow frames and two solid rectangles.  Step A classifies
components and computes the largest hollow bounding-box area.  Step B recolors
hollows to 4 and recolors only solids whose area reaches that cross-object
threshold to 2; smaller solids remain 7.  One solid matches the largest hollow's
dimensions and a second lies below the threshold, so the relay is visible in
every lesson rather than only in metadata.

Fresh focused plus retained tests passed 65/65, and both Racket programs passed
strict complete-program validation.  Native qualification covered both settings,
seeds 0 and 17, three demonstrations, four queries, and 40 protected-Racket
evaluations.  The public projection exported 16 sequential views; first-turn
checks passed 24 private-field invariance mutations and four positive controls.
The reviewer-replayed causal witness records a largest-hollow threshold of 42,
hollow areas `[15,42]`, solid areas `[8,42]`, and the canonical independent
policy as a wrong-intermediate counterfactual.

This is finite source-bound evidence, not a universal depth proof, owner
acceptance, measured training gain, or training admission.  The family is
intentionally limited to separated rectangular objects, exactly two hollow
frames and two solids, and a bounding-box-area relay; broader topology and
object-count variation remain future curriculum work.

