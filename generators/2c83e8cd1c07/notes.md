# Working notes: 2c83e8cd1c07

## Review outcome

The selected baseline generator (`aa36dc5e433ccb3ab0be46f92dd003dfd6751b9e68084dad181e61bdb8cd7377`) produced lawful labels but had three blocking review defects:

1. It did not pin the canonical `RULE_HASH`.
2. Advertised texture controls were dead or overlapping, and exact dimension/count overrides were rejected, ignored, or silently drifted.
3. It generated only clear diagonal pairs, so the canonical-compatible shortcut “fill every same-color diagonal even through a nonzero interior” was never contradicted. There was no executable semantic witness/rival contract.

The reference Racket authority was not edited.

## Repair design

Version `3.0.0` uses a constructive 5×7 template that fits every declared 7×7-or-larger canvas. A prefix of five pairwise-disjoint clear paths realizes `segments=1..5` exactly. A sixth, differently colored diagonal crosses the first clear path at that path's endpoint, giving it exactly one nonzero interior blocker. Random rotations, reflections, and translations vary layout without weakening the witness.

Only three exact controls remain advertised:

- `grid_h`: 7..14
- `grid_w`: 7..14
- `segments`: 1..5

Unknown keys and out-of-domain values are rejected. `observe_overrides` recovers all three values from the returned grid. Full domains are legal in every difficulty band; difficulty changes only the default segment schedule and broad dimension draw.

The four-slot dimension schedule places `(7,7)`, `(8,8)`, and `(8,9)` anchors before a broad draw. Segment schedules are `1,1,2` for easy, `1,2,3` for medium, and `1,4,5` for hard. Each draw uses one additional color for the blocked pair, so a one-segment lesson retains the canonical three-color palette profile (background plus two endpoint colors).

## Executable semantic contract

`rule_mirror` is a pure-Python diagnostic mirror; the pinned Racket program remains label authority. The declared rival `ignore_interior_blocker` fills diagonal pairs without checking their interiors. It fits every usable canonical pair but differs on every generated draw. `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS` expose that distinction to the shared gates.

## Test-driven evidence

Before implementation, `tests/test_generator.py` produced 16 expected failures and 12 passes against the baseline: missing rule pin, rejected/ignored overrides, absent witness/rival declarations, and no blocked counterexample. After the minimal implementation, the same suite passed 28/28.

Final generator SHA-256: `497eb0a87949fc29126c1ce52314ce0c6d7e4b24e8e23d86b9c990ebad91eebe`.

- Required after battery: 12/12 stages green.
- Portable selected-task tests: 28/28 passed.
- Lesson census: 300/300 lessons materialized, 1,200/1,200 query rotations scored, 0 ambiguities, 1,192 unique inputs.
- Post-repair visible solve: 3/3 demonstrations passed on the first revision; earlier rule exposure declared honestly.

## Remaining limits

The finite rival set does not prove universal rule identifiability. Generated blocked pairs always use exactly one blocker and that blocker is an endpoint of a clear pair; this is deliberate because it provides a compact, unmistakable negative while staying within the small-grid palette/profile budget. The generator does not cover arbitrary malformed scenes, multiple blockers, colors occurring more than twice, or non-diagonal same-color pairs; those are outside its documented training grammar rather than claims about the full reference program domain.

Imported associated notes remain in `evidence/associated_notes.jsonl` with their original timestamps and provenance.
## Current reviewer considerations

Source SHA-256: `497eb0a87949fc29126c1ce52314ce0c6d7e4b24e8e23d86b9c990ebad91eebe`.

# Decisions: 2c83e8cd1c07

## Evidence baseline and scope

No prior return was used as a design lead. I read the selected baseline, canonical examples, imported associated notes, and the required before-battery evidence. The imported notes did not provide a completed repair to reuse. The baseline generator SHA-256 was `aa36dc5e433ccb3ab0be46f92dd003dfd6751b9e68084dad181e61bdb8cd7377`; the final generator SHA-256 is `497eb0a87949fc29126c1ce52314ce0c6d7e4b24e8e23d86b9c990ebad91eebe`.

The repair was limited to selected-task generator, tests, notes, summary, and workspace documentation. Audit targets were examined but not changed. The canonical Racket row was not modified.

## D1 — Keep the reference authority unchanged

**Original rationale:** Unknown. The baseline did not pin `RULE_HASH`, but its rule-smoke and authority-sync stages already showed the selected canonical program executed correctly.

**Decision:** Pin `RULE_HASH = "177b2df2b99a"` and leave the Racket program byte-identical.

**Alternatives rejected:**

