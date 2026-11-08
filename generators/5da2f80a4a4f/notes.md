# Working notes: 5da2f80a4a4f

## 2026-10-20 UTC — strict request contract repair, review-5cfca8dcaae45d15

Current generator version remains `5.0.0`. Baseline SHA-256 was
`d0b5d9270362c9b8edbb0c3eedcf609b6c2b1aee0b7061defed4491fc8a83897`;
final SHA-256 is
`ff819cc96803491d7e32f1f2fd8cd6a2b9bcae826ee64328ad5e8d5c424e561b`.
The canonical Racket rule, canonical rows, `RULE_HASH`, and valid-integer sampling
distribution are unchanged.

The baseline accepted coercible public scalars: Boolean/float/string `seed` and
`sample_index`, negative `sample_index`, and string/float `grid_h`, `grid_w`, or
`palette_size` overrides. Defect lint reported 87 strict-scalar warnings. The
repair validates `seed`/`sample_index` before schedule or generation work,
requires nonnegative indices, and routes integer overrides through
`draw_int_strict`. A source-bound counterexample manifest lives at
`counterexamples/strict-scalar-contract.json`; focused tests replay it. Final
results are 39 task tests passed, 12/12 after-battery stages green, and defect
lint `FLAGGED 0`.

The production curriculum remains intentionally ordered with three demos. A
100-per-band census materialized 300 lessons / 1,200 unique inputs with zero
production hook warnings or declared-rival ambiguities. Arbitrary query rotation
is not supported: 39/1,200 rotations leave `frame_size_scale_lookup` alive.
Downstream data assembly must preserve production order unless a future change
strengthens every three-of-four subset. This is a documented limitation, not a
canonical repair.

A separate runnable prototype under `workspace/parametric/` chooses hidden
`key_transform` once per episode from `identity` (canonical/default) and
`transpose`. It uses a dense asymmetric 2x3 key and 12x12 frame interior so both
settings tile exactly. The retained verifier executed 10 Racket calls, checked
two complete three-demo episodes, canonical identity equivalence, public-label
hiding, and a same-input disagreement witness. It is proposed authoring evidence
only and does not alter or approve the production rule.

Open findings: the compact lesson census proves only the declared finite rival
set; rotation support is absent; the parameter prototype covers two fixed
episodes; no model-learning gain was measured. The post-repair visible-only
solve passed 3/3 examples on its first revision but is correctly marked as
previously exposed and does not claim hidden-query correctness.

## 2026-10-02 UTC — bounded distribution repair, review-6abdc8260b91668f

Version 4.0.0 had only four exact relative geometries. Frame dimensions determined key dimensions, offsets, palette defaults, and scale. A four-entry frame-to-scale lookup fit every canonical pair and the entire old sampler, despite existing semantic checks. RULE_HASH was stale (39bb6eb79ed8 versus current 5501c0734c5a); the canonical rule itself was not changed.

Version 5.0.0 retains all four anchors and adds 22 variable frame/key shapes, every legal key offset, independent 2..4-color palettes, a coverage-preserving shuffle, and bounded anti-quadrant repair. The eight-slot schedule supplies a variable counterexample in every three-demo window. Variable controls share the canonical 14x14 canvas. New shape families are disjoint from anchor shapes and observable from the grid.

Results: all 12 official after-battery stages green; 15 selected tests and 132 public tests passed; relocated canonical-Racket probe passed 4,901 executions, including 2,514 geometry/palette/offset cases and 612 three-demo windows. In 768 draws per version, relative geometry count rose 4 to 307 and lookup counterexamples rose 0 to 384. Actual public generation returned 16 episodes with zero recorded rejections. These are coverage/correctness checks, not measured learning gains or independent approval.

The first candidate's dynamic profile-name tuple triggered static AXES lint. Replaced it with an explicit literal and a metadata consistency test; did not weaken lint. Failure evidence is retained in the return.

Rerunnable tools: workspace/review_probe.py and workspace/audit_probe.py; instructions in workspace/README.md. Review packet docs contain exact before/after tables, an exact default-generated lookup counterexample, decisions/limits, and two unrelated findings-only audits. The canonical Racket and shared files remain unchanged. Approval remains a maintainer decision.

Imported associated notes retain original evidence/timestamps in evidence/associated_notes.jsonl.
## Current reviewer considerations

Source SHA-256: `ff819cc96803491d7e32f1f2fd8cd6a2b9bcae826ee64328ad5e8d5c424e561b`.

# Decisions for review-5cfca8dcaae45d15

## D1 — Repair the request boundary, not the sampler

**Choice.** Reject invalid integer-like values at the public boundary and use the repository's strict integer draw for declared integer overrides.

**Reason.** The reproduced defect was type/range admission, not label generation. The baseline accepted Boolean, floating-point, and string values for `seed`, `sample_index`, `grid_h`, `grid_w`, or `palette_size`, plus negative sample indices. Altering the geometry or schedule would not address that root cause.

