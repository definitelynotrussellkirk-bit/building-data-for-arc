# d57b7deebba2 generator notes

## Selected semantics

The canonical Racket authority groups nonzero cells by `(color, r+c)` and fills
between the minimum and maximum row within each group.  The generator therefore
permits one color to mark more than one span when the spans use distinct
anti-diagonals.  It deliberately rejects more than two endpoints in one such
group because that is outside this sampler's teaching grammar, even though the
authority itself can process it.

## Curriculum decision

All public canonical demonstrations happen to use each color exactly twice.
That leaves a strong shortcut: treat each color as one global pair and ignore a
color that occurs four times.  `sample_index % 3 == 0` reuses one color on two
separate anti-diagonals.  Every consecutive three-example lesson therefore
contains a direct counterexample while the other two slots retain the public
one-pair-per-color style.

## Exact controls

Only `grid_h`, `grid_w`, and `n_pairs` are public axes.  Their complete Cartesian
product is constructive in every difficulty band and recoverable from pixels by
`observe_overrides`.  Difficulty affects only non-public span-length weighting.
Negative fixtures and palette aliases from v2 were removed rather than exposed
as ordinary valid textures.

## Authority

`RULE_HASH = ed1603229043`.  No Racket source was changed in this review.
## Current reviewer considerations

Source SHA-256: `c20aebc584ad035299206e01dc82780bd26091dd47526ca75fcbf888e13144e6`.

# Decisions for `d57b7deebba2`

The canonical Racket program is the label authority. Decisions below concern the
input distribution, validation contract, and review tooling only.

## D1 — Keep the Racket authority unchanged

**Original rationale.** The v2 source described filling anti-diagonal endpoint
pairs but did not pin or analyze the exact authority. Its rule-smoke behavior was
already healthy.

**Decision.** Pin `RULE_HASH = "ed1603229043"` and repair the generator around
the actual rule: group nonzero cells by `(color, r+c)` and fill from minimum to
maximum row within each group.

**Alternatives rejected.** Rewriting Racket to enforce one global pair per color
would merely codify the generator's accidental restriction and would change
canonical semantics without evidence.

**Probe.** `checks/d57b7deebba2-racket-oracle/comparison.json` shows 64/64
independent-oracle matches; authority sync and rule smoke pass.

**Failure mode / limit.** The authority can process inputs broader than the
selected teaching grammar, including more than two cells in a group. This review
does not claim to sample its full total domain.

## D2 — Select a strict, canonical-supported geometry manifold

**Original rationale.** v2 declared `grid_h=5..16`, `grid_w=5..18`, and
`n_pairs=1..8`, but its difficulty branches actually sampled narrower ranges and
its validator rejected one canonical 7-row grid. No retained evidence justified
the broad declarations.

**Decision.** Use `grid_h=7..10`, `grid_w=10..12`, and `n_pairs=2..3`. These
cover all canonical shapes/pair counts relevant to the selected grammar and are
constructive as a full Cartesian product in every band.

**Alternatives rejected.** Keeping width 9 solely because v2 sampled it would
miss the canonical profile floor used by the packet. Expanding to four or more
spans would add a curriculum choice not required to fix the identified shortcut.

**Probe.** Boundary overrides are tested in all bands by
`test_exact_boundary_overrides_work_in_every_band`; the generic override gate
accepted 3,420/3,420 draws.

**Failure mode / limit.** This is deliberately narrower than all mathematically
possible anti-diagonal layouts.

## D3 — Expose only exact controls that can be recovered from pixels

**Original rationale.** v2 listed palette aliases, a texture alias, two
single-valued pseudo-axes, multiple overlapping count axes, and invalid negative
fixtures as ordinary valid values. The comments named these as “combinatorial
axes,” but did not establish observability or independent effects.

**Decision.** Retain only `grid_h`, `grid_w`, and `n_pairs`. Implement
`observe_overrides` as exact pixel recovery, reject unknown keys and non-integer
values, and declare no incompatible combinations.

