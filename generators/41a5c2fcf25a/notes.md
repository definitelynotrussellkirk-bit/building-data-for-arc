# Current notes: `41a5c2fcf25a`

## Intended rule

Read the contiguous nonzero legend in row 0. Find every cardinally connected nonzero component in rows 1+. Sort components by area descending; break equal-area ties by top row, then left column. Recolor rank `i` with legend color `i` while preserving the legend row.

Canonical rule pin: `RULE_HASH = 729bc9e3873e`. Generator version: `3.0.0`.

## Current sampler

- Canvas: `10..14 × 11..16`.
- Legend/components: two to four.
- Body components initially use color `8`; legend may also contain `8` because that is canonical-lawful.
- Shapes are compact connected D4 transforms with scheduled areas.
- Observable exact axes only: `grid_h`, `grid_w`, `n_blobs`.
- Four-period schedule: `canonical_source_tie`, `broad_distinct`, `source_distinct`, `canonical_tie`.
- Three demonstrations plus one query; every four-sample window retains at least two equal-area witnesses and two source-color witnesses.

## Reversed decisions

The imported generator enforced distinct component sizes and excluded color `8` from the legend. Both choices were reversed because canonical examples require the missing branches. The old texture API was removed because several values were dead, destructive, overlapping, or unobservable, and difficulty bands rejected values advertised as globally valid.

Selected `racket_target.target_code` was synchronized to canonical text through the guarded authority-sync operation. This was comment-only normalization; rule semantics and archival `raw_code` were unchanged.

## Evidence

- Canonical boundary counterexample: `counterexamples/tie-and-source-legend.json`.
- Independent oracle/tool: `workspace/reference_probe.py`.
- Portable regression suite: `tests/test_generator.py` (`48/48` passed in the return).
- Final battery: `checks/after/checks/41a5c2fcf25a_after_battery_summary.json` (`12/12` green).
- Fixed-seed schedule census: `checks/schedule-period-s0.summary.json` (`12` lessons, `48` rotations, no ambiguity).
- Larger census: `checks/lesson-census-100.summary.json` (`300` lessons, `1,200` rotations, no ambiguity).

## Known limits / open findings

The generator covers a compact shape family rather than every connected shape accepted by the Racket rule. The finite rival set does not establish universal identifiability. The deterministic four-profile schedule may expose periodic correlations, although layout, palette, shape, size, dimensions, and count remain seeded and diverse. Extending shape/area support is reasonable future work only if it preserves exact controls and the current branch guarantees.
## Current reviewer considerations

Source SHA-256: `de46eb17d0f8121e402c86517a6547616cd3f78c198dd3afb839fed6bf7e3c5f`.

# Decisions — `41a5c2fcf25a`

## D1: Preserve the canonical rule; repair the sampler

**Choice.** Keep the area-descending recolor rule unchanged and rebuild the input distribution around it.

**Reason.** All five canonical labels and the baseline Racket smoke were correct. The failures were in distribution, metadata, controls, and exact source synchronization—not output semantics.

**Rejected alternative.** Altering the Racket rule to prohibit ties or color `8` in the legend would have erased lawful canonical behavior and trained the wrong task.

**Evidence.** `checks/before/checks/41a5c2fcf25a_before_rule_smoke.json`; `repo/generators/41a5c2fcf25a/counterexamples/tie-and-source-legend.json`.

## D2: Synchronize only selected `target_code`

**Prior state.** Canonical source and selected `target_code` differed by a comment; archival `raw_code` already matched canonical comment-stripped behavior. Execution parity passed.

**New choice.** Use the guarded `authority-sync --selected-only` flow. Change only `/racket_target/target_code`; preserve `raw_code` and canonical JSONL.

**Reason.** Exact active-authority identity is useful for source binding, while archival provenance must not be rewritten.

**Rejected alternative.** Hand-editing both selected and archival code would destroy provenance. Leaving the harmless text divergence in place would keep the strict authority gate red.

**Evidence.** `checks/authority-proposal.json`; `checks/authority-apply.log`; `checks/after/checks/41a5c2fcf25a_after_authority_sync.json`.

## D3: Make canonical branches ordinary, not “degenerate”

**Choice.** Treat equal-area components and legend color `8` as scheduled teaching branches.

**Reason.** Both occur in canonical examples. The rule explicitly defines equal-area ordering by top then left. Excluding either creates a plausible shortcut that generated data never refutes.

**Rejected alternatives.** Keep strictly distinct sizes; reserve `8` as a forbidden legend color; expose an `all_same_size` texture without guaranteeing the source rule. Each alternative narrows the learned rule below its authority.

**Probe.** `counterexamples/tie-and-source-legend.json` makes both rivals disagree with the canonical oracle.

## D4: Use a four-period curriculum with three demonstrations

