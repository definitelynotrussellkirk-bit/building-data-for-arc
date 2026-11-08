# Working notes: 9c75b1456763

## Current parametric authoring — review-0299b08133a7021d

- Built the native `workspace/parametric/adapter.py` and finite `promotion.json` for
  `fill_scope = all_interiors | unmarked_rooms`; exact canonical source and
  production generator remain unchanged. Native qualification passed both settings
  on seeds 0 and 17 with three demos and four novel queries (28 labels, 40 Racket
  evaluations). Status is reviewer `ready`; owner exact-source acceptance remains
  pending and no training data is admitted.
- The alternative computes complete-eight-neighbor erosion within each marked
  network, then excludes the four-connected erosion core containing the marker.
  A room core means that connected region, not a drawn rectangle or a radius.
  Notches/corridors can split a rectangle into more than one core; this is defined
  behavior, not a claim that all authored rectangles are excluded intact.
- The new sampler teaches actual network association using woven outer/inner
  paths. Original production stripes admit a nearest-marker-row shortcut; that
  production distribution is unchanged. A long marked core defeats radius-two
  exclusion. Geometry varies independently of the episode setting; inputs include
  18/20/30-square grids, notches, corridors, boundary contact, unmarked distractors
  and all eight orientations. This is a broader prototype grammar, not a claim
  that the unchanged production self-check accepts it.
- Focused tests: 38 passed, including 16 protected-Racket labels across eight
  orientations, strict request typing, minimum/maximum counts, matched inputs,
  public metadata invariance and duplicate public-turn rejection. The final
  bounded self-review used two demos/four queries at seed 0 under both settings;
  nine rival families produced no query-disagreeing demonstration survivor.
  Explicit query-equivalent aliases are retained. This is finite evidence only.
- Protected sequential witness replaces the true marked core with radius-two
  exclusion and changes six cells on a qualified first demo. See returned
  `checks/9c75b1456763/causal/witness.json` and `causal/replay.json`.
- A relocated selected-source/runtime closure replayed both settings at maximum
  six-demo/four-query counts: 20 labels passed using fresh system Python -I and
  its own copied Racket. This was not a full-packet or whole-repository check.
- Reusable `audit.py` tests finite wrong rules; `export_examples.py` requires
  current native qualification and writes one-query public files with visible-byte
  hashes plus private labels/order/settings. Four qualified episodes yielded 16
  public turns; the existing public-export checker passed all 16.
- Keep old-source unresolved audits source-bound: the historical underfill/hole
  row concerns `0ce6fb...`, not current production `d5056d...`; this prototype
  neither clears it nor upgrades production approval. Next owner action: integrate
  the exact delta, run native qualification/acceptance and replay the causal
  witness. The manifest and execution evidence support that handoff.

## Final repair

- Final generator SHA-256: `d5056d94e7217a201f16d249328bf02f931acde3a301dfdffa2444e6e997a1c1`.
- Version / rule: `2.0.0` / `58004efe7e78`.
- Replaced rejection-sampled isolated rectangles with constructively placed connected room networks. Exact node requests no longer underfill.
- Every network has one marker, at least two separated fillable room interiors, and remote cells that require component-local marker propagation.
- Canonical profiles: `p18_5`, `p20_5`, `p30_4`, `p30_5`; each is scheduled in every band.
- Exact axes: `profile`, `nodes_per_network` in 2..4, and `layout` in `straight|bent`. Unknown or invalid overrides are rejected.
- Added strict grammar validation, Python rule mirror, three semantic witnesses, three executable rivals, and cyclic lesson identifiability.
- Added task-local regression tests and `workspace/semantic_probe.py` for source-bound future checks.

## Authority

Only `data/base/solutions/training/09c534e7__9c75b1456763.json#target_code` changed, to become byte-exact with canonical `program_solution`. Final base JSON SHA-256: `4d3854310812a5cb4ddbca39a49ab37d5bb006b385b5c122c1737c1daed13c55`. Canonical `program_solution` exact SHA-256 is `35809851bc0c1916920f2c9fab710a01428f36081fed4b6e81b418bdaa4f867e`; archival `raw_code` exact SHA-256 is `536152449410bd1a8bc8587c95009654c90f854d0b639fef64109e8d0b2e81cf`. Both normalize to rule hash `58004efe7e78` and solve all canonical pairs.

## Evidence

