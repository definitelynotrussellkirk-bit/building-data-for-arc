# Working notes: fdffdd0bbde7

## Current rule and authority

The unchanged canonical Racket rule (`RULE_HASH = 66637f26ea98`) reads a top
library of color-keyed stencils. Full-height color-9 columns divide panels; the
single 9 inside each panel is the anchor. Colored cells encode offsets from that
anchor. Every lower body cell stamps the offsets for its own color onto a blank
same-size output, with out-of-bounds cells clipped.

Generator version `4.0.0` is bound to that authority. It does not alter or wrap
the Racket program.

## Exact production controls

All advertised controls are literal integers, independently recoverable from the
returned grid, and exact across `None`, `easy`, `medium`, and `hard` bands:

| Axis | Domain | Pixel observation |
|---|---:|---|
| `grid_h` | 10–16 | number of rows |
| `grid_w` | 13–21 | number of columns |
| `lib_h` | 3–6 | index of the first blank row |
| `n_entries` | 2–4 | number of library panels |
| `stencil_size` | 1–5 | uniform colored-cell count per panel |
| `n_body` | 4–8 | nonzero body-cell count |

Defaults are weighted toward the canonical 12–13 by 17 shape, library height 5,
three entries, and moderate stencil/body counts. Difficulty changes only those
weights; it does not narrow the declared exact domains. There are no declared
incompatible axis combinations.

Each panel color is unique and appears in the body. Every body seed has at least
one in-bounds stamped cell. Stencils may span the full panel, while one sampled
stencil cell is reserved to guarantee constructiveness even for the shallowest
legal body. The validator accepts the complete lawful manifold and the canonical
pairs rather than merely accepting generator defaults.

## Teaching decision and reversal history

The selected canonical examples also fit a shortcut that ignores the visible 9
and assumes the anchor is at the panel center. The first repair moved anchors
only horizontally and declared only that full-center rival. Review then found a
second shortcut: assuming the panel-center **row** while using the visible anchor
column still fit every generated example. That design was rejected.

The current generator varies every anchor away from the panel center in both row
and column and declares three executable canonical-fitting rivals:

- `panel_center_anchor`: ignore both visible coordinates;
- `center_row_anchor`: use the visible column but assume a centered row;
- `center_col_anchor`: use the visible row but assume a centered column.

Each generated input preserves at least one uncontaminated disagreement cell for
each rival. A prior implementation protected only the aggregate disagreement
region by distance; seed `120254`, sample index `4833` showed another stamp could
contaminate it. The current constructive placement protects a concrete cell per
rival instead. The retained source-bound counterexample is
`counterexamples/current-shortcut.json`.

Lessons use three demonstrations plus one query. The production sampler has no
ordered curriculum restriction; arbitrary query rotations are intended to be
identifiable against all declared rivals.

## Final evidence for generator SHA-256

`b382282399f261a1a04883f8e4478c53b455b5dc7264376e230ed4f62a673cd9`

- Twelve-stage after battery: 12/12 green.
- Portable task tests: 57/57 passed.
- Independent random probe: 4,000/4,000 unique inputs deterministic,
  validator-clean, bi-axially off-center, isolated, and differing from all three
  rivals; 35/35 independent Python outputs matched Racket.
- Exact joint-axis enumeration: 75,600/75,600 combinations constructed across
  four bands, with 75,600 isolated witnesses and disagreements for each rival.
- Lesson census: 300/300 four-pair lessons and 1,200/1,200 query rotations had
  no ambiguity against the declared rival set.

See `workspace/reference_probe.py`, `workspace/build_counterexample.py`, and the
focused tests for replayable checks.

## Known limits

Finite rivals do not prove unique induction against every possible hypothesis.
All production anchors are deliberately bi-axially off center to refute the
known canonical shortcuts; the canonical centered-anchor morphology remains in
canonical data but is not sampled as a production default. Stencil size is
uniform within one generated puzzle because it is an exact puzzle-level axis.
The supported shape and body-count ranges are intentionally narrower than the
old fictional metadata; they are the ranges exhaustively shown constructive.
No multi-step state transformation is added—the task remains one contextual,
task-defined stencil operation.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-2daebcc8bdb78eb7:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `a53785271be29b9440a457bb958da77dc023f18c5a1cec464f499a2b998f0d8d`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Dead/inconsistent axes on sourcea53785271be2 addressed by accepted487b1 sourceb382282399f2:6exact constructive axes, difficulty-independent exact overrides and strict validation/observer. Reported57task tests,12/12 battery,4000draws/35Racketparity and75600exactjoint cases;300lessons/1200rotations. Bounded reviewer evidence, no independent rerun.

### Assessment or prior finding

## fdffdd0bbde7

**Reproduced generator-interface defect: advertised axes are dead or
inconsistently bounded.** Against generator SHA-256
`a53785271be29b9440a457bb958da77dc023f18c5a1cec464f499a2b998f0d8d`
and rule hash `66637f26ea98`, seed 123 / sample 0 / medium difficulty produces
a 12×11 validator-clean grid. Supplying any of `grid_h=24`, `grid_w=28`,
`stencil_size=1`, `palette_kind="warm"`, or `texture="warm"` produces the exact
same grid byte-for-byte. In addition, values advertised as globally valid—
`n_entries=4`, `lib_h=6`, and `n_body=12`—are rejected under medium difficulty
because explicit overrides are checked against the local difficulty prior.

