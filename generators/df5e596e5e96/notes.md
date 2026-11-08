# Working notes: df5e596e5e96

## 2026-10-03 review repair

Baseline `2.2.2` rejected one canonical 8-cell panel, lacked `RULE_HASH`, advertised dead/singleton controls, silently accepted unknown overrides, and sampled shape classes with distinct cell counts. That last choice let the wrong rule “same count means related; different count means unrelated” fit all five canonical pairs and every generated pair. The baseline also had no executable mirror, semantic rivals, witness contract, or complete-lesson identifiability check.

Version `3.0.0` keeps the selected Racket authority unchanged and pins `RULE_HASH = "dd7b7aac9913"`. It exposes one honest exact axis (`n_panels=3..5`), accepts all canonical inputs, constructs same-count unrelated motifs, alternates canonical one-color anchors with cross-color related panels, and shuffles panel order while preserving semantic witnesses. The Python mirror, declared rivals/witnesses, three-demo lesson hook, focused tests, and `workspace/semantic_census.py` make the teaching contract replayable.

Final generator SHA-256: `7eaedfe24e1c2faba9192e342314ad541f643291b3f17397db4754c9effb2ae3`.

Evidence:
- before failures: `checks/before_stages/`, `checks/tdd_red/`
- final 12-stage battery: `checks/after/checks/df5e596e5e96_after_battery_summary.json`
- focused tests: `checks/final_source/focused_tests.log`
- 300-lesson census: `checks/final_source/semantic_census.json`
- portable runtime test: `checks/portable_final/portable_tests.log`

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `7eaedfe24e1c2faba9192e342314ad541f643291b3f17397db4754c9effb2ae3`.

# Decisions for `df5e596e5e96`

## D1 — Keep the Racket rule immutable and pin it

**Input evidence.** The task already had a selected canonical Racket authority with normalized hash `dd7b7aac9913`. The baseline generator did not expose that hash or an independent mirror.

**Alternatives.** Change the authority to fit the baseline; trust catalog selection without a pin; or bind the generator to the existing authority and test a Python mirror.

**Choice.** Keep the authority unchanged, set `RULE_HASH = "dd7b7aac9913"`, and implement `rule_mirror` independently in Python.

**Probe.** All five canonical inputs must pass the validator and the mirror must exactly match all five canonical outputs; Racket rule smoke and authority sync must remain green.

**Limitation.** A mirror can share a conceptual bug with a reviewer. Canonical examples plus direct Racket smoke reduce, but cannot mathematically eliminate, that risk.

## D2 — Collapse the public override surface to one honest axis

**Input evidence.** Baseline controls included dead/singleton declarations, unknown keys were ignored, and difficulty-specific bounds contradicted the public `n_panels` range.

**Alternatives.** Preserve every advertised axis and implement a large cross-product; keep approximate controls; or remove claims that cannot be recovered exactly from the returned grid.

**Choice.** Retain only `n_panels=3..5`. It is exact, visible in grid width, and legal in every band. Unknown keys, booleans, non-integers, and out-of-range values fail loudly.

**Probe.** Focused tests exercise `n_panels` 3 and 5 under `None`, easy, medium, and hard; the repository override stage exercises all declared values and rejects an unknown key.

**Limitation.** Shape family, palette, and semantic profile remain deterministic internals rather than caller-controlled axes. This is deliberate until an exact observable contract is needed.

## D3 — Expand validation to the source-authoritative panel area

**Input evidence.** One canonical panel contains eight occupied cells, while the baseline validator capped generated/canonical panels below that value and rejected the canonical input.

**Alternatives.** Special-case that example; change the canonical row; or make the documented generator domain honestly include connected supports of 4–8 cells.

**Choice.** Accept and generate 4–8-cell, single-color, 4-connected supports in each width-5 panel.

**Probe.** `self_check` and `strict_canonical_like` accept all five canonical inputs, and structural mutation checks remain active in the battery.

**Limitation.** The authority can operate on inputs outside this training envelope. The validator defines a safe curriculum subset, not the complete program domain.

## D4 — Construct same-count unrelated motif pairs

**Input evidence.** The baseline gave each unrelated class a distinct area. The rival `same_count_implies_rotation` fit 5/5 canonical pairs and all generated pairs.