- Baseline battery: `checks/before/checks/9c75b1456763_before_battery_summary.json` — 6 green, 2 advisory, 4 failed.
- Final battery: `checks/after/checks/9c75b1456763_after_battery_summary.json` — 12/12 green.
- Task tests: `checks/task_tests_final.log` — 12 passed.
- Retained final-source probe: `checks/semantic_probe_final.json` — 360/360 strict, 360 unique inputs and outputs, every witness/rival and every cyclic two-example lesson verified.
- Post-repair solve: `solve/summary.json` — revision 1, 3/3 visible lessons, earlier exposure yes, no reference consulted during solve.

## Known limits and future checks

- Finite generated-domain evidence only; not a proof of universal model induction.
- The probe evaluates actual declared rivals, so future model failures should be harvested into new rivals/witnesses.
- Three duplicate-first-row generic mutations remained lawful; do not claim perfect mutation rejection.
- Re-run `workspace/semantic_probe.py` after any generator change and verify the reported source SHA before comparing counts.
- Keep the selected Racket source synchronized; preserve `raw_code` as archival provenance unless maintainers explicitly migrate it.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `d5056d94e7217a201f16d249328bf02f931acde3a301dfdffa2444e6e997a1c1`.

# Decisions: 9c75b1456763

## D1 — Replace rejection sampling with constructive placement (R1)

**Baseline behavior and rationale.** The original implementation attempted to place requested rectangles through repeated random proposals. Its likely intent was easy geometric variety, but no retained rationale explained why underfilling an exact request was acceptable. A reproduced exact `n_rects=3` request could return only two rectangles, and the baseline override gate reported generation, mismatch, and self-check failures (`checks/before/checks/9c75b1456763_before_override_results.json`).

**Decision.** Compute legal room-center columns directly, with minimum spacing and bounded one-cell jitter. Every requested `nodes_per_network` value in 2..4 is therefore realized without retries or silent underfill.

**Rejected alternatives.** Increasing the retry budget would reduce but not remove underfill and would leave seed-dependent tail failures. Retrying the whole scene until success would hide the defect, distort the requested distribution, and make exact overrides harder to audit.

**Probe and failure mode.** Exact-axis round trips are covered by `tests/test_generator_9c75b1456763_repair.py`; the official override gate exercised 3,240 draws across 36 cases and three bands. A future width/profile change could violate spacing assumptions, so `_jittered_columns` raises rather than underfills.

## D2 — Generate connected room networks, not isolated rectangles (R1, R2)

**Original rationale.** The baseline summary described one or two marked solid rectangles. That is locally compatible with the canonical rule but does not force a learner to associate one marker with an entire connected network.

**Decision.** Each nonzero component contains 2–4 thick 5x3 rooms connected by one-cell blue corridors. The marker is placed in one room. Other rooms supply distant fully surrounded cells, so `local_marker_room_only` is wrong on every retained probe draw. Two or three disconnected networks use distinct marker colors, defeating `global_first_marker` and `first_component_only`.

**Rejected alternatives.** Larger isolated rectangles would increase changed-cell count but still teach only local filling. A single connected component would omit component-local color binding. Fully thick connectors would create uncontrolled interior cells; one-cell corridors preserve connectivity without adding false 3x3 interiors.

**Probe and limits.** `test_generated_components_require_marker_propagation_between_nodes` verifies multiple separated interior regions and a remote fillable cell per component. The source-bound probe found all three witnesses on 360/360 draws. The grammar is intentionally narrower than all possible canonical-valid networks; it targets the missing causal evidence rather than universal shape coverage.

## D3 — Schedule all canonical shape/palette profiles in every band (R1)

**Decision.** The default schedule cycles `p18_5`, `p20_5`, `p30_4`, and `p30_5` in every band. These profiles encode the four public shape/palette combinations and the corresponding two- or three-component scale. The retained 120-per-band probe produced exactly 30 examples of each profile in each band.

**Rejected alternatives.** Random profile choice could create accidental small-sample gaps in a battery or lesson shard. Anchoring only one profile per band would entangle difficulty with shape and palette and let a learner treat canvas size as a rule branch.

**Probe and limits.** The official profile gate hit exact canonical profiles on 60/60 draws. Exact profile coverage does not by itself guarantee object-geometry boundary coverage; audit A2 is the counterexample motivating feedback F2.

