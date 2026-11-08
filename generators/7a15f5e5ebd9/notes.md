# Working notes: 7a15f5e5ebd9

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `0ce11d69f53e5e5fd455a91078df585baf1eb1fab3f11cbf25738884a38cbd5b`.

# Decisions for `7a15f5e5ebd9`

The baseline retained no substantive design rationale beyond a short rule summary, so “original rationale” below is marked **unknown** when it cannot be recovered from code or notes. Decisions are tied to finding IDs in `REVIEW.md`.

## D1 — Preserve the canonical transformation

- **Decision:** Keep rule hash `9a1bc43f327f` and the executable Racket behavior unchanged.
- **Original rationale:** The baseline rule description says to replay yellow offsets from the 9 at every red 2 anchor; no further rationale was retained.
- **Evidence:** Baseline rule smoke already passed, while validator/distribution gates failed (R1/R2). Final Racket smoke applies 120/120 without crashes and agrees with the Python mirror 120/120.
- **Rejected alternative:** Change the rule to require fully in-bounds copies or a connected yellow template. That would contradict canonical examples and would “fix” the validator by changing the task.
- **Failure mode guarded:** Accidental semantic drift while repairing the sampler.

## D2 — Model the five canonical inputs as linked profiles

- **Decision:** Encode each official input as a complete profile joining `(height, width, template, anchor offsets)`; allow global translation only when the linked signature and clipping count remain intact.
- **Original rationale:** Unknown. The baseline sampled dimensions, shape, and anchors independently.
- **Why:** Partial marginal support can look canonical while producing combinations never demonstrated by the task. Linked profiles give exact empirical support and make `strict_canonical_like` falsifiable.
- **Rejected alternatives:** (a) Independent resampling of canonical dimensions/templates/anchor counts; (b) memorizing five literal grids without translation. The first creates unsupported recombinations; the second gives poor diversity.
- **Probe:** `test_all_canonical_pairs_are_accepted_exact_and_linked` and `test_negative_recombination_is_lawful_but_not_canonical`.

## D3 — Use a ten-slot mixed curriculum

- **Decision:** Schedule five canonical slots, four teaching slots, and one single-anchor slot. Every cyclic window of four slots contains at least one teaching case.
- **Original rationale:** Unknown; baseline draws had no lesson-level schedule.
- **Why:** Four demonstrations are the configured lesson size. Cyclic coverage makes identifiability a lesson property rather than relying on pooled witness frequency.
- **Rejected alternatives:** Pure random mixing could produce all-canonical or all-easy lessons; a fixed canonical/teaching block would make some cyclic starts ambiguous.
- **Probe:** `test_every_four_slot_window_is_identifiable` checks all ten cyclic starts; the 300-lesson census checks production assembly.
- **Limit:** A deterministic schedule is auditable but creates periodic structure a model could potentially exploit.

## D4 — Keep five canonical templates and add two long-range disconnected templates

- **Decision:** The declared template domain is exactly seven shapes: five complete canonical templates and `scatter_long_a`/`scatter_long_b`.
- **Original rationale:** Baseline had four nearby connected shapes, some not matching official support.
- **Why:** The canonical templates preserve task fidelity. Two lawful extrapolation templates supply long-range offsets, disconnected components, holes, asymmetry, overlap, and anchor-collision witnesses without changing palette or operation.
- **Rejected alternatives:** Arbitrary random yellow clouds would maximize morphology but risk teaching a different task and make exact overrides/validator behavior hard to audit. Connected-only templates cannot refute the “nearest component only” shortcut.
- **Probe:** semantic witnesses `long_range_offsets`, `disconnected_template_uses_all_yellow`, `asymmetric_template`, and `template_bbox_has_holes`.
- **Limit:** Seven templates are not exhaustive; template memorization remains possible.

## D5 — Grid dimensions 8..18

- **Decision:** Exact override domain is 8..18 for both dimensions. Default linked-canonical slots use their official dimensions; noncanonical slots use difficulty-skewed draws in 11..18.
- **Original rationale:** Baseline advertised 6..12 by 8..14 but defaulted to a narrower range; no justification was retained.
- **Why:** Lower bound 8 supports all declared templates and at least one useful destination; upper bound 18 allows long-range, above/left, overlap, and clipping scenes without making grids disproportionately large.
- **Rejected alternatives:** Keep baseline bounds (insufficient support for larger canonical profiles and teaching geometry) or expand to arbitrary ARC sizes (unnecessary search/runtime cost and morphology drift).
- **Probe:** exact override boundary matrix and `observe_overrides`; final override stage covers all declared values and combinations.

## D6 — One to five red destination anchors

- **Decision:** Exact domain is 1..5 anchors; every anchor must contribute at least one visible yellow cell after red anchors are repainted.
- **Original rationale:** Baseline claimed 1–2 but effectively produced one.
- **Why:** One anchor preserves the lawful branch. Multiple anchors teach replication, overlap, union behavior, and color priority. Five is enough for dense interaction without dominating the source scene.
- **Rejected alternatives:** Require at least two (loses lawful single-destination branch) or allow anchors that produce no visible contribution (creates semantically inert controls).
- **Probe:** `single_destination_branch`, `multiple_destinations`, exact `n_anchors` overrides, and contribution checks in `self_check`.

## D7 — Accept per-cell clipping; use union; repaint red anchors last