**Alternatives.** Add random noise and hope for collisions; occasionally sample same-area shapes; or build explicit unrelated motif pairs for every supported area.

**Choice.** Use curated 4-connected motifs and prevalidated same-count unrelated pairs for counts 4–8. Every normal scene includes at least one such pair.

**Probe.** The witness `same_count_unrelated` must fire, while the declared rival must disagree with the official mirror. The 300-lesson census records 400/400 witness and rival-disagreement hits per band.

**Limitation.** The motif catalog is finite. New motifs should be admitted only after orbit classification proves the intended unrelated/equivalent relation.

## D5 — Teach color invariance inside complete lessons

**Input evidence.** Canonical examples use color in a way that lets a color-sensitive relation rival fit all 5/5 pairs.

**Alternatives.** Randomize every panel color independently; keep monochrome data; or place controlled cross-color related examples so small lesson windows necessarily expose invariance.

**Choice.** Use monochrome anchors in schedule slots 0/1 and varied foreground colors in slots 2/3. Every sliding three-demonstration window therefore contains a cross-color related example without making color variation the sole cue.

**Probe.** `cross_color_related` fires on half the census examples and `color_sensitive` is refuted in every complete lesson while still fitting all canonical pairs.

**Limitation.** The 50% cadence is discoverable. It is a reproducible curriculum schedule, not an estimate of a natural color distribution.

## D6 — Use four semantic profiles, not unconstrained random class sampling

**Input evidence.** Small ARC training episodes contain three demonstrations and a query. Independent random examples can be individually valid yet collectively leave the rule ambiguous.

**Alternatives.** Optimize only pair-level diversity; assemble lessons in an external sampler; or make the generator’s sample-index schedule carry a complete teaching contract.

**Choice.** Cycle through `full_relations`, `rotation_duplicate`, `two_rotations`, and `paired_classes`. Set `EXAMPLES_NEEDED=3` and provide `lesson_identifiable` over the generator’s actual declared competitors.

**Probe.** Every cyclic start is tested in all three bands. The final census checks 300 lessons and reports zero ambiguity.

**Limitation.** Consumers that randomly permute or subsample examples can destroy the schedule guarantee. The lesson constructor must preserve consecutive sample indices or rerun the identifiability hook.

## D7 — Shuffle panel order after constructing semantics

**Input evidence.** The first repair cleared semantic rivals but produced only four distinct output matrices in a 120-pair lint probe.

**Alternatives.** Ignore output diversity because inputs differ; create more profiles; or shuffle already-constructed panel tokens while preserving each scene’s relation graph.

**Choice.** Deterministically shuffle panel order using the local generator context. This changes matrix layout without weakening witness guarantees.

**Probe.** A regression requiring at least 32 output matrices was observed red before the change. Final lint/diversity stages are green; the census measures 105/108/108 outputs per band.

**Limitation.** Permutation diversity does not equal semantic diversity. It is used only after the profiles establish distinct relation structures.

## D8 — Declare executable rivals and witnesses in production metadata

**Input evidence.** The baseline had no machine-checkable statement of which shortcuts mattered or why a sample was informative.