**Choice.** Declare `LESSON_SCHEDULE_PERIOD = 4` and schedule two tie profiles plus two source-color profiles. A lesson has three ordered demonstrations and one query; every cyclic holdout is required to remain identifiable.

**Reason.** Three examples are sufficient only when each window retains the rare branches. Pure iid sampling could occasionally place the sole tie/source witness in the query, leaving demonstrations compatible with a shortcut.

**Rejected alternatives.** Increase demonstrations globally to four or more; sample rare branches probabilistically. More demonstrations cost training tokens, while probabilistic coverage is not falsifiable per lesson.

**Measured result.** All 12 fixed-seed starts and 48 rotations passed; the 300-lesson/1,200-rotation census also passed. These are finite declared-rival checks, not universal induction proofs.

## D5: Expose only three exact, observable axes

**Choice.** Keep `grid_h`, `grid_w`, and `n_blobs`; remove imported pseudo-controls such as fixed position bias, density labels, and texture modes.

**Reason.** The removed controls were dead, overlapping, destructive, or not actually observable from the returned grid. A smaller exact API is more useful to lesson assembly than a broad nominal API.

**Rejected alternative.** Preserve compatibility by accepting old keys and silently mapping them. That would hide caller mistakes and keep the unknown-key defect.

**Failure modes checked.** Unknown axes, booleans, floats, strings, out-of-range values, negative sample indexes, and unknown difficulty values all fail loudly; every legal exact override works in every band.

## D6: Construct shapes instead of retrying arbitrary scenes

**Choice.** Place compact connected D4-transformed shapes in four separated slots with predetermined area patterns.

**Reason.** Construction makes component count, separation, area ties, rank/position conflict, and exact dimensions guaranteed rather than probabilistic. It also avoids retry loops that can mutate requested dimensions.

**Rejected alternative.** Grow random shapes and enlarge the canvas after congestion. That breaks exact override semantics and makes failures seed-dependent.

**Known limitation.** Generated components are compact and areas are currently `2..6` although the validator accepts through `8`. This is deliberate YAGNI scope; broader shape diversity is a future distribution extension, not needed to close the documented defects.

## D7: Independent oracle and executable rivals

**Choice.** Put a reusable independent rule implementation and analyzers in `workspace/reference_probe.py`, then declare semantic witnesses/rivals in the generator.

**Reason.** Tests should not validate generator helpers against themselves. Named rivals turn “looks teachable” into a reproducible finite claim.

**Rejected alternative.** Compare only against the Racket program on generated examples. That proves labels, but not that demonstrations distinguish plausible wrong rules.

**Limit.** The rival set is intentionally explicit and finite. Passing it cannot rule out every conceivable shortcut.

## D8: Strict validator equals the supported training manifold

**Choice.** `strict_canonical_like` delegates to the structural `self_check`; teaching witnesses are evaluated separately at lesson level.

**Reason.** A single input can be lawful without individually containing every teaching witness. Conflating per-grid validity with lesson identifiability would reject useful complementary examples.

**Rejected alternative.** Require every grid to contain both a tie and source-color legend. That would collapse diversity and make the schedule redundant.

## D9: Audit targets remain unchanged

The assigned audits `0a2588a98f5b` and `b25434a1b56e` were findings-only. I produced source-bound reproductions and real Racket outputs under `checks/audit/`; no audited generator source was edited.

## Current parametric proposal: area or perimeter

`workspace/parametric/` adds the native opt-in `rank_by=area|perimeter` family.
Area remains the exact canonical Racket program. Perimeter counts all exposed
cardinal edges, including holes; component ranking consumes that measurement
before assigning legend colors. Two constructive demonstrations distinguish the
settings, cardinal versus diagonal connectivity, capped measurements, ties,
legend treatment and hole/bounding-box shortcuts. Independent counts support
2–6 demos and 1–4 queries; ordinary qualification uses 3 demos and 4 queries.
Four query profiles extend real shape content to 30×30 and eight components.

Retained bounded evidence: 24/24 usable episodes, twelve declared Python rivals
rejected by visible demonstrations, 52 protected-Racket audit evaluations, and
65 isolated task tests. A review-discovered complete-key tie mismatch in the
Python labeler was fixed by preserving canonical reverse-discovery stable order;
both settings have literal Python and protected-Racket regressions. See the
prototype README, native inventory and return
qualification/causal receipts for exact scope. These finite checks do not prove
universal identifiability. Reviewer qualification is a proposal for owner
exact-source acceptance, not acceptance or training admission.

The production generator remains at SHA-256
`de46eb17d0f8121e402c86517a6547616cd3f78c198dd3afb839fed6bf7e3c5f`.
Its retained capped-area and eight-neighbor sampling audits remain open. The
separate family's teaching contrasts do not clear those production findings.
