# Working notes: e1e7c467196f

## 2026-10-02 pairing-distribution repair

The version-2.0 generator always paired sorted source and target palettes by a
nonzero cyclic rank shift. A 256-seed × 12-index census therefore reached only
1/2 K=2, 2/6 K=3, and 3/24 K=4 bijections; it never emitted the canonical K=2
rank-aligned demonstration or the canonical K=3 reverse-rank query profile.
Ordinary shape and palette diversity remained 100%, so the existing diversity
battery did not reveal this semantic collapse.

Version 2.1 keeps the four-slot, three-demonstration curriculum but assigns
explicit pairing modes: K=2 aligned anchor, forced-crossed controls, uniform
all-permutation controls, and K=3 reverse anchor. Every cyclic three-profile
window still contains a crossed example and both unmapped-control branches.
The uniform profile gives full K=4 permutation support in the fixed hard-band
census. `workspace/pairing_coverage.py` records exact permutation signatures
and canonical support for future reviews.

The Racket authority did not change. Imported associated notes retain original
evidence and timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `109c7760e455ba0e2d81d343b8891c06f339ed9411fe539dff985875905c8cda`.

# Decisions for e1e7c467196f

## D1 — Preserve the task grammar and Racket authority

**Choice.** Keep the two-row, top-left contiguous legend; disjoint source and target colors; dimensions `5..14`; `K=2..4`; 4..10 mapped body cells; 0..4 unmapped body cells; same-size output; and the selected Racket rule hash `b5790be780c4`.

**Rationale.** Canonical execution, self-check, override behavior, rule smoke, and authority synchronization were already sound. The defect was not the transformation; it was which legal legend bijections the generator sampled.

**Rejected alternatives.** I did not modify the Racket rule, broaden the body grammar, add new axes, or restructure the generator. Those changes would enlarge the review surface without addressing P1.

**Probe.** The before and final batteries plus `workspace/pairing_coverage.py` isolate the distribution change while holding the rule constant.

## D2 — Retain the four-slot schedule

**Choice.** Keep `sample_index mod 4` and the profiles `canonical_k2`, `both_controls_a`, `both_controls_b`, and `canonical_k3_value`.

**Rationale.** The existing schedule already guarantees that every three consecutive demonstrations include a crossed legend and both target-colored and neutral unmapped controls. Reusing it preserves lesson composition and makes the repair bounded.

**Rejected alternatives.** Expanding the schedule would change lesson cadence and was unnecessary. Drawing every profile uniformly at random would improve pooled diversity but weaken deterministic three-example identifiability.

**Failure mode retained.** Profile identity is fully determined by sample index, so it is predictable. That is acceptable here because profiles are curriculum anchors, not hidden labels.

## D3 — Assign explicit pairing semantics to each profile

**Choice.** Use:

- `canonical_k2` → rank-aligned permutation;
- `both_controls_a` → uniformly selected nonidentity permutation;
- `both_controls_b` → uniformly selected permutation, including identity;
- `canonical_k3_value` → reverse-rank permutation;
- any explicit override draw → uniformly selected permutation.

**Rationale.** The aligned and reverse profiles directly restore canonical regimes. The crossed profile keeps a deterministic sorted-pairing counterexample. The uniform profile gives support to all legal permutations, including all 24 `K=4` cases in the fixed medium/hard census.

**Rejected alternatives.** Keeping cyclic shifts would preserve the defect. Making every profile uniform could occasionally produce three-demo windows with no crossed mapping and would discard useful canonical anchors. Forcing every profile to a distinct fixed permutation would restore only a handful of signatures, not full support.

**Limitations.** Easy defaults do not permit `K=4`. Hard default `K=2` appears only in the aligned anchor; explicit hard `K=2` overrides still use uniform pairing.

## D4 — Treat the old generator behavior as an explicit rival

**Choice.** Add `infer_nonzero_cyclic_rank_pairing`, which infers a nonzero cyclic rank shift and applies it to the body. Bind both `rank_aligned_pairing_is_supported` and `noncyclic_pairing_is_supported` to that rival.

**Rationale.** The first after battery correctly rejected unbound witnesses. Encoding the actual old shortcut makes the semantic claim falsifiable and gives future reviewers a precise regression target.

**Rejected alternative.** I did not weaken or bypass the semantic gate. A witness with no named behavioral competitor would only assert coverage, not prove instructional value.

## D5 — Add exact support diagnostics rather than more generic diversity statistics

**Choice.** Add `workspace/pairing_coverage.py` and `workspace/run_task_tests.py`.

**Rationale.** The original generator produced highly varied shapes, palettes, and positions while collapsing the semantically decisive permutation axis. A finite signature census directly measures that axis. The portable runner ensures the task-local tests execute even though root pytest discovery is limited to `repo/tests`.

**Rejected alternative.** I did not rely on aggregate unique-input/output rates; the before battery demonstrates they can be green while P1 persists.

## D6 — Keep the first failed after iteration

**Choice.** Retain the 11/12 after battery under `checks/after-iteration1/`, then add the rival and rerun both the focused semantic stage and full battery.

**Rationale.** The failure documents that the gate detected a real integration omission and that the final green result was not obtained by deleting evidence or relaxing policy.

## D7 — Solve honestly after final generator bytes

**Choice.** Use one ordinary solve revision, record the visible-derived hypothesis, and declare earlier rule exposure.

**Rationale.** The first program passed all visible examples. Creating a fake failed revision would reduce the evidentiary value of the episode.

## Unresolved / remaining

No model-learning experiment was run, so improved downstream accuracy remains a hypothesis. The finite census establishes observed support over its declared seed/index range, not exact long-run probabilities. Spatial arrangement variety was not promoted to a scheduled semantic axis.
