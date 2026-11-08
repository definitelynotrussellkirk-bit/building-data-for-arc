# Working notes: 25e18d9bd322

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `62c31795ef3e67c6bc7bddd21508b6ea8a416d604dea01ad4ea51e89313ab406`.

# Decisions — 25e18d9bd322

## D1: Treat the selected Racket authority and canonical pairs as the law

**Choice.** Preserve the nearest-cell Manhattan rule, its bbox row/column tie-break, and lawful touching/tie cases. Pin `RULE_HASH = "f275e1e6250c"`.

**Why.** The baseline validator contradicted a canonical tie rather than exposing a Racket defect. The selected rule executes all three canonical pairs consistently, and the authority smoke test was already green before repair.

**Rejected alternative.** Remove ties or add a stricter separation rule until the old validator passes. That would narrow the task around a generator accident and erase a rule branch visible in canonical data.

**Probe.** `test_distance_ties_use_bbox_row_then_column_instead_of_rejecting_input` and `test_canonical_domain_and_python_mirror_match_all_authoritative_pairs`.

**Failure mode/limit.** The Python mirror could drift later; the task test compares every authoritative canonical pair, while the battery retains Racket rule smoke and authority sync.

## D2: Replace dishonest controls with four exact observable axes

**Choice.** Keep only `grid_h`, `grid_w`, `n_blobs`, and `color_mode`; give each a bounded public domain; reject unknown keys.

**Why.** Baseline override diagnostics had tens of thousands of findings because labels and actual effects diverged. A smaller truthful interface is more useful than a broad nominal one.

**Rejected alternatives.** Preserve every old axis and special-case the checker, or silently ignore unsupported keys. Both make experimentation non-reproducible and let callers believe they controlled a property they did not.

**Probe.** `test_rule_hash_and_every_declared_override_round_trip_exactly`, `test_unknown_overrides_reject_loudly`, and final override evidence `checks/after/checks/25e18d9bd322_after_override.log`.

**Failure mode/limit.** Only values in the declared domains are promised. Exact multi-axis combinations are supported by scene transformation/placement, but this does not imply arbitrary future axes compose automatically.

## D3: Link canonical-profile anchors into every three-draw curriculum window

**Choice.** Use a deterministic scene schedule in which every third default draw is a transformed canonical-profile anchor.

**Why.** The baseline profile-floor stage found no dependable canonical support. An anchor makes the training distribution visibly connected to canonical sizes/palettes instead of relying on low-probability coincidence.

**Rejected alternatives.** Pure unconstrained randomness or copying canonical grids verbatim. Pure randomness failed the profile floor; verbatim repetition would create memorization and low diversity. The final approach transforms lawful scenes and varies size, color mode, palette, and reflection.

**Probe.** `test_default_schedule_supplies_profile_support_and_named_counterexamples`; final `profile_floor` battery receipt.

**Failure mode/limit.** Sample index influences scene class. ARC solvers see only the grid, so sample-index periodicity is not itself an input shortcut, but downstream data splitting should avoid assuming IID scene classes.

## D4: Make the strongest canonical shortcut executable and unavoidable in lessons

**Choice.** Encode “minimum distance to bbox top-left” and eight other plausible competitors as executable rivals, then schedule counterexamples so each three-example lesson refutes them.

**Why.** The bbox-origin rival fits all three canonical pairs, making it stronger than a hypothetical concern. An exact final-generator witness at seed 73/sample 0/medium reverses the intended and rival choices.

**Rejected alternative.** Add prose saying “distance means nearest cell” while leaving generated examples ambiguous. That tests documentation following, not task induction.

**Probe.** `test_strongest_canonical_demo_shortcut_is_executable_and_generated_against`, `checks/shortcut/25e18d9bd322/counterexample.json`, and the 300-lesson census.

**Failure mode/limit.** The rival registry is finite. Passing it is evidence against named shortcuts, not a theorem that no other program fits.

## D5: Preserve legal tie teaching and use four candidates in the default tie scene

**Choice.** Retain an exact nearest-distance tie resolved by bbox row/column, but place an additional earlier distractor so reading-order-first is wrong in the same lesson.

**Why.** The first complete census found 9/300 lessons ambiguous under `first_candidate`; each came from the three-candidate tie default omitting its intended earlier distractor. This was a lesson-assembly defect, not a rule defect.

**Rejected alternatives.** Delete ties, reorder the winner to first, or remove the first-candidate rival. Each would conceal the ambiguity rather than teach both branches.

**Probe.** Exact failing census seeds are locked by `test_census_reproductions_refute_reading_order_first`; red/green evidence is in `checks/tdd-census-red.log` and `checks/tdd-census-green.log`.

**Failure mode/limit.** The fix is tied to the current scene catalog. New scene classes must rerun the full census rather than relying on per-example witness frequencies.

## D6: Add lawful reflections and uniformly sample feasible extreme colors

**Choice.** Reflect target masks where placement permits and select the required palette extreme uniformly from feasible extremes.

**Why.** The standalone linter exposed only three normalized output masks, and the diversity test later isolated palette skew. Reflections increase shape support without changing semantics; uniform feasible-extreme selection avoids systematic low/high color bias.

