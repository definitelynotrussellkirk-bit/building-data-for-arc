# Working notes: 033db13a9d37

## Review lead

The pinned baseline was generator SHA-256 `16c52186783cfcc7f902dc7f52f8f9fb1343d32594d177388e5e50837def934d`. I used prior return `review-befb6364b93d8004:v0001` only as a lead: it reported a seed-17 three-demo lesson where the canonical-fitting `last_nonzero_seed` rival survived all demonstrations and changed the query, plus silently clamped/ignored overrides. All current-source claims were remeasured.

## Defects reproduced on the pinned source

- No `RULE_HASH` pin and textual divergence between the selected base Racket target and canonical authority.
- Fake/partial controls: out-of-range seed locations were clamped and unknown keys were accepted.
- Weak `self_check`, a degenerate bottom-row texture overlapping the ordinary texture domain, and minimal impostors accepted.
- No executable semantic contract. The profile-floor probe found exact canonical support in only 2/60 draws and zero support in easy and hard.
- A random 25% decoy rate did not guarantee that a three-demo lesson distinguished first from last nonzero seed.

The retained before evidence is under `checks/before*`; the full before battery was interrupted, so only the independently completed stage reports are used as measurements.

## Selected repair: version 2.0.0

- Reduced the public surface to four exact, observable axes: `grid_h`, `grid_w`, `fg_color`, and `scene_profile`.
- Reject unknown keys, wrong types, unsupported colors, invalid dimensions, and invalid difficulty rather than clamping.
- Alternate `decoy_witness` and `canonical_anchor` by sample index. Odd anchors cycle 3×3, 5×5, 9×9, and 12×12; even samples carry one later, differently colored decoy.
- Strengthened `self_check` to the exact generated manifold while retaining all four canonical inputs.
- Declared the canonical-fitting `last_nonzero_seed` competitor, its `later_decoy` witness, and an executable `lesson_identifiable` hook.
- Added an independent oracle/rival/schedule probe in `workspace/reference_probe.py` and 49 portable task tests.
- Exact-synchronized the selected base solution `racket_target.target_code` to canonical `program_solution`; the behavior-equivalent previous executable remains in `raw_code` for provenance. Canonical `puzzles.jsonl` was not changed.

## Measured final source

Generator SHA-256: `9a6756b67c901b2e0b973c4c2dd30524d20f364f6af1a556b6cfb33f4fbcdda4`.

- Full after battery: 12/12 green.
- Task tests: 49/49 pass.
- Override matrix: 57,330/57,330 accepted exact draws, 637 cases, zero findings.
- Semantic gate: 600/600 strict, 4/4 canonical, 295/600 later-decoy witnesses, 60/60 rival claims verified, 12/12 sampled lessons identifiable.
- Production lesson census: 300/300 lessons, 1,200 labelled pairs, 1,014 unique inputs, zero declared-rival ambiguities in production or 1,200 query rotations.
- Exhaustive deterministic schedule probe: 64 starts per band, 192 four-pair windows and 768 query rotations, zero surviving last-nonzero cases.

## Limitations and self-review

The default sequence intentionally correlates single-seed anchors with four square canonical sizes and decoy witnesses with the broader difficulty-weighted size distribution. Exact controls nevertheless realize every advertised joint axis combination, and the production sampler plus all query rotations were checked; a downstream assembler that discards sample order would lose the schedule guarantee. Only the declared last-nonzero rival is exhaustively refuted—finite rival checks are not a proof of unique induction against every conceivable program.
## Current reviewer considerations

Source SHA-256: `9a6756b67c901b2e0b973c4c2dd30524d20f364f6af1a556b6cfb33f4fbcdda4`.

# Decisions: 033db13a9d37

## D1 — Treat the prior audit as a lead, not current evidence

**Choice.** Reproduce baseline behavior and run current-source checks before editing.

**Rationale.** The retained review index named a concrete first-vs-last ambiguity and override defects, but the assignment explicitly warned that prior claims were not measurements of the pinned source. The prior source hash did match the packet pin, so it supplied useful hypotheses without replacing the required checks.

**Alternative rejected.** Applying the historical suggested patch or quoting its 27/291 rate directly. That would bypass source-bound verification and could import stale assumptions.

## D2 — Make lesson identifiability deterministic

**Choice.** Alternate `decoy_witness` and `canonical_anchor` by `sample_index % 2`.

Every four consecutive samples therefore contain two decoys. With three demonstrations and one query, every possible query rotation leaves at least one decoy in the demonstrations, so the `last_nonzero_seed` rival is refuted.

**Alternatives considered.**

- Keep a random decoy probability and sample more often. Rejected because any finite random rate still admits an all-single demonstration set.
- Make every sample a decoy. Rejected because it removes simple canonical-like anchors and overconcentrates the distribution.
- Reject ambiguous assembled lessons downstream. Viable, but more expensive and fragile because curriculum safety would depend on a separate assembler/retry loop rather than the generator schedule.

**Probe.** `workspace/reference_probe.py` exhausts 64 starts per band and all four query rotations. The final report covers 192 windows and 768 rotations with zero surviving last-nonzero cases.

**Limitation.** The guarantee assumes production assembly preserves consecutive sample indices. Independent downstream shuffling must rerun a source-bound rival gate.

## D3 — Retain canonical support without weakening the witness schedule

**Choice.** Odd-index anchors cycle square sizes 3, 5, 9, and 12, matching canonical size profiles; even-index witnesses use the full difficulty-weighted 3..18 domain.

