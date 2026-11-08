# Working notes: 961add4a2688

## Intended rule

A complete color-8 rectangular border encloses colored markers. Preserve the border and, independently for each interior column, move its nonzero markers to the top interior cells while preserving their original top-to-bottom order. All cells outside the frame remain background 0. The selected canonical Racket authority is unchanged and is pinned by `RULE_HASH = "9c6db5aba1ba"`.

## Review lead and reproduced baseline defects

I used return `review-51d5ced7ad16a1b9:v0001` only as a lead, then remeasured the pinned baseline source `50ce3ffef7e620a22f6dfc3de8e0716aa79446cd48d6cb308b1a2c4435e2e84a`. The baseline omitted the rule hash; exposed inert `palette_kind`, `palette_size`, `n_distinct_colors`, and helpful `texture` controls; advertised marker values that active difficulty branches rejected; accepted malformed scenes; and frequently failed to disprove sorting colors before packing. The before override probe completed 104,040 draws and retained 5,499 findings. The before full battery remained incomplete after its blocking lint/defect evidence was saved.

## Current design decisions

- Replace the broad stochastic grammar with a constructive four-slot schedule over the four canonical size/palette signatures: `8x9/p6`, `9x10/p8`, `9x11/p8`, and `10x10/p6`.
- Expose only four exact pixel-observable controls: `scene_profile`, `n_markers` (6 or 7), `column_pattern` (`separate`, `stacked`, `mixed`), and `frame_position` (`top_left`, `center`, `bottom_right`). Unknown or mistyped overrides fail closed.
- Use a complete frame of at least `6x6`, place every marker strictly inside it, require at least two marker colors and visible upward motion, and reject outside nonzero cells, extra/missing frame cells, ragged grids, invalid colors, and identity examples.
- Schedule four demonstrations. Every five-pair consecutive window, with any one pair used as the query, contains order-bearing stacks and disproves the declared ascending-sort, descending-sort, pack-down, keep-first, and identity rivals.
- Keep generation constructive rather than rejection-heavy. `observe_overrides` independently recovers every exact control from pixels.

## Final evidence

Final generator SHA-256: `63db3916d9292d959ddcadda068e28531d41d1954f0dbb27d5120a22045f68c2`.

- All 12 native battery stages passed when run individually against the final source. The aggregate battery controller did not produce a completed summary; it stopped at the `defect_lint` handoff even though the same stage and all remaining stages passed in isolated public invocations.
- Task-local portable tests: 318/318 passed.
- Exact override gate: 5,940/5,940 draws accepted, with zero findings, warnings, or explicit rejections; unknown keys were rejected.
- Independent finite probe: 216 exact override cases, 36 five-pair lesson windows, 180 query rotations, and 900 declared-rival rotation checks, with zero failures.
- Racket-backed census: 300/300 materialized lessons, 1,500 labelled pairs, 1,489 unique inputs, and 1,500/1,500 query rotations, with zero ambiguities, hook warnings, materialization errors, or scoring errors.
- Post-repair visible-only solve: first retained program passed all four demonstrations; earlier rule exposure was declared `yes` and reference consultation during the solve was `no`.

## Known limits and open findings

The semantic evidence is finite and covers the five declared rivals, not every possible hypothesis. The four-slot curriculum is intentionally structured rather than iid. The selected domain supports canonical inputs plus the four constructive profile families; it does not attempt every lawful 2–12-marker scene accepted by the rule. No Racket source was changed. The unrelated repository archival-identity regression for `defba1ab4f90` is present in an untouched packet and remains outside this task.
## Current reviewer considerations

Source SHA-256: `63db3916d9292d959ddcadda068e28531d41d1954f0dbb27d5120a22045f68c2`.

# Decisions for 961add4a2688

## D1 — Preserve the selected Racket authority

**Input choice:** Keep the canonical program unchanged and pin `RULE_HASH = "9c6db5aba1ba"`.

**Original rationale:** The baseline omitted the hash; no rationale was recorded. The canonical examples and native rule-smoke identify a stable column-wise packing rule.

**Alternatives considered:** Rewrite or normalize the Racket rule; derive labels from the Python mirror.

**Decision:** Reject both. The selected authority already produces the intended outputs. The Python implementation is a test mirror and rival oracle, not a replacement label source.

**Probe/failure mode:** `rule_smoke` and `authority_sync` must pass. Any generator change that requires a different rule is out of scope unless canonical evidence changes.

## D2 — Use four canonical-like scene profiles

