# Working notes: 994f16f93144

## Review result

The selected v3.0.0 generator labeled its targets as isolated three-cell diagonal objects. That was narrower than the canonical local predicate. The executable rival `isolated_exact_triples_only` matched all three usable canonical pairs and all 600 sampled v3.0.0 scenes, but disagreed on a same-color four-cell diagonal chain: the authority recolors both interior cells, while the rival recolors neither.

Version 3.2.0 makes longer chains lawful and places one in each generalized profile. A strict canonical anchor remains at `sample_index % 4 == 0`; generalized profiles occupy the other three residues. `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `WITNESS_RIVALS`, and the `overlapping_diagonal_targets` witness make the ambiguity executable rather than documentary.

## Construction choices

- Overlap is lawful only for same-color, same-slope local windows. Crossing slopes or conflicting colors remain validator errors.
- A four-cell chain represents two overlapping target centers while consuming one placement motif. `n_triples` continues to report the number of local windows, not the number of connected objects.
- Ordinary no-override sampling retains a 25% strict canonical-profile prior. The other 75% is intended to refute the exact-object shortcut and also carries the prior mismatched-diagonal, reused-color, slope, border, and position evidence.
- The three generalized profile sizes are intentionally different within each difficulty band. Any three-of-four query rotation therefore leaves at least two canvas sizes among the demonstrations.
- Explicit motif-count or interior-placement requests receive spacious 12×12 companion defaults unless the caller explicitly supplies dimensions. This fixes the v3.0.0 single-axis override failures without weakening explicit joint requests.
- Four geometric combination classes are declared incompatible: `mixed` with one target; 7×7; height 7 with five targets; width 7 with five targets. The strict override sweep verifies those declarations rather than treating arbitrary `ValueError` as acceptable.

## Verification snapshot

Final generator SHA-256: `1104b68e1b5941f2fd8686cbb0a279253a1e900d9ee2a5518b4d624481a7f41b`.

- Before battery: 11/12 green; override failed on medium seeds 10 and 13 for explicit `n_triples=3`.
- Final battery: 12/12 green.
- Selected task tests: 26/26 passed.
- Override sweep: 29,430 draws; 29,310 accepted; 120 declared incompatibility rejections; zero findings or warnings.
- Semantic gate: 600/600 draws completed, strict canonical-like 153/600 (25.5%), all nine witnesses fired in every band, rival claim 60/60 verified, and 12/12 sampled lessons identifiable.
- Source-bound census: 300/300 lessons, 1,200 query rotations, zero ambiguity, zero hook warnings, zero scoring/materialization errors, 1,195 unique inputs.
- Final visible-only solve: one hypothesis, 3/3 demonstrations passed; private query labels remain withheld by policy.

The canonical Racket authority and `RULE_HASH = 606a0be0f9ee` were not changed. Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `1104b68e1b5941f2fd8686cbb0a279253a1e900d9ee2a5518b4d624481a7f41b`.

# Decisions — 994f16f93144

## D1 — Keep the canonical Racket authority unchanged

**Original rationale:** The selected source already pinned normalized canonical hash `606a0be0f9ee`, and the before rule-smoke and authority-sync stages passed. The archival base record differs textually, but execution parity is reported.

**Decision:** Change only generator-side curriculum, validation, tests, and notes. Do not rewrite the Racket rule or canonical ledger.

**Alternatives considered:** Rewrite the authority to speak explicitly about sliding windows; normalize the archival source; encode longer-chain behavior in a new rule branch.

**Probe:** All three usable canonical pairs match `rule_mirror`; the final battery's Racket smoke, lint, and authority-sync stages are green. `solve/summary.json` and the final census bind to rule hash `606a0be0f9ee`.

**Failure modes / limits:** The Python mirror is only a test aid. Behavior claims still depend on the real Racket smoke/census evidence. The retained archival divergence remains outside this task-local repair.

## D2 — Interpret targets as local windows, not isolated objects

**Original rationale:** v3.0.0 described “isolated contiguous three-cell” targets and rejected all target overlap. No rationale was recorded for narrowing the canonical predicate.

**Decision:** Permit overlap only between same-color, same-slope target windows. A four-cell chain therefore contains two lawful target centers. Keep crossings and color-conflicting overlaps invalid.

**Alternatives considered:** Leave validator isolation unchanged and add a special negative fixture; permit arbitrary target overlap; use a five-cell chain; treat overlapping centers as one target for axis accounting.

**Probe:** The new four-cell regression failed on v3.0.0, then passed with expected cyan cells at both interior positions. Crossing-target mutation tests continue to fail validation. Real Racket smoke and the final solve agree with the local-window interpretation.

**Failure modes / limits:** The generator deliberately uses only collinear overlaps. It does not attempt to sample every lawful superposition. `n_triples` counts local windows, which differs from connected-component count and must remain documented.

## D3 — Retain a 25% canonical anchor and use 75% explicit rival counterexamples

**Original rationale:** v3.0.0 used `sample_index % 4 == 0` as a strict canonical-profile prior. Preserving this protects exact shapes/palettes and isolated examples.

**Decision:** Keep residue 0 unchanged. In residues 1–3, replace one isolated target object with a four-cell chain while preserving the requested number of local windows.

**Alternatives considered:** Make every scene a long chain; add long chains only rarely; replace canonical anchors; add a separate diagnostic-only texture that the production sampler never uses.

**Probe:** `workspace/probe_shortcut.py` measures exactly 50/200 strict anchors and 150/200 long-chain rival disagreements per band under its deterministic schedule. The semantic gate's independent pinned sampler measures 153/600 strict and 447/600 overlap witnesses. Profile-floor reports exact canonical support in every band.

**Failure modes / limits:** The four-residue schedule assumes production lesson assembly draws enough distinct sample indices. The source-bound census exercises the actual sampler and all query rotations, but not every imaginable external reshuffling policy.

## D4 — Make the strongest shortcut executable

**Original rationale:** The baseline semantic hooks covered slopes, borders, distractors, and color reuse but declared no rival corresponding to the object-vs-local ambiguity. The old gate therefore passed despite the defect.

**Decision:** Add `_isolated_exact_triples_only` and expose it through `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`. Bind `overlapping_diagonal_targets` to it in `WITNESS_RIVALS`; require a longer chain in `lesson_identifiable`.

**Alternatives considered:** Mention the rival only in prose; add only a witness predicate; copy separate implementations into each declaration; rely solely on the final human solve.

**Probe:** The rival fits 3/3 canonical pairs. On final production samples it disagrees 150/200 per band in the focused probe, its witness claim holds 60/60 in the semantic gate, and it is refuted in all 300 census lessons and all 1,200 query rotations.

**Failure modes / limits:** A finite declared-rival list is not universal identifiability. The same callable appears under three contract aliases in census evidence; this is intentionally explicit but motivates feedback F3.

## D5 — Repair single-axis overrides with companion defaults

**Original rationale:** Unknown. v3.0.0 selected a generalized profile for any override but left unrequested dimensions and motif counts at the ordinary profile values.

**Decision:** Treat explicit count/position axes as requests for a constructible scene. Pair them with 12×12 conservative dimensions unless dimensions are also explicit; pair a single explicit dimension with a spacious other dimension; reduce only unrequested counts for small dimensions.

**Alternatives considered:** Add exhaustive joint backtracking without changing defaults; silently decrement an explicit target count; mark all seed-specific placement failures incompatible; remove exact controls.

**Probe:** The initial hypothesis blamed greedy target placement. A zero-distractor reproduction disproved it: the 8×8 scene could not fit the requested separated target set at all. Tests for the exact seeds 10 and 13 then drove the companion-default fix. Final strict override sweep: 327 cases, three bands, 30 seeds, 29,430 draws, zero findings.

**Failure modes / limits:** Explicit multi-axis requests are never silently relaxed. Some small/high-count combinations remain impossible and are declared. Conservative 12×12 companions change the distribution of override calls, not ordinary no-override sampling.

## D6 — Declare only geometric incompatibilities

**Original rationale:** v3.0.0 had no strict incompatibility matrix, so the checker could not distinguish intended rejection from arbitrary generation failure.

**Decision:** Declare four broad geometric classes: `mixed` with one target; 7×7; height 7 with five targets; width 7 with five targets.

**Alternatives considered:** Declare the two failing seeds; enumerate every impossible full tuple; catch all `ValueError` as intentional; enlarge the public dimension minimum.

**Probe:** The final override report records 120 explicit rejections, all covered by declarations, with zero undeclared errors or warnings. Unknown-key rejection remains active.

**Failure modes / limits:** The declarations intentionally overapproximate within their small geometric class (for example, all 7×7 combinations), trading a little legal support for a simple falsifiable contract. Future layout improvements may justify narrowing them.

## D7 — Vary profile dimensions across every query rotation

**Original rationale:** v3.0.0 varied dimensions across broad random draws, but no lesson-level guarantee existed. The first repair left some four-pair bundles all 9×9.

**Decision:** Assign distinct dimension ranges to generalized profiles in each difficulty band so any three demonstrations from a four-pair bundle contain at least two sizes.

**Alternatives considered:** Remove the size-variation requirement; suppress the lesson hook; randomize dimensions and resample until varied; increase `EXAMPLES_NEEDED`.

**Probe:** `checks/tdd-red-size/` captures the exact failing easy lesson at seed `1_175_019_826`; `checks/tdd-green-size/` passes the every-rotation regression. The v3.1 census had 15 hook warnings; the final 1,200-rotation census has zero.

**Failure modes / limits:** Dimensions are now more correlated with profile residue. Colors, locations, slopes, motif counts, and layouts remain stochastic; the finite census found 1,195 unique inputs among 1,200 pairs.

## D8 — Keep a reusable source-bound rival probe

**Original rationale:** No focused reproducer existed for the exact-object shortcut.

**Decision:** Add `workspace/probe_shortcut.py`. It discovers the current declared rival, checks canonical fit, samples 200 inputs per band, and prints the exact disagreement matrices.

**Alternatives considered:** Store only a static JSON witness; embed the probe solely in pytest; rely on the multi-megabyte census.

**Probe:** `checks/shortcut-probe.log` is the final run. The script is also source-bound in the runtime manifest and can be rerun with `run_with_racket.py`.

**Failure modes / limits:** It uses `rule_mirror` for high-volume comparison; the real authority is independently checked by the Racket stages and lesson census. Its fixed seeds are a reproducible sample, not exhaustive support.

## D9 — Preserve failed iterations and distinguish final evidence

**Original rationale:** The return contract asks for genuine failed evidence rather than a cleaned narrative.

**Decision:** Retain TDD red/green runs, the v3.1 all-green battery, the warning-bearing v3.1 census, the old solve, and the interrupted standalone wrapper. Use only final v3.2 runs for acceptance claims.

**Alternatives considered:** Delete intermediate evidence to reduce size; treat the interrupted wrapper's staged completion as the final override pass; overwrite the first solve.

**Probe:** Final battery, task tests, census, solve, and fresh replay all carry the same generator SHA `1104b68e…7f41b`. `checks/patch-replay.json` confirms the solve hash matches replayed bytes.

**Failure modes / limits:** The retained checks directory is large and is automatically evidence-bundled by the packager. Intermediate source hashes are intentionally different and must not be mistaken for final evidence.
