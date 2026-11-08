# Working notes: 2ca60ab198d6

## Review repair 2026-10-04

The selected v2.0.1 baseline had no `RULE_HASH`, advertised dead or overlapping
axes/textures, silently accepted unknown overrides, and offered no executable
semantic contract. The 12-stage before battery reported 7 green, 2 advisory,
and 3 failures; the override audit alone found 7,491 issues. Canonical examples
also shared three exact shortcuts: every rejected guide was zero, selected rows
alternated, and exactly three rows were selected.

Version 3.1.0 replaces the sampler with six exact, pixel-observable axes and a
four-profile deterministic teaching cycle. It pins the unchanged canonical rule,
validates unknown and malformed overrides fail-closed, exposes
`observe_overrides`, checks canonical support, and declares independent rivals,
witnesses, and lesson identifiability hooks. Every payload row is nonempty and
payload color 7 appears in both selected and rejected rows.

The first 100-per-band census found normal lessons unambiguous but 221/1,500
artificial query rotations ambiguous when the sole four-selected example was
held out. A failing regression reproduced that exact `first_three_selected`
case. The irregular profile was changed from three to four selected rows, making
the witness redundant: the final census reports 0/300 ambiguous lessons and
0/1,500 ambiguous rotations.

`workspace/cyclic_lesson_probe.py` is a reusable source-bound probe. It exhausts
requested cyclic starts across all bands, iterates declarations rather than a
copied rival list, checks exact-axis boundaries, and records source hashes and
finite-audit limitations. No prior associated return was available as a lead;
`evidence/associated_notes.jsonl` was empty.
## Current reviewer considerations

Source SHA-256: `a9bb48897a774b2eff60fdfefefb19a9015391e56bbb906680d9d3db419f2151`.

# Decisions for 2ca60ab198d6

## D1 — Preserve the canonical authority

**Choice.** Keep the Racket rule unchanged and pin `RULE_HASH = "a6ff93ed49cd"`; use a small independent Python `rule_mirror` only for source-bound tests, rivals, and probes.

**Rationale.** Every canonical pair already expresses the intended filter-and-crop law, and the before `rule_smoke` and authority stages were green. The defect was in sampling and contracts, not labels.

**Alternatives rejected.** Rewriting the Racket implementation would add authority risk without addressing lesson ambiguity. Treating the Python mirror as label authority was also rejected; final labels and the exact shortcut witness were checked with the supported Racket bridge.

**Evidence and failure modes.** Final `rule_smoke`, `racket_lint`, and `authority_sync` are green. A future rule change requires updating the pin and rerunning all parity checks; matching a mirror alone is insufficient.

## D2 — Replace broad fictional axes with six exact observable controls

**Choice.** Advertise only `grid_h`, `grid_w`, `n_keep`, `selector_style`, `payload_density`, and `n_payload_colors`.

**Rationale.** Each value can be recovered from pixels by `observe_overrides`, has a constructive finite domain, and changes a task-relevant property. The baseline’s palette aliases, singleton/inert declarations, and degenerate textures produced thousands of override findings and outputs outside a clean training contract.

**Alternatives rejected.** Keeping legacy aliases as diagnostics would preserve confusing public surface area. Supporting empty outputs, all-kept identity-like inputs, or blank payloads was unnecessary and weakens teaching.

**Probe.** The final override gate checks 304 cases across three bands and 27,360 draws. The task-local probe independently checks all 432 combinations of exact boundary and categorical values.

**Limits.** Boundary Cartesian checks do not exhaust every seed for every interior integer value, but the repository override gate additionally samples all declared values.

## D3 — Keep dimensions near the canonical family without collapsing diversity

**Choice.** Lawful dimensions are height 6–10 and width 7–11. The `canonical_alternating` and `four_selected` profiles draw from the three exact canonical shape profiles; the other profiles use band-aware ranges.

**Rationale.** The baseline’s final profile-floor evidence had no canonical-profile hits. Retaining exact canonical support prevents a generated-only shape cue while still allowing ten output shapes and all three difficulty bands.

**Alternatives rejected.** Making every draw canonical-sized would overfit geometry; making canonical support probabilistic without a schedule could miss the per-band floor.

**Evidence.** Final profile floor: 27/60 exact-profile and envelope hits, with all three canonical inputs accepted.

## D4 — Use a deterministic four-profile teaching schedule

**Choice.** `schedule_profile(seed, sample_index) = profiles[(2*seed + sample_index) mod 4]`, with four consecutive examples covering `canonical_alternating`, `nonzero_selector`, `four_selected`, and `irregular_selection`.

**Rationale.** The schedule gives every normal four-demo lesson a counterexample to all declared rivals, avoids diagonal aliasing in common seed/index scans, and guarantees canonical support.

**Alternatives rejected.** Pure random profile selection could produce ambiguous windows. A schedule keyed only by `seed + sample_index` caused diagonal sampling to alias during early defect-lint work. A longer schedule added no teaching value.

**Failure found and repair.** The first production census showed 0/300 normal ambiguities but 221/1,500 rotated ambiguities: holding out the sole four-selected profile let `first_three_selected` survive. A failing test captured the case. Changing the irregular profile from three to four selected rows gives every five-example window two fixed-three counterexamples; the final census has 0/1,500 rotated ambiguities.

## D5 — Make selector semantics visible

**Choice.** Support `zero_only`, `nonzero_only`, and `mixed` rejected-guide styles. Selected guides are always 7; rejected nonzero guides are chosen from the payload palette excluding 7.

