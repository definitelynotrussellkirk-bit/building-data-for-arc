# Working notes: 0a1bba9e3d93

## Review outcome

- Baseline v2 failed lint, self-check mutation audit, defect lint, and override contract; profile and semantic stages were advisory.
- Rebuilt v3 around a shared structural analyzer and total constructive generation for all declared overrides.
- Pinned canonical rule hash `386c52a84df2`; no Racket/canonical source changed.
- Added canonical profile recurrence, deterministic four-profile lessons, two canonical-fitting rivals, linked witnesses, and lesson identifiability.
- Added independent oracle, task-local tests, and source-bound production/cyclic lesson census.
- Final generator SHA-256: `b16cab45787ea7e24357080bd6b8e173650fbd7d87a04152f9adc2c0ae7e3b0e`.
- Final required battery: 12/12 green. Task-local suite: 41 passed.

## Retained limitations

The sampler covers four linked three-cell connected morphologies with two-cell deltas and single-color panels. Evidence refutes the declared rival set over recorded finite seeds and the current runner policy; it does not prove arbitrary-shape induction.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `b16cab45787ea7e24357080bd6b8e173650fbd7d87a04152f9adc2c0ae7e3b0e`.

# Design decisions for 0a1bba9e3d93

## D1 — Preserve the selected authority and pin it

**Choice.** Keep the canonical Racket authority unchanged and add `RULE_HASH = "386c52a84df2"` to the generator.

**Original rationale.** The before rule-smoke and authority-sync stages already showed the selected rule executing canonical outputs correctly; the defects were in the sampler and its contracts, not the rule.

**Alternatives considered.** Rewriting the Racket rule would add authority risk without repairing distribution or lesson ambiguity. Leaving the hash unpinned would continue allowing silent source drift.

**Probe and result.** Canonical pairs are checked by an independent Python oracle and the live Racket gates. The final authority-set hash equals the baseline hash and all authority stages pass.

**Limit.** The repository still records an archival base-source divergence. This return neither resolves nor broadens it.

## D2 — Advertise only constructive exact axes

**Choice.** Declare exactly `grid_h=3..12`, `panel_w=3..8`, and `texture=plain|diff_query|clip`; reject unknown keys, wrong types, invalid difficulties, and out-of-domain values. No incompatibility exemptions are needed.

**Original rationale.** The imported generator advertised broader exact domains than its difficulty-specific draws could honor and silently swallowed unknown keys. Its `no_growth` degenerate contradicted the intended proper-growth teaching contract.

**Alternatives considered.** Keeping difficulty-narrow exact domains would make advertised controls depend on hidden band context. Declaring thousands of incompatibilities would document avoidable construction failures rather than eliminate them. Keeping `no_growth` would introduce identity rows that do not teach the selected growth rule.

**Probe and result.** The task tests enumerate 10 heights × 6 widths × 3 textures × 4 difficulty settings = 720 exact combinations and compare realized observations to the request. The final override gate reports no findings or warnings and rejects an unknown key.

**Failure mode/limit.** New axes must be added to construction, observation, tests, and the full Cartesian test together; metadata-only additions should fail.

## D3 — Use constructive linked morphology instead of rejection sampling

**Choice.** Use four small connected BEFORE families, each with a linked two-cell delta and a different-query shape that remains valid at the minimum 3×3 panel.

**Original rationale.** Exact override support requires every legal size/texture combination to succeed deterministically. Random walks plus post-hoc filtering made small boards fragile and made accepted distributions hard to characterize.

**Alternatives considered.** Arbitrary random polyomino growth offers more morphology but requires rejection sampling, conditional override failures, or a much larger constructive library. A single family would be too easy to memorize.

**Probe and result.** Every generated board passes the shared analyzer, the independent oracle, and the Racket rule. Default 96-draw samples produce at least 90 distinct input/output signatures per band setting.

**Failure mode/limit.** Four families are finite and do not establish arbitrary connected-shape generalization. Expanding this library is the clearest next distribution improvement, provided exact construction remains total.

## D4 — Make teaching support a deterministic four-position schedule

**Choice.** Schedule `canonical_small → diff_query → clip → canonical_large` by `sample_index mod 4`. Every four consecutive samples contains all profiles.

**Original rationale.** Per-draw witness frequency does not imply that the runner’s actual four-demo lesson contains a witness. The canonical pairs admit both declared shortcuts.

**Alternatives considered.** IID texture sampling has a nonzero chance of witness-free lessons. Seed-only scheduling can alias with runner seed/index policy. Forcing every individual board to contain both witness properties would collapse useful profile diversity.

**Probe and result.** Tests check every four-sample window over multiple starts. The source-bound probe emulates sequential sample indices, duplicate rejection, 100 production seeds per band, and all four cyclic starts; no declared rival survives any demo set.