## D4 — Expose only exact, recoverable axes (R1)

**Decision.** The public axes are `profile`, `nodes_per_network`, and `layout`. `observe_overrides` recovers all three from the generated grid, and unknown keys or invalid values fail loudly. Marker colors remain random because naming a requested palette without a recoverable semantic need would enlarge the contract without improving lessons.

**Rejected alternatives.** The baseline `texture`, `grid_h`, and `grid_w` controls were dead, misleading, or incompatible with canonical support. Keeping them as accepted-but-ignored metadata would preserve API appearance at the cost of training-data provenance.

**Probe and limits.** The final override gate accepted 3,240/3,240 supported requests and rejected unknown keys. `layout` is inferred from whether a connector detours; a future geometry change must preserve that observability or remove the axis.

## D5 — Validate the task grammar, not merely color presence (R2)

**Decision.** `self_check` now enforces rectangular ARC grids, one of four canonical profiles, required 0/1 colors, no sealed zero holes, the expected number of 4-connected components, exactly one non-blue marker per component, and multiple separated fillable room interiors. `strict_canonical_like` shares the analysis and accepts all four canonical inputs.

**Rejected alternatives.** Checking only shape, palette, and marker count allowed nonsolid rectangles and did not establish that a scene actually teaches propagation. Requiring generated corridor topology for canonical inputs would overfit the constructor and reject lawful public examples, so canonical acceptance is semantic rather than constructor-identical.

**Probe and limits.** The validator rejects explicit hole and markerless mutations. The generic mutation probe rejected 50/53 destructive mutations; duplicate-first-row can remain lawful, so mutation sensitivity is strong but not complete.

## D6 — Make rival hypotheses executable and bind them to witnesses (R2)

**Decision.** The semantic contract declares three named rivals and three witnesses, plus `WITNESS_RIVALS` and `lesson_identifiable`. A witness counts only when the authoritative mirror and its relevant rival differ. `EXAMPLES_NEEDED=2`; the retained probe checks every cyclic two-example start rather than only independent witness frequencies.

**Rejected alternatives.** Natural-language claims are not regression tests. Hard-coding rival names only in an external script would allow source declarations and probes to drift. Declaring a canonical shortcut that does not fit every canonical pair would misstate the public ambiguity, so `CANONICAL_SHORTCUTS` is empty.

**Probe and limits.** The official semantic gate verified three of three claims; the retained source-bound probe verified all 360 cyclic lesson windows. This still covers declared rivals, not every hypothesis a model may learn; that limitation directly motivates the automated gate proposed in `QUESTION_ANSWER.md`.

## D7 — Add a retained source-bound semantic probe (R4)

**Decision.** `workspace/semantic_probe.py` imports the final generator by path, records source SHA-256 and rule hash, uses the generator's real schedule and declarations, samples 120 draws per band, checks strictness, uniqueness, axis realization, change density, witness/rival disagreement, canonical shortcut validity, and all cyclic lesson starts.

**Rejected alternatives.** A copied list of rivals could become stale. A one-off notebook would be hard for future agents to rerun. A much larger Monte Carlo sweep would cost more while adding little confidence to deterministic profile coverage.

**Sampler and limits.** Easy uses seeds 31000–31119, medium 131000–131119, hard 231000–231119, with sample indices 0–119. Results are finite generated-domain evidence only. Reproduce with the command recorded in `RESULTS.json`.

## D8 — Synchronize selected authority text without changing semantics (R3)

**Decision.** Replace only the base JSON's selected `target_code` with the exact canonical `program_solution`. Preserve canonical JSONL and archival `raw_code`. This makes the selected source byte-exact while retaining the historical executable source.

**Rejected alternatives.** Editing the canonical Racket program was unjustified because execution parity already passed. Replacing `raw_code` would erase provenance. Leaving selected textual drift would keep the authority gate red despite equal normalized behavior.

**Probe and limits.** Authority sync reports selected exact sync and execution parity PASS for both exact source groups. The archival source remains intentionally exact-text divergent and is labeled as such.

## D9 — Freeze and solve the final generator (R2)

The final generator was hashed before the post-repair solve. The visible examples alone identified component-local marker propagation; revision 1 matched 3/3. Earlier exposure is declared `yes`, reference consultation during the solve is `no`, and private labels are not claimed. No generator edits were made after the solve freeze.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/9c75b1456763/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