**Rationale.** All canonical rejected guides are zero, so “keep every nonzero guide” fits every public demonstration. Nonzero rejected guides are the minimal direct counterexample.

**Alternatives rejected.** Using one fixed rejected color would still teach a brittle binary palette association. Arbitrary 0–9 values including 7 would violate the law.

**Probe.** `checks/question/racket-final.json` is an emitted mixed-guide case where the intended Racket result has 2 rows while the nonzero shortcut returns 5.

## D6 — Make row-position and count shortcuts visibly wrong

**Choice.** Include adjacent and irregular selected rows, and use scheduled keep counts `3, 2, 4, 4`.

**Rationale.** All canonical selected rows alternate and all canonical outputs contain exactly three rows. Irregular placement refutes alternating-row inference; two separate four-row profiles make fixed-three refutation robust to query rotation.

**Alternatives rejected.** Random keep-row sampling alone can accidentally alternate. A single four-row profile was sufficient for fixed production windows but fragile under held-out rotations.

**Limits.** The lawful count range is intentionally 2–4. One or all selected rows are excluded because they create weak or identity-like examples and are not needed to teach the rule.

## D7 — Control payload density and palette by observable buckets

**Choice.** Every row receives at least one payload cell. Exact sparse/medium/dense fill counts land below 1/3, from 1/3 through below 2/3, and at least 2/3. Payloads use exactly 2–8 nonzero colors.

**Rationale.** This makes every row’s fate visually meaningful, permits exact observation, and covers both canonical-like and broader textures.

**Alternatives rejected.** Independent Bernoulli fill could miss rows, colors, or density buckets. A fixed 45% baseline density was not an exact axis.

**Failure modes.** Very small sparse canvases can conflict with palette cardinality; `_fill_count` explicitly reserves enough cells for every row and color while staying inside the bucket. The 432-case boundary probe covers the smallest canvas with eight colors.

## D8 — Place payload-7 decoys on both sides of the selection boundary

**Choice.** Reserve at least one payload color-7 cell in a selected row and one in a rejected row for every generated input.

**Rationale.** This refutes the plausible rule “keep rows containing any 7” and prevents the guide color from becoming a whole-row presence cue.

**Alternatives rejected.** Excluding 7 from payloads would make the left-column role less explicit and preserve the shortcut. Placing 7 only in selected payload rows would strengthen it.

**Evidence.** The witness fires in 600/600 semantic-gate inputs and 7,680/7,680 cyclic-probe materializations.

## D9 — Fail closed and validate structure independently of metadata

**Choice.** Reject unknown override keys, invalid difficulty values, booleans masquerading as integers, wrong types, and out-of-range values. `self_check` validates rectangularity, integer colors, dimensions, keep/drop counts, nonempty payload rows, and payload color cardinality from the grid itself.

**Rationale.** Silent override typos were a baseline failure. Metadata-dependent validation can certify malformed grids.

**Alternatives rejected.** Clamping out-of-range controls conceals broken caller assumptions. Accepting unknown keys for forward compatibility makes contract testing meaningless.

**Limit.** Mutation sensitivity is 23/63, not universal; color swaps that preserve the lawful domain are correctly accepted rather than treated as structural defects.

## D10 — Declare finite rivals and reusable evidence, not uniqueness claims

**Choice.** Declare four competitors (`nonzero_selector`, `alternate_from_first_keep`, `first_three_selected`, `any_seven_in_row`), four witnesses, and `lesson_identifiable`; add `workspace/cyclic_lesson_probe.py`.

**Rationale.** These include every exact shortcut found to fit the canonical pairs plus one domain-plausible payload shortcut. Declarations let shared tools discover the contract without duplicating names.

**Alternatives rejected.** Claiming universal identifiability from a handful of examples is unjustified. A probe with a hard-coded rival list would drift from the generator.

**Limits.** The final evidence refutes only declared deterministic rivals over finite schedules and samples. Other conceptual rules may remain; the reports state this as unknown rather than a proof.

## D11 — Prior evidence and retained failures

`evidence/associated_notes.jsonl` was empty, so no prior return was used as an implementation lead. The baseline source and current measurements were treated as authoritative. Decisive failures are retained: TDD reds, the incomplete aggregate wrapper run, early defect/profile failures, the first 221-rotation census, and the superseded solve episodes bound to older source hashes.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/2ca60ab198d6/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Current parametric extension: dependent column guide

The canonical generator and Racket authority remain unchanged. The separate
`workspace/parametric/` implementation adds `selection=rows|rows_then_columns`.
The default returns the exact canonical Racket source. In the alternative,
row selection binds the first surviving payload row; that row determines the
second-stage column mask. This is input-dependent contextual gating, not a
claim of iterative simulation. A wrong original-top-row mask is the causal
counterfactual used for protected-Racket witness replay.

The setting-independent constructive sampler supports 2–6 demos (default 3),
1–4 distinct queries (default 4), and a substantive 30x30 query. Fixed demo and
query RNG indexes preserve the first-turn content when query counts change.
The first two demonstrations distinguish the modes and finite explicit
shortcuts; labels, rival tests and public-file invariants are checked by the
task-local reusable audit. See `workspace/parametric/README.md` for grammar,
limits, exact commands and the owner qualification/acceptance step. The
production generator's existing approval and historical audit disposition
are not changed by this separate proposed family.

Short-demo self-review found and repaired a seed-44 sorted-output shortcut.
The retained original protected-Racket case fits both demos yet changes three
query labels; the new constructive order witness and explicit sort rivals
remove this hole without increasing demo count. The original lesson remains
underidentified evidence, not a clean single-answer training example.