- Rewriting the rule for stylistic clarity: unnecessary authority risk with no observed semantic defect.
- Broadening the rule to fill blocked diagonals: contradicted by the canonical zero-interior precondition and by visible examples.

**Probe:** Required rule smoke, Racket lint, and authority sync all passed after repair. The after summary retains the same authority-set hash as the baseline.

**Failure mode/limit:** The archival bank still contains a divergent historical source, reported by authority sync, but selected execution parity is PASS and was not part of the selected repair.

## D2 — Reduce the public control surface to three exact axes

**Original rationale:** Inferred from source names only. The baseline exposed grid dimensions, segment count, palette/count controls, singleton density/position labels, and textures, but several did not affect bytes or could generate invalid fixtures.

**Decision:** Advertise only:

- `grid_h`: integer 7..14
- `grid_w`: integer 7..14
- `segments`: integer 1..5

Every declared value is legal in every difficulty band. Unknown keys, booleans, non-integers, and out-of-range values raise `ValueError`. `observe_overrides` reports all three realized values.

**Alternatives rejected:**

- Keep dead axes as “diagnostic”: they would still enlarge the matrix and mislead callers about meaningful variation.
- Add palette axes: with one extra blocked pair, palette cardinality is mechanically coupled to segment count; exposing both would require a compatibility matrix without adding useful task variation.
- Keep negative textures (`single_endpoint`, `axis_aligned_pair`, `no_pairs`) in ordinary generation: they are malformed or out-of-grammar and do not teach the intended transformation.

**Probe:** Exact minimum/maximum combinations were tested in `None`, easy, medium, and hard settings. The final override gate reports no findings and rejects an unknown key.

**Failure mode/limit:** Callers cannot independently request palette size or arbitrary negative fixtures. That is intentional; these are not exact independent properties of the lawful grammar.

## D3 — Use a constructive geometry rather than rejection placement

**Original rationale:** The baseline tried random non-overlapping diagonal placement and could silently return fewer pairs after placement failures.

**Decision:** Use a fixed 5×7 base arrangement with five pairwise-disjoint clear paths. Selecting the first `segments` paths realizes 1..5 exactly. Apply one of eight dihedral orientations and a random legal translation within the requested canvas.

**Alternatives rejected:**

- Increase random placement retry counts: reduces but does not eliminate silent underfill and makes extreme override behavior harder to reason about.
- Backtracking search for arbitrary path layouts: more code and runtime for no demonstrated data-quality gain.
- Precompute a large catalog: unnecessary for the declared range; geometric transforms already provide safe variation.

**Probe:** `observe_overrides` is checked against the requested count inside `generate`; focused tests exercise extrema and 48 draws per band; override and self-check gates are green.

**Failure mode/limit:** Relative path geometry comes from one template family. This trades combinatorial shape breadth for exactness and a guaranteed semantic witness.

## D4 — Put a blocked diagonal in every normal draw

**Original rationale:** The baseline supplied only positive examples, and the canonical pairs also fail to distinguish a solver that ignores interior blockers.

**Decision:** Add one differently colored diagonal whose sole nonzero interior cell is an endpoint of the first clear pair. The official rule leaves it unchanged; the declared rival `ignore_interior_blocker` fills it.

**Alternatives rejected:**

- Add the counterexample only occasionally: complete lessons could still omit the load-bearing condition.
- Use a random unrelated blocker: harder to guarantee compactly at every grid/count extreme and could add arbitrary visual clutter.
- Use malformed one-endpoint or axis-aligned negatives: those test eligibility of candidate pairs, not the zero-interior condition that was actually underdetermined.

**Probes:**

- The rival fits all 3 canonical pairs.
- Semantic gate: witness `600/600`; rival claims `60/60` verified.
- Lesson census: 300 lessons × 4 query rotations = 1,200 rotations, zero ambiguity.
- Focused cyclic-window test checks every short three-demo window over the deterministic schedule.

**Failure mode/limit:** The generator does not teach multiple blockers or blockers that are not endpoints of another fillable pair. Those remain untested extensions of the same predicate.

## D5 — Anchor default dimensions to canonical profiles

**Original rationale:** The baseline used difficulty-skewed ranges; the required profile floor measured zero exact canonical-profile support in hard and only `12/60` canonical-envelope hits overall.

**Decision:** For sample-index slots 0–2, schedule `(7,7)`, `(8,8)`, and `(8,9)`; slot 3 uses a broad difficulty-skewed 7..14 draw. Exact overrides always win.

**Alternatives rejected:**

- Use only canonical dimensions: would reduce spatial variety and make layout size a shortcut.
- Rely on random chance: the baseline showed that hard-band support could disappear entirely in a 20-draw check.

