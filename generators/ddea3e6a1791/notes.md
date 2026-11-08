# Current notes: ddea3e6a1791

## Intended rule and authority

Crop the input to the smallest inclusive rectangle containing **every nonzero
cell**. Preserve colors, disconnected components, interior zeros, and gaps.
The selected canonical Racket program was not changed. Its pinned normalized
`RULE_HASH` is `debb1a8a129a`.

## Repaired generator

Version 2.0.0 replaces the imported 1.1.0 distribution, whose ordinary samples
contained only one connected monochrome motif. That old distribution made the
intended union crop observationally identical to shortcuts such as “crop the
sole/largest component” and “crop the only color.” The prior audit in
`evidence/review_index.json` was used as the lead; the current repair was
re-measured against the pinned packet rather than accepting the old claim.

The four-slot schedule is:

1. canonical-profile 4×6, one component and one foreground color;
2. two disconnected components using two foreground colors;
3. canonical-profile 5×5, one component and one foreground color;
4. a second two-component/two-color witness.

`EXAMPLES_NEEDED = 4`. Every four consecutive ordinary samples therefore
contain two joint witnesses; every possible four-of-five query rotation keeps
at least one. The declared exact integer axes are `grid_h` 4..10, `grid_w`
5..10, `bbox_h` 2..3, `bbox_w` 2..4, `n_components` 1..2, and
`n_distinct_colors` 1..2. Every advertised Cartesian combination is
constructible and observed exactly.

The semantic contract declares the intended mirror, strict-canonical support,
four lesson competitors (`identity`, `largest_component_only`,
`monochrome_crop`, and `solid_bbox_fill`), and two canonical shortcuts. The
retained Racket-backed separator is
`counterexamples/review-18e44a66ec02e372/sole-component-shortcut.json`.

Public controls are strict: `seed` must be an exact integer, `sample_index` an
exact nonnegative integer, and `difficulty` one of `None`, `easy`, `medium`, or
`hard`. This was added after the adversarial detector showed that booleans,
floats, strings, negative indices, and invalid difficulty labels were silently
accepted.

## Final evidence

Final selected generator SHA-256:
`a0cc1e30f8c619816c66cf333f936e1ee0728dbc2559bee1f3410de011cc6d29`.

- Final battery: all 12 stages green (`checks/after-final/`).
- Task-local portable suite: 41 passed (`checks/task-tests-final-v2/`).
- Profile floor: 30/60 exact canonical-profile hits, with 12 easy, 9 medium,
  and 9 hard; no crashes.
- Semantic census: 299/600 strict-canonical draws (49.83%, floor 45%), all
  12/12 sampled lessons identifiable, and 0/60 ambiguous smoke-test rotations.
- Required-rotation semantic gate: pass, 0/60 ambiguous rotations.
- Large census: 300/300 lessons, 1,500 pairs and 1,500 held-out rotations,
  0 ambiguities/errors, 1,263 unique inputs.
- Exposed post-repair solve: 4/4 visible examples, with earlier rule exposure
  recorded and no reference consultation during the solve.

## Proposed parametric extension

`workspace/parametric/` is a separate, unapproved prototype. It chooses
`background_color` once per episode from `{0, 9}` while preserving the core
“crop cells unequal to the background” rule. Value 0 is exactly the canonical
program; value 9 swaps the 0/9 color roles in inputs. Both settings were run
through Racket on four pairs each, and all six demonstrations distinguished the
other setting. This does not alter production generation or approval metadata.

## Limits and open findings

