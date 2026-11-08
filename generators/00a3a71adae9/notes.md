# Working notes: 00a3a71adae9

## Review 2026-10-06 — assignment `review-7da879f2c942db2f`

Baseline generator SHA-256: `4908e0386fbd416f559ab65f59af39758fd0b8f9d8ebb7e44d25088ca6c6b696` (version 1.2.1).
Final generator SHA-256: `81c6903b1c51bdd1c173400770cf4f16bf7be49f963b877737085f6790707d62` (version 2.0.0).
Canonical authority hash: `cdd6424b9ac7`; the Racket rule was not changed.

### Confirmed baseline defects

- The battery was 7 green, 2 advisory, and 3 failed. Lint, strict defect lint, and the override contract failed.
- Fixed-seed probes showed that all advertised `motif_size`, `mask_cells`, and `mask_noise` values collapsed to identical inputs. The ordinary sampler overwhelmingly taught a unique positive-overlap winner and did not deliberately exercise the authority's distance or final reading-order comparators.
- The generator had no pinned `RULE_HASH`, no executable rival/witness contract, accepted unknown override keys, and mixed ordinary textures with destructive negative fixtures.

### Repair

- Replaced the nominal texture/noise system with three lawful semantic profiles: overlap beats proximity, proximity breaks an overlap tie, and top-left order breaks a score-and-distance tie.
- Made all six public axes exact and observable: `grid_h`, `grid_w`, `n`, `motif_size`, `mask_cells`, and `texture`. Unknown, mistyped, or out-of-range controls are rejected.
- Enumerated every fixed connected polyomino of size 1–10 that fits a 3×4 slot. The default size draw is weighted toward larger motifs to avoid repetitive tiny outputs while explicit size overrides remain exact.
- Added strict canonical validation, independent semantic rivals, named witnesses, canonical-shortcut declarations, and a lesson-level identifiability hook. Five demonstrations plus one query cover the three-profile cycle twice and survive every held-out query rotation.
- Added task-local tests and `workspace/reference_probe.py`, an independent Python oracle plus a real-Racket parity helper with no silent fallback.

### Final evidence

- Complete battery: 12/12 green.
- Task-local tests: 84 passed, including real Racket parity.
- Override matrix: 26,190/26,190 accepted draws across 291 cases, zero findings/warnings; unknown key rejected.
- Semantic gate: 600/600 strict, all three canonical inputs accepted, all three witnesses firing, 12/12 lessons identifiable, and 0/72 ambiguous smoke-test rotations.
- Larger census: 300/300 lessons, 1,800 labelled pairs and 1,800 unique inputs; zero production ambiguities and zero ambiguities across 1,800 held-out-query rotations against the declared rivals.

Finite rival tests are evidence against the declared shortcuts, not a proof that no other induction exists. The deterministic profile schedule is intentional and should remain coupled to the five-demonstration lesson policy.
## Current reviewer considerations

Source SHA-256: `81c6903b1c51bdd1c173400770cf4f16bf7be49f963b877737085f6790707d62`.

# Decisions for `00a3a71adae9`

Final generator SHA-256: `81c6903b1c51bdd1c173400770cf4f16bf7be49f963b877737085f6790707d62`.

## D1 — Keep the selected Racket authority unchanged

**Original rationale:** unknown; the packet pins the selected canonical rule at hash `cdd6424b9ac7`.

**Decision:** change the generator only and add `RULE_HASH = "cdd6424b9ac7"`.

**Probe:** the baseline rule smoke and authority synchronization already passed; independent Python-oracle parity and the final rule smoke still pass all canonical and generated checks.

**Rejected alternative:** rewrite the Racket rule to fit the old generator's simpler overlap behavior. That would destroy the authority's distance and reading-order semantics rather than repair the curriculum.

**Failure mode/limit:** the authority contains semantics that are underdetermined by some canonical pairs. The generator must continue supplying counterexamples; the pin alone does not guarantee teaching quality.

## D2 — Replace nominal textures with three semantic profiles

**Decision:** ordinary samples use exactly one of `overlap_priority`, `distance_priority`, and `scan_tiebreak`. They all obey the same authority but isolate successive comparator levels.

**Why:** a random layout can be label-correct while almost never distinguishing the intended ranking from a shorter rule. Named profiles make coverage executable and diagnosable.