- **Decision:** Each translated yellow cell is clipped independently. Overlapping copies form a set union. Red anchors are repainted after all yellow stamps.
- **Original rationale:** The executable canonical rule already has these semantics, though the baseline validator incorrectly required whole stamps in-bounds.
- **Why:** These choices exactly match canonical behavior and distinguish three plausible rules that canonical examples alone do not fully resolve.
- **Rejected alternatives:** Drop an entire copy if any cell clips; XOR overlapping copies; let yellow overwrite red.
- **Probe:** `test_teaching_profile_refutes_clipping_overlap_and_anchor_priority_shortcuts`, `test_rule_mirror_preserves_red_anchors_after_clipped_union_stamping`, and the retained clipping-witness regression.

## D8 — Reduce AXES to four exact, observable controls

- **Decision:** Advertise only `grid_h`, `grid_w`, `template`, and `n_anchors`; reject unknown names.
- **Original rationale:** Baseline exposed nine axes, including dead palette aliases, singleton palette/color counts, singleton position/density controls, and invalid degenerate textures.
- **Why:** A control should be externally observable and honored exactly. Removing fake controls is more honest than adding metadata-only variation.
- **Rejected alternatives:** Keep compatibility aliases (`texture`, `palette_kind`) or declare invalid fixtures as ordinary values. Both caused false passes and unlabeled/invalid data.
- **Probe:** `test_exact_override_observation_boundaries_and_unknown_rejection`; final override contract has zero findings over 41,130 draws.

## D9 — Construct teaching witnesses algebraically

- **Decision:** Derive overlap/collision anchor relations from differences among template offsets, then fill remaining anchors with bounded scored candidates.
- **Original rationale:** No baseline teaching constructor existed.
- **Why:** An initial exhaustive pair search was correct but unnecessarily quadratic and made semantic/override gates slow. Offset-difference construction directly creates the required collision and overlap relation.
- **Rejected alternative:** Enumerate every legal anchor pair on every attempt. It was too slow and added no semantic value.
- **Probe:** all teaching slots must simultaneously have clipping, overlap, anchor collision, and an above/left destination; generation fails loudly if construction cannot satisfy them.

## D10 — Seed-mix schedule selection without breaking cyclic lessons

- **Decision:** Use `(sample_index + (seed ^ (seed >> 3))) mod 10`.
- **Original rationale:** Baseline had no schedule.
- **Why:** Tools often hold `sample_index` fixed while varying seed. A sample-index-only schedule collapsed such probes to one prototype; adding a seed-derived phase restores cross-seed diversity while consecutive indexes still traverse the same cyclic ordering.
- **Rejected alternatives:** Randomly choose the slot (breaks cyclic-window guarantee) or use sample index alone (fails fixed-index diversity).
- **Probe:** `test_fixed_sample_index_does_not_collapse_seed_diversity` was written red first, then passed after this change.

## D11 — Declare executable rivals and witnesses

- **Decision:** Publish 11 rival functions, 12 witnesses, four canonical-fitting shortcuts, and a lesson-level identifiability hook.
- **Original rationale:** Unknown; baseline had no semantic contract.
- **Why:** Surface diversity is not enough. A named witness must actually make its rival disagree with the authoritative behavior, and each assembled lesson must eliminate all declared rivals.
- **Rejected alternative:** Count geometric properties only. The intermediate clipping witness proved that a property can occur while its rival still returns the same output (R4).
- **Probe:** final semantic gate, all-cyclic-window test, and 300-lesson census.
- **Limit:** Declared rivals are finite and cannot cover every possible shortcut.

## D12 — Narrow the clipping witness to an output distinction

- **Decision:** `per_cell_boundary_clipping` fires only when the canonical result differs from `drop_entire_clipped_copy`, not merely when any translated offset is out of bounds.
- **Original rationale:** Initial repair used the broader geometric condition.
- **Why:** A clipped anchor can be output-redundant when other anchors reproduce all surviving cells. Such an example does not teach per-cell clipping.
- **Rejected alternative:** Keep the broad witness and downgrade the semantic warning. That would overstate teaching value.
- **Probe:** exact retained counterexample in `test_boundary_clipping_witness_requires_an_output_distinguishing_copy`; red and green logs are retained.

## D13 — Synchronize duplicate Racket text without changing behavior

- **Decision:** Remove two comments from the selected `racket_target.target_code` so it exactly matches canonical active source.
- **Original rationale:** The duplicate appears to have been a beautified copy; no rationale was retained.
- **Why:** Exact active-authority synchronization is a required gate and avoids ambiguous source identity. Comment stripping already showed semantic equivalence, and execution parity passed.
- **Rejected alternatives:** Change canonical source, or leave a diagnostic divergence. Neither adds value.
- **Probe:** before/final authority-sync logs plus unchanged rule hash `9a1bc43f327f`.

## D14 — Retain failures and replay the final patch from scratch

- **Decision:** Keep the baseline failure, the 11-green/1-semantic-failure intermediate battery, the red/green clipping regression, final battery, census, audits, and fresh patch replay.
- **Why:** This distinguishes measured repair from a final-only success claim and binds the handoff to exact source bytes.
- **Fresh replay:** `git apply --check` and `git apply` both exited 0; final generator/test/authority hashes match; 12 focused tests pass.
- **Limit:** The full battery was not rerun in the fresh extraction because the exact source hash plus focused fresh tests and the already completed final battery provide the required replay chain.