Evidence is finite and rival-relative; it does not prove uniqueness against all
possible programs. The production family intentionally remains small: zero is
fixed as canonical background, there are at most two components and two
foreground colors, and bbox sizes are 2..3 by 2..4. The random 300-lesson census
does not exhaust all seeds, although task tests exhaust cyclic starts 0..7 for
three bands and three seeds. No remaining blocking failure is known.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-af468f78a47f9f1d:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `b2c686b932c7648ea741575e36569cded389f3d7d7946c027befb0351ba5d252`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit focused closure against current a0cc1e30f8c619816c66cf333f936e1ee0728dbc2559bee1f3410de011cc6d29. Owner static inspection confirms4-slot defaults now include two disconnected/multicolor joint-bbox witnesses;largest_component_only andmonochrome_crop areexplicitrivals andall_components/allcolors witnesses. Source-bound sole-component-shortcut.json andregression assertactualretainedRacketcrop differsfromcomponentrival;reviewer current-source41tests/full76576-file replay,300four-demo lessons/1500rotations providefocusedclosureofoldsolemotif shortcut. Boundedfinite scope;notowner runtime run.

### Assessment or prior finding

## ddea3e6a1791

A plausible surviving shortcut is: **find the sole monochrome 4-connected motif and normalize that component to the top-left of its own box**. That is answer-equivalent to tight nonzero-bbox cropping on every canonical example and every ordinary generated example, because generation always creates exactly one connected one-color motif. The `multiple_motifs` case is only an explicit degenerate override and is never sampled normally.

Concrete disagreement input:

```text
0 2 0 0 0 0
0 2 0 0 3 0
0 0 0 0 3 0
0 0 0 0 0 0
```

The intended crop over **all** nonzero cells is:

```text
2 0 0 0
2 0 0 3
0 0 0 3
```

A “sole/first component” shortcut can return only the normalized color-2 domino:

```text
2
2
```

The ordinary distribution therefore does not teach that disconnected components and multiple colors jointly determine one global bounding box. At least one lawful multicomponent/multicolor profile is needed to refute that shortcut.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `a0cc1e30f8c619816c66cf333f936e1ee0728dbc2559bee1f3410de011cc6d29`.

# Decisions — ddea3e6a1791

## D1. Keep the canonical Racket rule unchanged

**Original choice:** crop to the tight bbox of all nonzero cells. The rationale
in the imported task was not recorded beyond the canonical examples.

**Decision:** preserve the rule and pin `RULE_HASH = debb1a8a129a`. All four
canonical pairs are reproduced by the Python mirror, and authority/rule-smoke
checks pass. The defect was in what inputs were taught, not in labels.

**Rejected alternative:** modify the Racket rule to crop one object or one
color. That would fit the weak old distribution but contradict disconnected
canonical behavior and the authority record.

## D2. Replace random single-motif generation with a four-slot schedule

**Original choice:** version 1.1.0 sampled one connected monochrome motif with
padding. Its rationale is unknown. It made “all nonzero cells,” “the only
component,” and “the only color” observationally equivalent.

**Decision:** use a deterministic period-four schedule with two canonical-like
slots and two decisive joint witnesses. `EXAMPLES_NEEDED = 4`; every four
consecutive samples contain all profile roles. Tests cover starts 0..7, three
seeds, three bands, and all five possible held-out query positions.

**Rejected alternatives:**

- Pure random witness frequency: a nominal 50% rate does not guarantee that a
  complete episode contains a witness.
- One witness per four: holding that pair out as query can leave four ambiguous
  demonstrations.
- All-witness lessons: strong semantics but unnecessary distribution drift from
  tiny canonical inputs.

**Failure mode retained:** a downstream assembler using fewer than four demos
can omit a witness. The generator declares the required count so such assembly
is visible rather than silently accepted.

## D3. Make each witness jointly multicomponent and multicolor

**Decision:** witness slots contain exactly two 4-connected components and two
nonzero colors, with the components at opposite bbox corners. A single example
then refutes both `largest_component_only` and `monochrome_crop`; interior zeros
also refute `solid_bbox_fill`.

**Rejected alternatives:** separate component-only and color-only witnesses.
Those require more demonstrations and can fail under query rotation.

**Probe:** the source-bound Racket counterexample is
`repo/generators/ddea3e6a1791/counterexamples/review-18e44a66ec02e372/sole-component-shortcut.json`.
The intended output differs from the largest-component rival.