**Input choice:** Exact profiles `8x9/p6`, `9x10/p8`, `9x11/p8`, and `10x10/p6`.

**Original rationale:** Unknown. The baseline rarely hit exact canonical profiles.

**Alternatives considered:** Arbitrary 8–14 grids and palette sizes; replaying only the five canonical inputs.

**Decision:** Use the four distinct canonical signatures while randomizing frame location, marker columns, colors, and order. This gives exact profile-floor support without memorizing grids.

**Probe/failure mode:** The profile-floor check requires at least one exact hit in every band. The 80-draw anti-replay test requires at least 72 distinct grids.

## D3 — Restrict markers to 6 or 7

**Input choice:** `n_markers` is an exact observable axis with values 6 and 7.

**Original rationale:** The baseline advertised 2–12 but active difficulty branches and validation disagreed.

**Alternatives considered:** Preserve 2–12; difficulty-dependent hidden ranges.

**Decision:** Use only counts that fit every profile/pattern constructively and provide enough columns/stacks to teach order preservation. Do not advertise unsupported values.

**Probe/failure mode:** Every band/profile/pattern/position/count combination is generated and observed exactly in focused tests and the standalone probe.

## D4 — Replace palette aliases with semantic geometry controls

**Input choice:** Expose `scene_profile`, `n_markers`, `column_pattern`, and `frame_position` only.

**Original rationale:** The old palette/texture controls were copied from a generic axis template and were not read by construction.

**Alternatives considered:** Keep `palette_kind`, `palette_size`, `n_distinct_colors`, and `texture`; silently ignore unknown controls.

**Decision:** Remove inert controls. The profile encodes the visible palette cardinality, while the other three axes are directly recoverable from pixels. Unknown keys and wrong types fail closed.

**Probe/failure mode:** Native override gate: 5,940/5,940 accepted, zero findings/warnings, unknown key rejected. Independent probe: 216/216 exact cases.

## D5 — Four demonstrations and rotation-safe schedule

**Input choice:** `EXAMPLES_NEEDED = 4`; a four-slot cyclic schedule supplies mixed, separate, stacked, and mixed examples. Actual lessons contain four demonstrations and one query.

**Original rationale:** The prior random curriculum did not guarantee order-bearing evidence.

**Alternatives considered:** Three demonstrations; iid sampling; test only the production query position.

**Decision:** Four demonstrations are the smallest robust choice for this finite rival set. Test every query rotation because downstream assembly permits a pair to be held out at any position.

**Probe/failure mode:** The independent probe checks 108 lesson windows (36 cyclic starts per band) × 5 rotations = 540 rotations and 2,700 rival checks. The Racket census checks 300 lessons and 1,500 rotations. Both found zero surviving declared rivals that disagree on the query.

## D6 — Make validation structural and fail closed

**Input choice:** Require a rectangular ARC grid, exactly one complete color-8 border of at least 6×6, zero exterior, 2–12 interior markers using at least two colors, and at least one upward move.

**Original rationale:** Baseline `self_check` only checked coarse counts and allowed malformed or identity scenes.

**Alternatives considered:** Validate only generated defaults; repair malformed inputs inside the oracle.

**Decision:** Reject malformed scenes at the domain boundary. Keep `strict_canonical_like` equal to the lawful structural validator so canonical examples and generated inputs share one contract.

**Probe/failure mode:** Focused tests mutate frame cells, add outside markers, create identity-packed columns, rag grids, and invalid cell types.

## D7 — Declare executable witnesses and rivals

**Input choice:** Rivals are ascending sort, descending sort, downward pack, keep-first, and identity. Witnesses are ascending/descending stacks, multi-marker columns, upward motion, and top-versus-bottom distinction.

**Original rationale:** Prior audit demonstrated ascending-sort survival but the baseline had no executable semantic contract.

**Alternatives considered:** Text-only notes; a copied rival list in the external probe; claim universal identifiability.

**Decision:** Bind witnesses to executable rivals in the generator and make the probe read the current declarations dynamically. `CANONICAL_SHORTCUTS` is empty because these rivals are not asserted to fit every canonical pair.

**Limitation:** Passing this finite family does not prove uniqueness against every possible rule.

## D8 — Keep audit targets unchanged

The required audits found reproducible lesson ambiguities in `9adaf46a8128` and `a80c6418f6bc`. Those generators are evidence-only targets and were not edited. Exact inputs, selected Racket outputs, rival outputs, hashes, and commands are retained under `checks/audit/`.