**Probe:** Final profile floor: exact profile `25/60`, envelope `25/60`, all bands supported.

**Failure mode/limit:** Scheduled indices are predictable. Layout transforms, translation, colors, and segment counts remain independently keyed, so the schedule does not determine the answer.

## D6 — Use a small count curriculum by difficulty

**Original rationale:** Unknown beyond the baseline's general easy/medium/hard count skew.

**Decision:** Default cycles are easy `1,1,2`, medium `1,2,3`, hard `1,4,5`; unspecified difficulty uses `1,2,3`. Exact `segments` overrides remain valid everywhere.

**Alternatives rejected:**

- Uniform 1..5 in every band: valid, but weakens a simple curriculum distinction and makes easy lessons needlessly dense.
- Fixed count per band: creates a count/difficulty shortcut and weakens lesson diversity.

**Probe:** Focused tests require count 1 in every band and maxima of at least 2/3/5 respectively; all pass.

**Failure mode/limit:** Default easy generation never reaches 3–5 without an explicit override. The domain still supports those values, and the override gate verifies them in easy.

## D7 — Preserve canonical palette support with one extra color

**Original rationale:** The canonical examples use background plus two endpoint colors.

**Decision:** Draw `segments + 1` distinct nonzero colors: one per clear pair and one for the blocked pair. With one clear segment, the palette has exactly three colors including background, matching canonical profiles.

**Alternatives rejected:**

- Reuse a clear-pair color for the blocked pair: that would make a color occur more than twice and confound pair identification.
- Fixed colors: encourages color-specific shortcuts.

**Probe:** Profile-floor and diversity stages pass; focused tests verify each nonzero color occurs exactly twice.

**Failure mode/limit:** Maximum segments 5 plus the blocked color uses six of nine nonzero ARC colors; larger counts were not declared.

## D8 — Build reusable executable probes in the selected task

**Decision:** Added focused tests and a pure-Python `rule_mirror`/declared-rival interface. The tests cover rule pinning, exact controls, unknown/invalid overrides, every-draw blocked witnesses, canonical rival compatibility, complete short lesson windows, canonical-profile support, malformed inputs, and destructive mutations. `workspace/README.md` records portable commands.

**Alternative rejected:** A standalone rival-name script duplicating declaration names. The return guide explicitly favors iterating the generator's actual declarations; the shared semantic gate and lesson census already do that.

**Probe:** TDD first run against the baseline was red (`16 failed, 12 passed`); final portable selected-task run was green (`28/28`).

## D9 — Stopping criterion

I stopped changing generator bytes after the final required battery, selected-task tests, and 300-lesson rotated census passed at SHA-256 `497eb0a87949fc29126c1ce52314ce0c6d7e4b24e8e23d86b9c990ebad91eebe`. The post-repair visible solve used those same bytes and passed all 3 visible demonstrations in one revision. Further expansion to arbitrary blocker forms would be a new distribution-design decision, not a repair required by current evidence.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-254d83e902b42f90:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `497eb0a87949fc29126c1ce52314ce0c6d7e4b24e8e23d86b9c990ebad91eebe`. At disposition, audited bytes match the current source.

### Current decision

Bounded source497eb0a87949 audit:28reported task tests, strict semantics, compact exact-control sweep and canonical blocked/clear diagonals; no issue in tested domain. Target unchanged; no approval or blanket closure of other audits.

### Assessment or prior finding

## 2c83e8cd1c07

**Conclusion: No issue found.** Audited immutable generator SHA-256 `497eb0a87949fc29126c1ce52314ce0c6d7e4b24e8e23d86b9c990ebad91eebe`.

I compared the generator with all three canonical labeled pairs and inspected its constructive blocked-diagonal witness, validator, exact-control observer, rule mirror, and declared canonical-fitting rival. The combined audit snapshot passed **28/28** portable task tests and the strict semantic gate. A separate compact exact-control sweep also passed, including unknown-key rejection and declared extrema. The generated blocked pair is a legitimate counterexample to “fill every diagonal pair,” while every requested clear-segment count is realized exactly.

Evidence:

- `checks/audit/2c83e8cd1c07-combined-final/result.json`
- `checks/audit/2c83e8cd1c07-combined-final/checks/2c83e8cd1c07_audit_semantic_gate.json`
- `checks/audit/2c83e8cd1c07-override-final/checks/2c83e8cd1c07_audit_override_results.json`

Limits: this was a finite peer audit, not approval. I did not enumerate undeclared rivals or all seeds. The audited source was left unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