**Alternatives rejected.** Marking dead aliases “diagnostic” would silence a
warning without making them useful. Exposing `palette_size` or
`n_distinct_colors` would be misleading because repeated-color teaching makes
those quantities dependent on the curriculum branch.

**Probe.** R3 in `REVIEW.md`; before and after override logs under
`checks/before-manual/` and `checks/after-override/`.

**Failure mode / limit.** Span length remains an internal difficulty-weighted
choice, not an exact external control.

## D4 — Schedule repeated-color witnesses every third sample

**Original rationale.** v2 always sampled distinct colors. Every canonical
example also has each color exactly twice, so the restriction looked plausible
but left the intended `(color, anti-diagonal)` grouping unidentifiable.

**Decision.** `sample_index % 3 == 0` reuses one color across two distinct
anti-diagonals. The other two slots preserve the public distinct-color style.
With `EXAMPLES_NEEDED = 3`, every cyclic consecutive demonstration window has a
direct counterexample to the strongest rival.

**Alternatives rejected.** Purely random reuse gives only average witness
frequency and can leave complete lessons ambiguous. Reusing a color within one
anti-diagonal would violate the selected two-endpoint group grammar rather than
teach independent groups.

**Probe.** `test_every_consecutive_three_demo_window_refutes_canonical_shortcut`
and the 300-lesson census in `checks/d57b7deebba2_lesson_probe.json`.

**Failure mode / limit.** The schedule addresses the declared strongest rival;
it does not prove exclusion of every unenumerated hypothesis.

## D5 — Weight defaults toward canonical profiles without narrowing overrides

**Original rationale.** The packet requires canonical profile support, while a
uniform draw over all control combinations would underrepresent exact canonical
shape/palette marginals.

**Decision.** Cycle six anchor triples and pass an anchor-weighted option list to
`GenCtx`. Every legal value remains present, and an explicit override still
selects exactly the requested value.

**Alternatives rejected.** Hard-coding a single canonical shape would pass a
floor but destroy diversity. Rejection sampling would make exact overrides and
runtime behavior harder to reason about.

**Probe.** Profile floor is 57/60 exact and 60/60 envelope; diversity remains
100% unique over 300 probed pairs.

**Failure mode / limit.** The resulting distribution is intentionally not
uniform over dimensions or pair counts.

## D6 — Choose spans by distinct anti-diagonal keys

**Original rationale.** v2 attempted placements up to 400 times and reserved
all span cells. This worked often but made constructive guarantees indirect.

**Decision.** Precompute all length-2–5 spans grouped by anti-diagonal, sample
distinct diagonal keys, then sample one span per key. Distinct anti-diagonals are
disjoint, so the construction needs no capped retry loop.

**Alternatives rejected.** Retaining rejection placement would preserve a
silent possibility of underfilling. Allowing overlap adds occlusion semantics
not present in the canonical task.

**Probe.** Determinism, validity, and mutation tests in
`test_generator_review.py`; 600/600 strict semantic-gate samples passed.

**Failure mode / limit.** Overlapping or touching same-diagonal segments are
outside the selected grammar.

## D7 — Keep endpoint groups exactly two cells, with lengths 2–5

**Original rationale.** This matches all public examples and the imported task
description. The authority itself can totalize some larger groups.

**Decision.** `self_check` requires exactly two endpoints per `(color,r+c)`
group, empty interiors, and length 2–5.

**Alternatives rejected.** Generating three or more marked cells on one
anti-diagonal would raise a different inference problem—whether interior markers
matter—and is unnecessary for the repeated-color fix.

**Probe.** Canonical 5/5 acceptance plus structural mutation tests.

**Failure mode / limit.** This validator defines generator support, not the full
mathematical domain of the Racket function.

## D8 — Declare executable semantics rather than prose-only intent

**Original rationale.** v2 had no semantic hooks, so the generic gate could
measure morphology but not whether lessons separated plausible rules.