**Alternatives.** Describe risks only in prose; copy rival names into an external script; or expose executable `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and `WITNESS_RIVALS` from the generator.

**Choice.** Put the contract beside the sampler and make probes iterate the declarations rather than maintaining a second list.

**Probe.** The semantic gate and `workspace/semantic_census.py` execute the actual declarations. Both canonical shortcuts are first proven to fit every usable canonical pair, then required to be refuted by lessons.

**Limitation.** The contract is only as complete as its rival library. Undeclared shortcuts remain possible and should be added when discovered.

## D9 — Build a source-bound complete-lesson census

**Input evidence.** The generic semantic gate checks a small set of lessons, while this schedule has four possible starts and strong sequence-level claims.

**Alternatives.** Rely on the focused unit test’s 12 lessons; create a one-off notebook; or provide a reusable CLI that runs in both source and prepared runtime layouts.

**Choice.** Add `workspace/semantic_census.py`, with configurable lesson count and seed base, source hash binding, unique input/output counts, witness rates, competitor disagreements, and canonical-shortcut verification.

**Probe.** The focused test runs a 12-lesson smoke census. The final qualification runs 100 lessons per band (300 total) and writes `checks/final_source/semantic_census.json`.

**Limitation.** It is deterministic finite sampling, not exhaustive enumeration of seeds or all legal inputs.

## D10 — Preserve failed iterations and qualify the exact source

**Input evidence.** Test-first failures and the fixed-order output collapse were useful evidence of what the regressions detect.

**Alternatives.** Keep only final green logs; summarize failures without artifacts; or retain compact decisive failures alongside final evidence.

**Choice.** Keep the original red test log and intermediate lint failure, then bind final battery, focused tests, census, solve, and fresh-patch replay to the final generator SHA-256.

**Probe.** The return packager generates a source-only patch; that patch is applied with `git apply --check` to a fresh packet extraction and the focused suite is rerun there.

**Limitation.** A completed full battery is retained from the exact final generator bytes, but a later redundant rerun exceeded the outer command window during defect lint. It does not supersede the completed green run.

## 2026-10-24 native parametric promotion candidate

The reviewer added a task-local native family without changing the approved production generator or canonical rule.  `matrix_order=input` returns the canonical Racket source byte-for-byte (SHA-256 `dd7b7aac9913cfda3671bc02b7b8af33716140dd90702a08af92f45f4f8383e4`).  `matrix_order=relation_signature` first computes that canonical pairwise relation matrix, derives each row's counts of exact/rotation/reflection relations, then sorts panel indices by those input-dependent signatures and permutes both matrix axes.  This is a real A → intermediate → B dependency; a protected-Racket reverse-order ablation changes both retained witness outputs.

The native contract is under `workspace/parametric/`: thin `adapter.py`, bounded `promotion.json`, source/evidence `evidence/manifest.json`, focused tests, a replay helper, and a public-projection probe.  Same-seed inputs are matched across settings.  The adapter supports 2–6 demonstrations and 1–8 queries; the first two demonstrations uniquely select the setting and refute the five declared shortcut orders (reverse input, total relation degree, row sum, rotation count, and panel color).  Qualification uses three demonstrations and four distinct queries for seeds 0 and 17.

Exact approved-source pins:
- generator: `7eaedfe24e1c2faba9192e342314ad541f643291b3f17397db4754c9effb2ae3`
- prototype: `bf92bac33bb6f63c559b7195bb6311f74b02208af530858e8bc485b67a0d56d8`
- adapter: `bd326ed10196f23343a8591141f28e126b6be6a96ba63c7a454afa4fc87e6996`
- promotion contract: `078229f96b9aec104b8bf27f01032f651083f9493c996da918216a48e7344d0b`
- source/evidence manifest: `59c161623383917f2181d481727eac35f465c4fe0182311eb5974b047b38639c`

Retained evidence:
- `checks/df5e596e5e96/qualification/{qualification,execution}.json`: native protected-Racket qualification for both settings × seeds 0/17.
- `checks/df5e596e5e96/sequential-dependency-witness.json`: two qualified wrong-order counterfactual cases; owner-path replay is in `sequential-witness-owner-replay.json`.
- `workspace/parametric/evidence/current/probe.json`: six protected-Racket episodes, 42 labels, zero Python/Racket mismatches, zero declared-rival ambiguities, all 40 supported demo/query count combinations prefix-stable and unique, and lawful `5×17`/`5×29` boundaries.
- `checks/df5e596e5e96/parametric/public-export-check-approved-source.json`: four masked public challenges with exact visible-byte IDs, distinct inputs, three demonstrations, and four queries.

The fixed five-row panel grammar cannot lawfully produce `30×30`; its natural boundaries are `5×17` (three panels) and `5×29` (five panels).  The finite rival audit is not a universal uniqueness proof, and qualification is reviewer-reported readiness rather than owner acceptance or training admission.  A separately tested lesson-schedule repair is retained only as `workspace/parametric/evidence/current/deferred-approved-generator-lesson-repair.patch`; it is not integrated because changing the approved generator would invalidate the native source binding.

Next action: integrate these exact bytes, rerun native qualification and the protected-Racket causal witness on the live source, then make the explicit owner acceptance decision.  The two optional peer checks were left unrun after completing MAIN.