**Probes:** each profile has a task-local witness and rival; the semantic gate observed 203 overlap, 208 distance, and 189 scan witnesses in 600 samples. All three rivals were checked on 60 witness draws each.

**Rejected alternatives:**

- Keep `mask_noise`: it was behaviorally inert and added no semantic contrast.
- Pure random resampling until a useful case happens: this obscures coverage and makes lesson assembly fragile.
- Keep destructive `no_mask`/`no_motifs` textures in the ordinary domain: these are diagnostic negatives, not lawful training examples.

**Limit:** deterministic profiles simplify auditability but make profile order predictable. The morphology, dimensions, counts, and placements still vary independently.

## D3 — Use five demonstrations plus one query

**Decision:** `EXAMPLES_NEEDED = 5`; a six-pair schedule repeats each of the three profiles twice.

**Why:** every held-out position still leaves at least one demonstration of every comparator level. With only three total pairs, holding out one profile would remove its only witness.

**Probes:** task-local tests exhaust all six query positions for each difficulty band. The source-bound census held out every materialized pair once: 1,800/1,800 rotations were identifiable against all declared rivals.

**Rejected alternative:** rely only on ordered production queries. That would pass an easier policy but leave rotated or shuffled downstream assembly unsafe.

**Limit:** the check covers the actual six-pair bundles and declared rivals; it does not enumerate every possible resampled lesson or unknown model hypothesis.

## D4 — Make every public control exact and observable

**Decision:** expose only six real axes: `grid_h`, `grid_w`, `n`, `motif_size`, `mask_cells`, and `texture`. Validate unknown keys, exact types (including rejecting bool-as-int), ranges, and profile names before drawing.

**Why:** the baseline advertised controls that did not alter pixels, which makes sweeps and data balancing untrustworthy.

**Probe:** the final override matrix exercised 291 cases and 26,190 draws over all difficulty bands; every draw was accepted, every observation matched, no warnings/findings remained, and the unknown-key probe was rejected.

**Rejected alternative:** retain placeholder axes with singleton or undocumented semantics. Metadata should describe a controllable factor, not an aspiration.

**Limit:** difficulty changes the profile offset and keyed randomness, not a monotone cognitive scale. No stronger difficulty claim is made.

## D5 — Enumerate connected 1–10-cell motifs in a 3×4 slot

**Decision:** construct a deterministic bank of all fixed connected polyominoes of sizes 1–10 fitting a 3×4 box; weight ordinary size draws toward larger motifs while honoring explicit size overrides exactly.

**Why:** an early profile-correct implementation using a small hand bank produced only 41 distinct outputs in 150 draws. Richer shapes raised independent 150-draw output counts to 121–125 per band/configuration before the final battery; the battery itself reports 70% unique outputs over 300 labelled pairs.

**Rejected alternatives:**

- Arbitrarily rotate/reflect a tiny bank: still too repetitive and easy to memorize.
- Unbounded random walks: harder to make deterministic, exact-size, and slot-safe.
- Allow motifs larger than 10 cells: unnecessary for canonical support and tighter placement guarantees.

**Limit:** motifs fit a 3×4 slot and placements use separated teaching regions. This is intentionally not the full space of lawful component geometry.

## D6 — Keep mask count exact and construct it from occupied extremes

**Decision:** place exactly 3–6 color-1 cells in a profile-specific arrangement. For scan ties, anchor mask construction to actual occupied extreme cells, not bounding-box corners.

**Why:** irregular polyominoes may not occupy their bounding-box corner. A first scan-tie construction used a fixed box column and sometimes produced unequal distances; a failing test exposed this before the production change.

**Probe:** all profile witnesses fire across all bands, and exact mask counts pass the complete override matrix.

**Failure mode/limit:** profile constructors deliberately favor clean, readable counterexamples over arbitrary mask topology.

## D7 — Add an independent oracle and real-authority parity

**Decision:** keep `workspace/reference_probe.py` independent of production helpers and make Racket unavailability an explicit error in parity checks.

**Why:** tests that call the production selector to compute their expected answer can reproduce the same bug. Silent Python fallback would falsely claim Racket parity.

**Probe:** 84 task-local tests pass in the packet's Racket runtime; canonical and generated outputs match the independent oracle.

## Prior evidence used

I used the packet's pinned baseline, canonical record, selected bank record, task notes, and the battery generated in this review. No prior external return was used as a source of truth. The archived baseline under `workspace/generator-v1.2.1.py` is byte-identical to the assignment SHA.
