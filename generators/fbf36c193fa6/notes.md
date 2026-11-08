# Working notes: fbf36c193fa6

## Review review-d3fc762ad44cb0b2 — 2026-10-02

R1: the v4.0 fixed NE corner-pinch template admitted the plausible canonical-fitting rule “only upward red rays stop at corner pairs.” It matched all four public canonical pairs and all 1,200 baseline sampled inputs. V4.1 uses open/mixed/mixed scenes with opposite rotations in the two mixed slots, changes blocker depths, and declares the actual canonical-fitting rival. Each tested three-demo window refutes all six declared lesson rivals.

R2: active selected `target_code` differed from canonical only in whitespace; synced that one JSON value exactly. Canonical ledger and archival `raw_code` unchanged. Normalized rule hash remains `df658022eba5`.

R3: an intermediate semantic gate correctly rejected the unlinked `red_open_to_edge` witness. Added “omit all red rays” and a regression requiring actual linked rival disagreement for every witness. The selected runtime tests pass 19/19; full repository tests pass 178/178; final battery has 12/12 green stages.

Evidence belongs to return ZIP `review_response_review-d3fc762ad44cb0b2.zip`, under `checks/after/`, `checks/probe-final/`, and `checks/source-binding.json`. Final generator SHA-256: `b04b2ff18150208d0dabbe05a259dcdfd1aa4776df651aa44d8a671d2e68c334`. Census: 100 disjoint four-grid lessons in each of easy/medium/hard (three demos and one query), 1,200 unique inputs and live Racket parity for all; zero surviving lesson rivals. Exact seed recipe and cyclic starts are in each probe summary.

Reusable tooling: `workspace/stage_review.py` stages all new task-local tests, `workspace/coverage_probe.py` measures actual declared rivals against live Racket, and `workspace/audit_probe.py` reproduces the two assigned findings-only audits. Read workspace/README.md for commands.

Limits: constructive mixed scenes retain correlated blocker roles; the evidence does not exhaust all plausible shortcuts or establish learner performance. Complete-lesson coverage assumes same-seed consecutive sample indices with ordinary profiles. Audited generators were not modified. The final-source solve is reviewer-authored with earlier rule exposure, passed 3/3 visible demos, and has unknown masked correctness; training admission remains false.

Imported associated notes retain their original evidence/timestamps in `evidence/associated_notes.jsonl`; they are historical, not fresh evidence for v4.1.
## Current reviewer considerations

Source SHA-256: `b04b2ff18150208d0dabbe05a259dcdfd1aa4776df651aa44d8a671d2e68c334`.

# Decisions: fbf36c193fa6

## R1 — repair the actual canonical ambiguity, not just witness frequency

**Observation.** The old generator had many named barrier features but always assigned pinch stopping to the same upward corner at depth three. “Corner pairs stop only upward rays” fits all four public canonical pairs and every one of 1,200 baseline samples. Merely increasing sample count cannot reveal a branch outside sampler support.

**Choice.** Retain the narrow input grammar and correct output rule; rotate the five blocker roles, vary legal stopping distance, and make both an upward and a downward pinch available in each three-demo lesson. This targets a reproduced error mode without changing puzzle semantics or expanding to unrelated shapes/colors.

The cycle is open/mixed/mixed. Mixed slots 1 and 2 are opposite in orientation. Seed parity chooses one of two complementary pairs of rotations, covering all four corners across seeds. Red direct and pinch depths and yellow intermediate/next-diagonal depths are drawn from their legal path indices using a named RNG stream. Yellow-start blocking necessarily has depth zero; it is not counted as distance variation. Six deliberate blockers are reserved first and remaining gray distractors are outside all ray-sensitive cells, preserving exactly requested gray counts and avoiding accidental branch destruction.

**Why not independent random rotations?** That would produce the missing direction eventually but could still leave many short lessons ambiguous. The deterministic three-slot schedule provides a checkable same-seed consecutive-example coverage property. Opposite slots preserve all cyclic-start cases. **Why not global grid rotation?** Clockwise staircase orientation and rectangular shape profiles need care; rotating only blocker roles preserves the declared grammar and dimensions directly. **Why not a hand-picked downward witness only?** A witness outside ordinary sampling would diagnose the bug without repairing training support.

**Accepted limitation.** The roles in a mixed scene remain correlated; the two mixed rotations are not independent within one seed. The tested rival set is finite. These are defensible next investigations, not claims of complete task identifiability. The generator's `lesson_identifiable` hook is rival-relative, not a uniqueness proof over all programs. Arbitrary shuffling/reseeding can discard the schedule benefit. Forced profiles must preserve explicit caller overrides even when this yields an ambiguous lesson; the hook reports that ambiguity rather than silently replacing the requested profile.

## R1/R3 — distinguish fitting shortcuts, controls and meaningful witnesses

All declarations are evaluated against every usable public canonical pair. Only the verified upward-only alternative is now labeled in `CANONICAL_SHORTCUTS`. Other rivals stay in `LESSON_COMPETITORS` as useful controls, with their non-fitting canonical counts visible in the reports. The lesson hook iterates the live declaration instead of a copied literal list. The coverage probe likewise reads actual mappings, so future additions cannot be silently omitted.