**Alternatives rejected.** Coercing with `int(...)` preserves the defect and can silently truncate non-integral floats. Adding checks only in `generate` leaves `schedule_profile` inconsistent. Changing shared `gen_ctx` behavior would affect unrelated generators and was unnecessary.

**Probe and limit.** The focused red tests demonstrate 20 baseline failures; the final manifest replays 13 representative counterexamples. This establishes the selected generator's contract, not a repository-wide audit of every generator.

## D2 — Keep version 5.0.0 and deterministic valid outputs

**Choice.** Do not increment `VERSION` or repin `RULE_HASH`.

**Reason.** The patch changes only behavior for requests that violate the declared integer contract. For every valid integer request, keyed labels, ranges, schedule residues, and output grids are unchanged. The canonical Racket source and rule hash `5501c0734c5a` are already synchronized.

**Alternative rejected.** A version bump would unnecessarily invalidate reproducible valid seeds while implying a distribution change that did not occur.

**Limit.** Historical callers that intentionally relied on coercion will now receive a clear exception; that compatibility break is the repair.

## D3 — Preserve the authoritative rule and canonical data

**Choice.** Leave the Racket rule, canonical puzzle rows, Python mirror semantics, and rule metadata unchanged.

**Reason.** Canonical smoke and authority synchronization passed before and after the repair. The defect existed entirely in request validation.

**Alternative rejected.** Rewriting authority to absorb malformed requests would conflate API behavior with ARC semantics.

## D4 — Retain ordered three-demonstration lessons

**Choice.** Keep `EXAMPLES_NEEDED = 3` and the existing eight-residue production schedule.

**Evidence.** The final 300-lesson, 100-per-band census materialized 1,200 unique inputs and found 0 production-order hook warnings or declared-rival ambiguities. Every ordinary three-demo window contains the necessary variable control.

**Rejected alternative.** Redesigning the schedule so every possible three-of-four subset is identifying would be a larger curriculum/interface change unrelated to R1. It could reduce anchor support or require more demonstrations.

**Limitation.** Arbitrary query rotation is explicitly unsupported: 39/1,200 rotated queries leave `frame_size_scale_lookup` alive. Downstream assembly must preserve production order unless a future repair strengthens subset coverage.

## D5 — Prototype `key_transform`, do not integrate it

**Choice.** Build a runnable episode-level parameter with values `identity` and `transpose`, keeping `identity` canonical/default.

**Why this parameter.** It changes one interpretable operation while preserving object extraction, frame cropping, independent axis replication, colors, and overall family identity. It also admits an exact Racket implementation for each setting.

**Input choices.** Use an 18×18 canvas, a 14×14 color-2 frame, a dense asymmetric 2×3 key, and a 12×12 interior. The interior is divisible by both 2×3 and 3×2, so neither setting needs padding, clipping, or fractional scaling. The parameter is fixed once per episode, with three demonstrations and one query.

**Alternatives rejected.** A 90°/180° rotation family adds redundant symmetries and more settings than needed. Palette remapping risks changing semantic color roles. Variable replication factors are already inferred from frame/key dimensions and would not be a clean hidden rule parameter. Integrating transpose directly into production would change authority and requires separate review.

**Evidence and limit.** The verifier performs 10 Racket executions, checks canonical equivalence of identity, retains a same-input disagreement witness, and proves uniqueness only against the two bounded settings for two fixed episodes. It is a prototype, not an admission decision.

## D6 — Keep exact failures, compact large censuses

**Choice.** Retain the baseline detector log, both TDD red records, exact audit reproducer, and compact source-bound census companions. Large full census JSON files are replaceable by their generated companion summaries, which retain counts, source bindings, recipes, first witnesses, and limitations.

**Reason.** The return has strict member and expanded-size limits. Keeping duplicated runtime manifests and multi-megabyte full reports would make intake slower without adding a different conclusion.

**Restoration.** Re-run the exact `lesson-census` commands in `RESULTS.json` to regenerate the omitted full reports at their original paths.

## D7 — Treat audit findings as findings only

**Choice.** Do not modify `03909f3e98e7` or `80b1344c17c8`.

**Reason.** The audit contract asks for adversarial review, not repair. `03909f3e98e7` passed complete fixed-seed schedule enumeration after the initial strict audit lacked period evidence. `80b1344c17c8` reproducibly misses its declared prefix-tally hook in some production lessons, but it declares no concrete rivals, so logical ambiguity and a differing query prediction remain unproven.

## D8 — Report solve exposure honestly

**Choice.** Preserve the blind solve as no prior exposure, and mark the post-repair solve as earlier exposure `yes` with no reference consultation during solving.

**Reason.** The latter necessarily followed generator inspection. Visible-example success is retained without claiming hidden-query correctness or blindness.