**Failure mode/limit.** A future runner that changes demo count or sample-index progression must rerun the source-bound probe. The report records the sampler policy and hashes for this reason.

## D5 — Recur exact canonical-scale anchors

**Choice.** Schedule exact 3×11/palette-4 and 4×14/palette-4 boards, while allowing wider/taller boards in difficulty-aware non-anchor positions.

**Original rationale.** The imported distribution had zero measured strict canonical profile support and failed the profile-floor requirement.

**Alternatives considered.** Relying on random chance cannot guarantee a hit in each band’s 20-draw floor. Generating only canonical dimensions would reduce useful scale diversity.

**Probe and result.** The strict profile and profile-floor gates pass in every band; task tests explicitly require both exact signatures.

**Failure mode/limit.** Scheduled anchors produce some repeated dimensions and contribute to the measured 8 duplicate occurrences among 500 production pairs per band, although inputs remain 492/500 unique.

## D6 — Keep colors simple and semantically separated

**Choice.** Sample two distinct colors without replacement from `1..7,9`; reserve `0` for background and `8` for separators. BEFORE and AFTER share one color; QUERY uses the other.

**Original rationale.** This makes color transfer observable while avoiding separator ambiguity.

**Alternatives considered.** Same-color QUERY would hide recoloring. Multi-color objects would require a rule decision not present in the canonical authority. Allowing 8 in a panel would break arithmetic separator semantics.

**Probe and result.** The analyzer enforces the exact four-color palette `{0,8,demo,query}` and all canonical/generated boards pass.

**Failure mode/limit.** Multi-color object transfer is intentionally outside this generator’s domain.

## D7 — Centralize structural truth in `_analyze`

**Choice.** Derive validation, texture classification, override observation, strict-profile checks, and the rule mirror from one normalized structural analysis.

**Original rationale.** The imported `self_check` only checked coarse dimensions/non-emptiness, so malformed boards and semantic drift could be accepted while metadata claimed success.

**Alternatives considered.** Separate ad-hoc checks are shorter initially but drift independently. Trusting generation alone leaves mutations and future edits unguarded.

**Probe and result.** Destructive mutation tests cover blank boards, separator corruption, palette pollution, missing query, disconnected AFTER, removed growth, ragged rows, and boolean cells. The final self-check mutation audit is green.

**Failure mode/limit.** Shared analysis reduces drift but can create correlated implementation errors, so `workspace/reference_probe.py` remains deliberately independent.

## D8 — Declare only concrete canonical-fitting rivals

**Choice.** Retain `copy_after_shape` and `reject_partial_clip` as `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`, with linked `different_query_shape` and `partial_clip` witnesses.

**Original rationale.** Both rivals fit all three usable canonical pairs, making them plausible shortcut labels for a learner.

**Alternatives considered.** Generic geometric rivals do not fit the canonical data and add little task-specific value. An unbounded list of speculative rivals would make the gate noisy and easy to game.

**Probe and result.** The live semantic gate checked 60 fired examples per witness: every claim held, with zero oracle/rival errors. All 12 sampled lessons were identifiable. The larger census reports zero survivors.

**Failure mode/limit.** Passing this finite rival set is not universal rule identification. New plausible canonical-fitting shortcuts should be added as executable competitors, not prose claims.

## D9 — Bind long-run evidence to final sources and the actual runner

**Choice.** Build `lesson_probe.py` with generator, oracle, probe, canonical-ledger, and rule hashes; emulate runner retries, duplicate rejection, sequential indices, and cyclic starts.

**Original rationale.** Counts detached from source bytes or from the real lesson-assembly policy are not reusable evidence.

**Alternatives considered.** A simple per-input witness histogram is cheaper but cannot answer whether complete lessons refute a rival. Copying rival names into the tool would silently diverge from generator declarations.

**Probe and result.** `lesson_census_100.json` reads the generator’s actual declarations and reports exact denominators, unique inputs, profile sequences, rejection reasons, canonical fit, and survivor counts.

**Failure mode/limit.** The probe is finite and CPU-only; it does not measure Qwen loss, confidence, or generalization.

## D10 — Keep the fresh solve honest and separate

**Choice.** Prepare the solve after final generator bytes, declare earlier exposure, consult no reference during solving, preserve the real failed first revision, and stop after all visible pairs passed.

**Original rationale.** A visible-example solve tests whether the generated lesson is operationally understandable without converting masked answers into reviewer leakage.

**Alternatives considered.** Reopening the rule would invalidate the solve. Manufacturing a bad attempt would create false training evidence. Iterating against masked labels is intentionally unavailable.

**Probe and result.** Revision 1 exposed a coordinate-frame bug at 3/4 visible pairs; revision 2 passed 4/4. Masked correctness remains unknown.

**Failure mode/limit.** Because earlier rule exposure is yes, this is not claimed as a blind human solve or independent model-generalization measurement.