**Decision.** Add `strict_canonical_like`, `SEMANTIC_WITNESSES`,
`SEMANTIC_RIVALS`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`,
`LESSON_COMPETITORS`, `schedule_profile`, and `lesson_identifiable`.

**Alternatives rejected.** A witness-name constant without executable predicates
would not verify that generated pixels actually realize the claim.

**Probe.** Semantic gate: strict 600/600, witness 219/600, rival claims 60/60,
12/12 lessons identifiable.

**Failure mode / limit.** `lesson_identifiable` is exact for declared rivals,
not an open-ended cognitive model.

## D9 — Retain an independent oracle and source-bound lesson census

**Original rationale.** Production helper reuse can make a test agree with the
implementation for the wrong reason, and the generic gate's 12 lessons are only
a smoke sample.

**Decision.** Build `workspace/reference_probe.py` without importing production
output helpers. It computes the intended and rival outputs independently,
checks canonical fit, records a fixed counterexample, and samples 100
nonoverlapping lessons per band using an explicit seed/start policy.

**Alternatives rejected.** Copying a fixed list of rival names into the probe
would drift from the generator contract; the tests instead assert the declared
contract and the retained tool exposes the concrete rival implementation.

**Probe.** 300/300 lessons identifiable, 1,199/1,200 unique inputs; independent
oracle 64/64 against Racket.

**Failure mode / limit.** One duplicate hard-band input occurred among 400
draws. This does not create overlapping lesson windows or an identifiability
failure.

## D10 — Treat the aggregate battery timeout as tooling evidence, not a pass

**Original rationale.** The packet explicitly requires the monolithic command,
but that process stopped producing progress after starting `defect_lint` even
though the same stage passed quickly in isolation.

**Decision.** Preserve the timed-out aggregate log and status, then execute all
12 supported stage invocations separately with source-bound receipts. Mark the
work complete because the generator and required checks are complete, while
retaining the aggregate wrapper limitation in `remaining_failures`.

**Alternatives rejected.** Calling the partial aggregate output green would be
false. Repeating it indefinitely would add no semantic evidence.

**Probe.** `checks/after-command-status.json` and
`checks/after-per-stage-summary.json`.

## D11 — Add a native fill-then-relay parametric family

**Original rationale.** The canonical task had no native episode parameter or
sequential dependency suitable for admission. A cosmetic reflection or palette
change would not create a materially different rule.

**Decision.** Keep the canonical `fill_only` program byte-for-byte and add
`activated_projection`. Both settings first use the same anti-diagonal fill.
The alternate setting then selects the unique color-8 relay adjacent to a cell
that changed from zero to a span color, recolors the relay with that span color,
and casts the color away from the newly filled cell through post-fill zeros.

**Alternatives rejected.** Selecting any endpoint-adjacent relay ignores the
newly filled intermediate; projecting toward the span reverses the dependency;
using the relay's marker color, leaving the relay gray, or projecting on a fixed
diagonal are simpler shortcuts rather than the selected rule.

**Probe.** `workspace/parametric/audit.py` executes both selected Racket rules
and six executable rivals, checks public/private separation, exports hash-named
public challenges, materializes a wrong-intermediate counterfactual, and sweeps
both settings over every demonstration count. Native qualification and the
source-bound witness are retained under `checks/d57b7deebba2/` in the return.

**Failure mode / limit.** The bounded teaching audit excludes the alternate
setting and six authored rivals; it does not prove uniqueness over all possible
programs. Owner exact-source acceptance and training admission remain pending.

## D12 — Keep source authority and visible inputs matched across settings

**Decision.** `relay_policy=fill_only` reads the exact canonical Racket bytes.
For a fixed seed, demonstration count, and query count, both settings use the
same inputs and differ only in labels. Requests support 2–6 demonstrations and
1–4 prefix-stable sequential queries, with a 30×30 fourth query.

**Probe.** The adapter tests compare source hashes, matched inputs, count
boundaries, query-prefix stability, protected-Racket labels, finite-rival
teaching, stress-query geometry, and public-turn masking.

**Failure mode / limit.** The sampler is constructive for the declared count
range and retained seed sweep; it does not claim to cover every anti-diagonal
layout accepted by the canonical authority.