## D4. Retain strong canonical-profile support

**Decision:** two scheduled profiles use 4×6/2×2 and 5×5/2×3 one-color motifs,
matching observed canonical height/width/palette profiles. Witness dimensions
increase by difficulty but stay within declared bounds.

**Measured result:** profile-floor draws produced 30 exact hits in 60 attempts:
12/20 easy, 9/20 medium, and 9/20 hard, with zero crashes. The semantic census
measured 299/600 strict-canonical-like draws (49.83%). `MIN_STRICT_FRAC` is 0.45,
not 0.50, because the checker samples arbitrary indices and measured 299 rather
than exactly 300 strict slots.

**Rejected alternative:** lower the floor to the generic minimum. That would
pass but no longer document the deliberate near-half canonical support.

## D5. Advertise only exact, constructive axes

**Decision:** expose integer controls for grid height/width, bbox height/width,
component count, and foreground-color count. Every Cartesian combination of the
published ranges is generated and checked by `observe_overrides`; no
incompatibility table is needed.

**Rejected alternative:** preserve the old `position_bias` and `density` axes.
They were singleton/dead controls and described incidental layout rather than
observable semantic coverage.

**Known limit:** the family does not explore three-plus components, three-plus
foreground colors, bbox heights above 3, or bbox widths above 4. These are
intentional bounded-domain limits, not claims about the full ARC input space.

## D6. Add an executable semantic contract and named rivals

**Decision:** declare `strict_canonical_like`, `SEMANTIC_WITNESSES`,
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `lesson_identifiable`.
Production lessons and arbitrary held-out rotations must refute the named
rivals.

**Measured result:** the required-rotation gate checked 60 rotations with zero
ambiguity. The larger production-sampler census materialized 300 lessons/1,500
pairs and checked 1,500 rotations with zero ambiguity, zero hook errors, and
1,263 unique inputs.

**Limit:** these are finite checks against declared and bounded searched rivals,
not a proof of unique induction against every possible program.

## D7. Reject coercible public controls

**Intermediate failure:** the first repaired generator accepted invalid `seed`,
`sample_index`, and `difficulty` values. Defect lint emitted 48 strict-scalar
warnings because Python treats booleans as integers, `Random` accepts coercible
seeds, and the difficulty lookup silently fell back.

**Decision:** validate exact integer types, require nonnegative sample indices,
and accept only `None/easy/medium/hard`. Sixteen focused parameterized cases
were written red first; the repaired suite passes and final defect lint is clean.

**Rejected alternative:** rely on downstream `gen_ctx` coercion. That creates
silent aliases between logically distinct episode controls.

## D8. Prototype one episode-level rule parameter, separately

**Parameter:** `background_color ∈ {0, 9}`, chosen once per episode. Default 0
is exactly the canonical Racket program. Alternative 9 changes the executed
foreground predicate to `cell != 9` and swaps 0/9 roles in generated inputs.

**Why suitable:** it changes the transformation while preserving the core bbox
reasoning. Applying the wrong setting treats the canvas as foreground, so every
demonstration is distinguishing.

**Evidence:** `checks/parametric/report.json` records two exact programs, eight
Racket-checked pairs, and 6/6 distinguishing demos. Public artifacts hide the
parameter, rule, and query labels.

**Limits:** only two settings and one retained seed were checked. The prototype
is not wired into production, catalog approval, or the canonical hash.

## D9. Curriculum-composition annotations

This is one extraction operation with no sequential state, branch-dependent
subrules, task-defined symbol dictionary, or multi-rule interaction. Therefore
`multi_rule_interaction`, `sequential_state`, `contextual_gating`, and
`task_defined_symbols` are **not applicable**, rather than absent defects.

## D10. Stop condition

Stop after the canonical generator passed all 12 battery stages, 41 portable
task tests, required query rotations, the 300-lesson census, Racket-backed
counterexample replay, parametric verification, and the exposed visible solve.
No remaining blocker was observed; broader hypothesis coverage remains an
explicit limitation.