**Rejected alternatives.** Random arbitrary shapes or choosing max/min after an unrelated palette draw. Arbitrary shapes risk illegal/disconnected objects; the old extreme mechanism was measurably skewed.

**Probe.** `test_default_outputs_cover_reflected_shape_variants`, `checks/tdd-diversity-red.log`, and final lint/diversity logs.

**Failure mode/limit.** Crop outputs necessarily repeat because a finite connected-shape catalog is used. The final diversity stage reports 38% unique outputs over 300 pairs and retains that note.

## D7: Separate feature probes from semantic rival witnesses

**Choice.** Put legal feature-presence checks in `FEATURE_WITNESSES`; require every `SEMANTIC_WITNESSES` entry to correspond to an executable rival disagreement.

**Why.** An intermediate semantic gate correctly rejected two entries that showed feature presence but no competing output. Calling them semantic witnesses inflated evidence without proving identifiability.

**Rejected alternative.** Invent dummy rivals that always disagree or weaken the gate. That would satisfy the shape of the contract while destroying its meaning.

**Probe.** `test_every_semantic_witness_names_an_executable_rival_disagreement`; intermediate failure `checks/after-semantic-failed/`; final semantic gate log.

**Failure mode/limit.** Feature probes still matter for domain coverage, but they must not be counted as shortcut rebuttals.

## D8: Synchronize selected Racket source text without changing executable meaning

**Choice.** Copy the selected authority's `raw_code` exactly into `target_code`; do not edit the rule body.

**Why.** Baseline authority sync found selected-source divergence while execution parity already held. Textual synchronization removes split authority without taking an unjustified semantic change.

**Rejected alternatives.** Leave the divergence documented, or rewrite the Racket rule to mirror Python style. The first keeps a needless acceptance blocker; the second introduces semantic risk without evidence.

**Probe.** Final authority sync reports exact/comment-stripped/whitespace groups all count 1 and execution parity `PASS`.

**Failure mode/limit.** This is still a changed authority JSON byte sequence and is disclosed as such. Rule hash and behavior remain unchanged.

## D9: Build portable task-local regression tooling

**Choice.** Add 22 parameterized pytest cases under the selected task test directory and a standalone audit verifier under `checks/audit/verify_findings.py`.

**Why.** The general battery does not discover task-local tests automatically, and future agents need executable reproductions for canonical law, overrides, RNG purity, shortcuts, cyclic lesson starts, reflections, semantic witness integrity, and source-name collisions.

**Rejected alternative.** Rely only on one large battery pass or prose notes. That would make exact regressions hard to isolate and easy to lose.

**Probe.** `checks/task-tests/result.json` (`22 passed`) and `checks/audit/verification-summary.json`.

**Failure mode/limit.** The tests deliberately bind important deterministic examples. A future intentional curriculum rewrite must update them with equivalent semantic evidence, not merely new snapshots.

## D10: Do not patch adversarial audit targets

**Choice.** Reproduce and report `c0bd45c81959` and `1fe4628c64c4`; leave their source unchanged.

**Why.** The assignment explicitly requests audit, not repair, and selected-task deltas are tightly scoped. Both reports include exact Racket outputs, source hashes, domain status, and executable verification.

**Rejected alternative.** Opportunistically modify unrelated generators. That would mix ownership, enlarge the patch, and make acceptance unsafe.

**Probe.** `checks/audit/verify_findings.py` and the two `counterexample.json` files.

## Remaining limitations

The final evidence covers the production sampler, all cyclic start residues represented by 100 lessons per band, nine declared rivals, two canonical shortcuts, and 871 unique materialized inputs. It does not prove universal identification against every possible program. The scene catalog is handcrafted, the lesson schedule is structured, and output masks are finite. Any future expansion should rerun both the portable tests and a fresh 100-per-band census; witness frequency alone is insufficient because the first repaired version demonstrated that individual counterexamples can still assemble into ambiguous complete lessons.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/25e18d9bd322/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Current native distance-metric proposal

`workspace/parametric/` adds `metric=manhattan|chebyshev` with the exact canonical
Manhattan default and an alternative using the existing Chebyshev primitive.
It preserves monochrome cardinal components, nearest-occupied-cell selection,
stable bbox top/left ties and reconstruction of only the selected object.
The separate family supports 2–6 demonstrations and 1–4 queries, normally 3/4,
with matched inputs, 30×30 content and one-query public projections.

Two constructive scenes reject all 22 declared Python rivals under both metrics,
including Euclidean/centroid/bbox distances, discovery-order ties, connectivity,
raw cropping and hole filling. Retained bounded evidence covers 24/24 usable
episodes, 52 protected-Racket audit evaluations and 42 isolated task tests.
Independent review identified a nested-training-metadata projection gap; a
failing regression led to explicit input/output whitelisting in `public_turn`.
Ordinary generated episodes did not contain that private per-pair metadata.

See the prototype README and native inventory for exact grammar, scope and
evidence. Selection produces the winning object's cells; reconstruction consumes
them to determine output size, shape and color. The return includes a native
counterfactual metric witness and qualification for owner exact-source acceptance.
No production edit, acceptance or training admission is claimed. Production SHA:
`62c31795ef3e67c6bc7bddd21508b6ea8a416d604dea01ad4ea51e89313ab406`.