**Rationale.** The baseline profile-floor probe found only 2/60 exact profiles and zero easy/hard support. Deterministic anchors raise exact support while preserving broad witness sizes.

**Alternative rejected.** A probabilistic canonical-profile prior. It does not guarantee per-band support and can make small checks unstable.

**Measured result.** Final profile floor: 32/60 exact and envelope hits, with every band supported.

## D4 — Replace fake axes with four exact controls

**Choice.** Advertise only `grid_h`, `grid_w`, `fg_color`, and `scene_profile`; reject unknown keys, wrong types, and out-of-domain values. Add `observe_overrides` and declare no incompatible combinations.

**Rationale.** The baseline exposed clamping and unknown-key acceptance. Exact controls are more valuable than a larger nominal surface because they allow reproducible coverage and meaningful matrix checks.

**Alternative rejected.** Preserve `seed_row`, `seed_col`, `position_bias`, `edge_avoidance`, and texture aliases. Those controls were either partial, clamped, overlapping, or irrelevant to the curriculum defect, and keeping them would increase contract complexity without improving answer-bearing diversity.

**Measured result.** The override gate exercised 637 cases and 57,330 draws across three bands with zero findings.

## D5 — Validate the exact manifold but keep all canonical inputs

**Choice.** `self_check` accepts rectangular 3..18 grids with one seed or one seed plus one later, differently colored decoy; it rejects color 4, a first seed on the bottom row, malformed shapes/types, and extra cells.

**Rationale.** The old check admitted minimal impostors and a bottom-row degenerate. The new contract is strong enough to make semantic hooks meaningful while explicitly testing all four canonical pairs.

**Failure mode considered.** Overfitting validation to generated examples and accidentally rejecting canonical inputs. The tests call both `self_check` and `strict_canonical_like` on every canonical pair and compare an independent oracle to each canonical output.

## D6 — Declare the actual plausible rival

**Choice.** Expose the same pure `last_nonzero_seed` callable through `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; connect it to a `later_decoy` witness and `lesson_identifiable`.

**Rationale.** The rival fits every canonical pair because each has one nonzero seed, yet changes lawful generated decoy outputs. Naming it lets the shared semantic and lesson-census tools test the exact teaching failure rather than relying on informal notes.

**Limitation.** Passing one declared rival does not prove unique induction. Undeclared competitors remain an open domain question.

## D7 — Do not change canonical Racket behavior

**Choice.** Leave `repo/shared/data/canonical/puzzles.jsonl` unchanged. Exact-synchronize the selected base solution's `racket_target.target_code` to the canonical `program_solution`, keep the earlier behavior-equivalent executable in `raw_code`, and add provenance roles.

**Rationale.** The defect was curriculum and source binding, not rule semantics. The authority-sync check compared selected and canonical source text, so fixing the selected source was lower risk than changing a correct rule.

**Alternative rejected.** Rewriting the canonical rule. No behavioral disagreement justified it.

## D8 — Add reusable, independent tests and tooling

**Choice.** Add 49 task tests plus `workspace/reference_probe.py`.

The probe avoids importing the production rule implementation when computing oracle/rival outputs, uses portable canonical-data helpers, observes axes from grids, and emits JSON for exhaustive schedule starts. This gives future agents a small, deterministic way to test curriculum safety without rerunning the full battery.

## D9 — Stop the post-repair solve after one passing revision

**Choice.** Preserve the first visible-only implementation after it matched 3/3 demonstrations.

**Rationale.** The examples explicitly contained later distractors, so they distinguished first from last nonzero seed. Manufacturing a failed revision would create misleading training evidence. Earlier rule exposure is recorded as `yes`; no reference was consulted during the solve phase.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/033db13a9d37/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Proposed native parity relay

The separate `workspace/parametric/` family preserves production v2.0.0 and
generator SHA-256 `9a6756b67c901b2e0b973c4c2dd30524d20f364f6af1a556b6cfb33f4fbcdda4`.
Its `seed_mode=first` program is byte-exact canonical authority. In
`seed_mode=parity_relay`, the row-major first marker projects strict-below,
same-column-parity lanes; their first row-major original marker supplies the
canopy height, echo location and color, with fallback to the origin if no hit
exists. The input-derived mask is consumed by selection. This is contextual
gating, not iterative simulation. The canonical task's row/column orientation
remains semantic, so no D4 symmetry is claimed.

Independent review found that the initial two-demo basis allowed rightward-only
eligibility, target color extrema and incorrect bottom-edge behavior. The final
contract uses three core demonstrations and supports 3–6 demos with 1–4 queries.
Active visible echo, active bottom hit and no-hit fallback are mutually exclusive
cases; three exposes all three without restricting the query grammar. The
packet explicitly permits this narrower minimum. A second finding showed that
a Manhattan-distance contrast still allowed Euclidean nearest selection; the
visible core now places a later marker at squared distance 9 while the intended
row-major target is at squared distance 20. Protected before/after evidence and
the pre-repair sources are retained with the return.

The proposed semantic domain extends to nonempty 1..30 rectangular grids with
arbitrary counts of exact-integer markers, retaining input color 4 as reserved.
Independent RNG streams give matched inputs across settings, stable demo/query
prefixes and four distinct query profiles up to substantive 30×30 scenes.
Task-local independent oracle/rival/audit tools and native evidence record the
finite exercised scope. The selected production source and its unresolved
column-major-origin teaching audit remain unchanged; this separate proposal
does not resolve or reclassify that finding. Owner exact-source acceptance and
training admission remain separate from reviewer qualification.
