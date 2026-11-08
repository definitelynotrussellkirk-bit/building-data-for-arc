# Current review notes: bca4f37ec5e9

## Intended rule and authority

The input contains one contiguous block of nonzero rows in a zero background. Repeat that row block vertically over the full grid while preserving its source-row phase: output row `r` copies source row `first_nonzero + ((r - first_nonzero) mod period)`. Horizontal content and colors are unchanged.

Selected generator version: `2.1.0`. Final reviewed generator SHA-256: `80add324b59500cbb90e762c2cfd6b9ad26d54325a4982f2d07684f5ef555c21`. Canonical rule hash remains `868f6b6ec7f1`; the Racket law was not changed.

The selected `target_code` fields in both base solution records are now exact canonical text, matching their declared `selected_exact_canonical` status. Their shorter archival `raw_code` fields remain preserved and intentionally divergent.

## Repaired teaching defect

The accepted prior audit `review-d13bc7df567eab52:v0001` was used as the lead. On generator SHA `3567cc82...`, it found 11 harmful three-demo lessons out of 1,200 cyclic windows where an absolute-grid-row-0 phase rival fit every demonstration but disagreed on the query. The smallest retained example was easy seed `100083`, cyclic start `1`.

Prior choice: only lesson slot 0 was guaranteed to distinguish source-row anchoring from grid-row-0 anchoring. New choice: slots 0 and 2 are guaranteed phase witnesses. Slot 2 now chooses only `period4_top`, `period5_center`, or `period5_bottom`, all of which have `first_row % period != 0`. Therefore every cyclic window of three consecutive samples contains slot 0 or slot 2 and rejects the grid-top rival.

The repair does not remove `period4_bottom` from the generator. It remains available in the unrestricted slot and through explicit profile overrides; only the scheduled teaching slot was narrowed.

## Verification and limits

- Focused regression: all `3 bands × 4 cyclic starts × 100 seeds = 1,200` three-demonstration windows reject the grid-top phase rival.
- Selected task tests: 14/14 checks passed (`9 passed, 5 subtests passed`).
- Final battery: all 12/12 stages green.
- Larger source-bound census: 300 lessons, 1,200 pairs, 1,200 rotations, 883 unique inputs, no materialization/scoring errors. Its verdict is `no_contract`, not an identifiability pass, because no lesson rival hook is declared.
- The proof is finite over the current ten linked profiles, four cyclic starts, and tested source-row-vs-grid-top rival. It does not establish uniqueness against every possible induction rule.
- The standalone authority parity option failed before execution with `ModuleNotFoundError: scripts`; the supported battery authority stage passed execution parity. This is recorded as a shared-tool issue, not a generator defect.
## Current reviewer considerations

Source SHA-256: `80add324b59500cbb90e762c2cfd6b9ad26d54325a4982f2d07684f5ef555c21`.

# Decisions for bca4f37ec5e9

## D1 — Treat the inherited audit as a lead, then reproduce its mechanism

The lead was accepted audit `review-d13bc7df567eab52:v0001`, bound to generator SHA `3567cc82...`. It reported 11/1,200 harmful cyclic lessons for a grid-row-0 anchor rival and retained easy seed `100083`, start `1` as the minimal example. I did not treat the prior count as proof about the pinned source; I encoded the rival in a new final-source regression and first observed the same failing tuple `(easy, 100083, 1)`.

Rejected alternative: dismiss the finding because ordinary generator/rule checks were green. Those checks establish lawful labels, not whether a complete lesson distinguishes phase conventions.

## D2 — Repair the teaching schedule, not the semantic rule

The canonical law is correct and already solves all canonical pairs. The defect was demonstration selection. I preserved rule hash `868f6b6ec7f1` and changed only slot-2 profile choices so every option has `first_row % period != 0`.

Rejected alternatives:

- Change the Racket rule: unnecessary and would alter correct authority semantics.
- Add a fourth demonstration: increases training cost and is unnecessary because a three-demo schedule can guarantee the witness.
- Resample until a witness appears: less deterministic, harder to audit, and can hide an unbounded retry path.

Failure mode considered: narrowing slot 2 might erase a useful profile. It does not; `period4_bottom` remains in unrestricted sampling and explicit overrides.

## D3 — Guarantee two witness slots per four-slot cycle

Slot 0 was already a phase witness. Slot 2 now also always witnesses the distinction. Every cyclic three-sample demo window over slots `{0,1,2,3}` includes slot 0 or slot 2, including starts 1 and 3 that defeated the prior single-witness design.

The regression enumerates 3 difficulty bands, all 4 cyclic starts, and 100 seeds per band: 1,200 complete three-demo windows. It asserts that at least one demo in every window differs under the grid-top rival. This is stronger for the repaired defect than random witness-frequency sampling.

Limit: this is a finite guarantee over the current four-slot schedule and current profile table. A future schedule-length or profile-phase change must update the test.

## D4 — Keep exact selected authority and archival source as separate roles

Both selected base records declared `selected_exact_canonical`, but their `target_code` was only semantically/whitespace equivalent. I replaced `target_code` with the exact canonical `program_solution` text in both records and preserved `raw_code` unchanged as archival executable source.

Rejected alternative: weaken the metadata to say normalized-equivalent. Exact synchronization is already the declared contract and gives one selected source group. The final battery reports selected synchronization with archival divergence and execution parity passing.

## D5 — Make focused tests portable rather than repository-depth-dependent

The existing selected test file failed in the packet's isolated runtime because it derived data paths from source depth. I changed it to `find_root(__file__)`, `canonical_path`, and `canonical_pairs`, then reran the same suite. This is a harness repair, not a relaxation: canonical pair count and exact authority assertions remain intact.

## D6 — Do not claim the larger census proves lesson identification

The 300-lesson census successfully materialized 1,200 pairs and 1,200 rotations with no errors, but the generator has no declared lesson contract/rivals. I report its production and rotation verdicts as `no_contract`. The task-local cyclic rival regression is the actual evidence for the repaired ambiguity.

Rejected alternative: interpret `ambiguous: 0` as a pass. With no rivals scored, zero is not evidence of uniqueness.

## D7 — Final self-review for a new shortcut or restriction

I checked that the repair does not make source phase inferable from a fixed period or remove any advertised exact profile. Slot 2 still spans period 4 and period 5 witnesses across positions, while unrestricted slot 3 and overrides retain all ten profiles. The change constrains only the teaching schedule needed to expose anchoring; grid dimensions, palettes, periods 2–5, positions, and exact controls remain covered by the green battery.

## 2026-10-24 parametric phase-anchor prototype

A task-local native adapter now lives under `workspace/parametric/`. Its episode-fixed parameter is `phase_anchor`:

- `source` is the exact canonical Racket program byte-for-byte.
- `grid_top` uses the same input grammar and period detection but starts row zero with the first source row.

The sampler constructively chooses a 2–5-row block with background above and below, varied row masks, and `first_row mod period != 0`, so every generated demonstration directly separates the two settings. It supports 2–6 demonstrations and independent 1–8 queries; the retained examples use three demonstrations and four distinct queries, with the fourth query a content-bearing 30×30 scene.

Bounded self-review attempted the two most relevant break surfaces: minimum/maximum demonstration counts and private/public projection. All demo counts 2–6 uniquely refuted the alternate setting; invalid counts/settings failed before producing an episode. Mutating private settings, Racket source, and query answers left public bytes and IDs unchanged. Protected Racket replayed two retained episodes (one per setting, 14 labels) and the native qualification worker executed four jobs (two fresh seeds × two settings) successfully. The native export command was deliberately not used to publish because the prototype is not owner-accepted; no acceptance or training admission is claimed.