The source-bound reproducer, output hashes, shapes, validator results, and exact
exceptions are in `checks/audit/fdffdd0bbde7/analysis.json`; the catalog snapshot
is `checks/audit/fdffdd0bbde7/show.json`. This is an override/API finding rather
than a Racket-rule counterexample. I left the audit target unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-2daebcc8bdb78eb7-v0001/audit_assets.json), manifest SHA-256 `cf6fb5bfdb472082750d79ed35517eba3daa88f4f9ea96489baa3fbbf352a3a8`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `b382282399f261a1a04883f8e4478c53b455b5dc7264376e230ed4f62a673cd9`.

# Design and repair decisions — fdffdd0bbde7

Final generator SHA-256:
`b382282399f261a1a04883f8e4478c53b455b5dc7264376e230ed4f62a673cd9`.
Canonical Racket authority remained unchanged at `RULE_HASH = 66637f26ea98`.

## D1 — Treat the retained audit as a lead, not as current evidence

The retained return `review-2daebcc8bdb78eb7:v0001` reported that generator
SHA `a5378527…` advertised dead axes and rejected values that its metadata called
globally valid. I used that finding to choose probes, then reran the full baseline
battery against this packet. The before battery independently reproduced the
problem: 7 green, 2 advisory, and 3 failed stages, including 11,410 override
mismatches and difficulty-local rejections. Prior claims were not counted as
measurements of the repaired source.

## D2 — Replace fictional metadata with six exact, observable controls

**Prior choice:** thirteen-ish metadata concepts mixed real choices, aliases,
singletons, and ignored controls. Several values were silently swallowed or
bounded by difficulty-local priors.

**New choice:** expose only `grid_h`, `grid_w`, `lib_h`, `n_entries`,
`stencil_size`, and `n_body`. Each is a literal integer, has one global domain,
is exactly honored in every difficulty band, and is recoverable from pixels by
`observe_overrides`.

**Alternatives rejected:** retaining diagnostic aliases would preserve a broad
API but keep ambiguity about whether an override changes output. Declaring large
incompatibility tables would make the contract harder to understand and still
leave avoidable construction failures. The final constructive design supports
all Cartesian combinations, so `INCOMPATIBLE_OVERRIDE_COMBINATIONS` is empty.

**Evidence:** 75,600/75,600 joint combinations across four bands passed in
`checks/reference-final.json`; the public override stage passed in the final
battery.

## D3 — Choose ranges by constructive support, not by inherited prose

The final ranges are 10–16 rows, 13–21 columns, 3–6 library rows, 2–4 panels,
1–5 cells per stencil, and 4–8 body seeds. These preserve canonical morphology
while guaranteeing enough panel area, a body below the separator, unique panel
colors, and at least one seed per color.

The old wider size claims were not retained merely for apparent diversity. The
selected ranges are the ranges demonstrated by exhaustive joint-axis evidence.
Defaults remain weighted toward canonical 12–13 × 17 grids, library height 5,
and three panels so canonical-like support remains frequent in every band.
Difficulty changes probabilities only; it does not change legality.

## D4 — Keep one puzzle-level stencil-size control uniform across panels

A single exact `stencil_size` is observable only if every panel uses that count.
Per-panel independent sizes would add diversity but make one scalar override
ill-defined. Stencils may otherwise occupy any non-anchor cell across the full
panel, preserving broad geometry rather than only tiny local motifs.

A first broad-stencil implementation failed at shallow-body endpoint
combinations when every sampled offset pointed too far downward. The repair
reserves one body-placeable stencil cell, then samples the remaining cells from
the full panel. This retains broad support while making all exact combinations
constructive.

## D5 — Exercise every library color and require every seed to contribute

Each panel color is unique; the body has 4–8 seeds, contains every library color,
and never introduces an unknown color. Each seed must have at least one in-bounds
stamped cell. This avoids dead library entries, irrelevant body content, and
examples where a seed appears to do nothing because all offsets clip away.

Body positions are selected constructively rather than sampled and rejected in
an unbounded loop. A fixed first witness seed plus deterministic RNG for the
remaining positions keeps generation repeatable.

## D6 — Vary visible anchors in both coordinates

The canonical examples fit the intended visible-anchor rule, but also fit a
shortcut that assumes every anchor is at the panel center.

**First repair (rejected):** move anchors only horizontally and test only the
full-center rival. This refuted `panel_center_anchor`, but every anchor row stayed
centered, so `center_row_anchor` still fit every example.

**Final choice:** every production anchor differs from the panel center in both
row and column. The first panel's anchor is preferentially below center so its
witness has usable disagreement support in the body. The generator declares
three executable canonical-fitting rivals: ignore both anchor coordinates,
ignore only the row, and ignore only the column.