The first after gate correctly flagged `red_open_to_edge`: a feature firing alone did not establish any named wrong answer. Added the minimal “omit all red rays” rival and a regression requiring each witness's linked rival to disagree when it fires. Rejected suppressing the warning or pretending a feature frequency was a semantic pass. Kept both the failing gate and the new regression failure. The old branch fixture needed a third scene after the explicit downward requirement was added; the fixture was expanded, not weakened.

## R2 — exact active authority synchronization without a semantic rewrite

The initial selected base target and canonical program were byte-different but whitespace-normalized identical. Replaced only `racket_target.target_code` with the existing canonical string. All other parsed JSON fields, including archival executable `raw_code`, are unchanged. Canonical file bytes and rule pin remain unchanged. Rejected editing the canonical authority to match incidental formatting, deleting archival provenance, changing the transformation or weakening the exact synchronization gate. Existing and final live authority execution-parity checks support the no-semantic-change claim. `checks/source-binding.json` gives the field comparison and before/after hashes.

## T1 — keep new local tests runnable without editing shared infrastructure

Normal staging uses a frozen map and did not include the newly added task test. The task-local `stage_review.py` composes the existing staging API and then copies every selected-task `test_*.py` plus the coverage probe, hashing extra files. Rejected changing shared runtime/catalog infrastructure outside scope. The runtime is explicitly named in RESULTS.json, and its generated files are not part of the source patch. The helper does not alter an unrelated task or overwrite old evidence. The full repository suite and the selected-runtime suite were both run.

## Measurement and historical evidence

Census source hashes are explicit: before `151522ecd70e95af65b47847ed4b7cc8e64f51e0ead3f289b1501869e3570f3e`, intermediate `905b6b49230cc4569d1f3780d14cf3d2c4ed6b59eb287686c4657adabbf94c6f`, final `b04b2ff18150208d0dabbe05a259dcdfd1aa4776df651aa44d8a671d2e68c334`. Both before and final use exactly the same deterministic 100-lesson-per-band recipe, no rejection filtering and 1,200 unique grids each. Every output uses live Racket, not solely a mirror. Comparing all sample residues prevents a lucky schedule offset from masquerading as reliable lesson coverage. The independent red-rival helper preserves the ordinary yellow behavior; live Racket and stored public outputs independently validate the intended answers. This is not a second independent implementation of the entire puzzle rule.

Failure logs, exact counterexamples and the intermediate source are retained. The before/intermediate sources are not promoted as current. The 432 override boundary cases are distinct from the random Racket census; neither is described as exhaustive over all seeds. No runtime timing is presented as a performance benchmark and no model score improvement is inferred from these checks.

## A1/A2 and the solve boundary

Audits are diagnoses only. A1 is an exact-override failure, so its counterexample deliberately has no invented “rival output.” A2 is a true output-rule alternative with exact Racket/rival outputs; its hand-built right-edge scene passes validation but lies outside ordinary sampler support. A2's count is 90 draws / 87 unique inputs, not 90 unique inputs. Neither audit target was edited. The validator/canonical differences in A1 are recorded as a separate domain question, not silently repaired.

The solve started only after the final generator hash was fixed. Its visible-only boundary was respected, and prior exposure was disclosed. One genuine ordinary solution revision sufficed on visible examples; no accidental failure narrative was fabricated. Completion means the assigned repair, checks, audits, question and solve record are delivered, not that the masked outputs are correct or that maintainers have approved training use.

## Parametric prototype review — 2026-10-24

Added a task-local native parametric prototype under `workspace/parametric/` with one bounded semantic control: `yellow_turn` is either `clockwise` (the exact canonical default program) or `counterclockwise` (the adjacent turn direction only). Red rays, obstacle semantics, colors, and the 3x3 cyan source remain unchanged. The adapter supports 2..6 demonstrations and 1..4 stable-prefix queries from setting-independent inputs. Every retained example distinguishes the two settings; the fourth query is a substantive 30x30 stress scene with gray boundary decoys and long rays in every quadrant.

The evidence exporter writes public challenges whose query outputs and rule/settings are private. A packet-level export audit first rejected pretty-printed bytes with truncated IDs and then the nonconforming `arc-` prefix; the final files are exact `public_challenge_bytes` named `challenge-<full-sha256>.json`, and the official helper passes all ten retained public episodes across the three assigned tasks. It materialized two complete episodes, each with three demonstrations and four queries. All 14 labels were executed through the bundled protected Racket bridge and matched the independent Python mirror; demo-only finite-rival teaching selected exactly the intended turn. The native qualification receipt is `checks/parametric/fbf36c193fa6-qualification/qualification.json` and reports `qualified` for both settings at seeds 0 and 17. The source-bound manifest hash is `0a5b9e9ed63b6e6035865435bb1c56277157bf37e1706f86ac4e0eb465340eb6`.

Two task-test portability defects were also repaired without changing generator semantics: canonical/base data now resolve from the selected library root via `reviewer_support`, and the task no longer depends on an unstaged `scripts` package. The staged native task-test route passes 26/26; the focused prototype suite passes 7/7. This is proposed task-local evidence only. Production generator behavior, approval state, and training admission remain unchanged; `parametric status` is `not_accepted` and `training_admitted` is false.