This is a deliberate teaching distribution restriction: centered anchors remain
valid canonical morphology but are not production defaults because they cannot
refute these shortcuts.

## D7 — Protect an actual disagreement cell for every rival

An intermediate implementation relied on distance between the witness seed and
other seeds. Seed `120254`, sample `4833` showed that another stamp could still
touch part of the designated disagreement region. Distance was therefore not a
sufficient invariant.

The final generator computes the true and rival stamp sets at the witness seed,
chooses one concrete disagreement cell per rival, and rejects subsequent seed
positions whose true or rival stamps would touch those protected cells. This is
weaker than reserving the entire symmetric-difference region, but it is exactly
what is needed to retain a visible witness while keeping every axis combination
constructive. `counterexamples/current-shortcut.json` and the focused tests bind
this behavior.

## D8 — Use a structural parser and strict validator

The former validator was mostly count-based. The new parser identifies the first
blank separator, full-height 9 dividers, panel spans, one anchor and one color per
panel, anchor-relative offsets, and body seeds. `self_check` then validates shape,
range, uniqueness, body/library color agreement, and in-bounds contribution.
`strict_canonical_like` delegates to that structural check and accepts all three
canonical pairs.

Malformed unknown controls, nonliteral integers, invalid difficulties, ragged
grids, duplicate colors, malformed panels, and body colors without entries now
fail explicitly rather than being silently accepted.

## D9 — Preserve the Racket rule

No evidence justified changing authority. The selected Racket rule already
matched canonical data; the defect was entirely in sampling, metadata,
validation, and teaching support. Independent Python parsing/oracle logic matched
Racket on 35/35 source-bound cases, and the public rule-smoke and authority-sync
stages passed.

## D10 — Require arbitrary query-position identifiability

Lessons use three demonstrations and one query. There is no ordered-curriculum
exception, so every one of the four pairs may occupy the query position. The
three rival functions are declared in `SEMANTIC_RIVALS`,
`CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`.

A production census materialized 300 lessons (100 per named band), 1,200 unique
pairs, and all 1,200 query rotations. There were zero materialization errors,
zero scoring errors, and zero ambiguities against the declared rivals. This is
finite evidence only; it does not establish unique induction against every
possible program.

## D11 — Build reusable source-bound probes

`workspace/reference_probe.py` independently parses and solves grids, checks
determinism, iterates the selected module's declared rivals, compares sampled
outputs with Racket, and exhausts the exact axis product. It does not call the
generator's parser or output helper for its authority mirror.

`workspace/build_counterexample.py` verifies canonical rival fitness and emits a
small deterministic generated witness plus Racket receipt. Both tools bind exact
source hashes and use public reviewer helpers so future agents can replay them in
a repository or staged runtime.

## D12 — Curriculum annotation

This task has **task-defined symbols**: within each puzzle, a body color selects
the stencil defined by the same-colored library panel. It also has
**contextual gating** because the seed color determines which transform applies.
It does not require sequential state or interacting independent rules, so those
axes are marked not applicable rather than inflated.

## Remaining limitations

- The three rivals cover the known canonical anchor shortcuts, not all possible
  learned heuristics.
- Every generated anchor is bi-axially off center, so production does not measure
  generalization back to centered anchors.
- Stencil size is uniform inside a puzzle to keep the exact scalar axis honest.
- The post-repair solve had prior rule exposure and is correctly labeled exposed;
  it is not evidence of blind human discovery.

## Native parametric prototype — review-1fb87d7465bc9bd2

A separate task-local adapter now exposes one episode-fixed `composition`
parameter without changing the approved scalar generator or canonical authority:

- `single_stage` returns the exact canonical Racket program byte-for-byte.
- `border_routed_cascade` first materializes the seed color's own stencil. Its
  border-contact state then selects the next library panel on contact or the
  previous panel otherwise, and that selected stencil is applied from every
  first-stage cell. The second choice therefore depends on the input-dependent
  result of the first operation rather than merely following it in code order.

Inputs are deterministic and matched across settings, support 2–6 demonstrations
and 1–4 queries, preserve the first query when counts change, and include an exact
30×30 four-entry / 24-body-cell stress profile. Every demonstration contains both
routing branches and bi-axially off-center anchors. At the minimum two-demo count,
each setting rejects the other setting plus the declared center-anchor,
constant-route, swapped-route, and skip-first-stage rivals.

The bounded review covered 20 seeds, demo counts 2/3/6 and query counts 1/4:
240 episodes, 1,480 labeled pairs, 740 matched input instances whose outputs all
differed across settings, and 60 exact 30×30 stress instances, with no teaching,
determinism, or branch-coverage failures. Protected Racket independently replayed
24 labels and four counterfactual cases. The task suite passed 91/91 tests.
Native qualification passed for two settings × two fresh seeds with three demos
and four queries per job. A two-case protected-Racket witness shows that both
skipping stage A and replacing its border intermediate change the final output.

This remains reviewer-ready evidence, not acceptance. Exact-source owner
integration and fresh native acceptance are pending, and `training_admitted`
remains false. Finite rival checks do not prove universal identifiability or
measured training gain.
