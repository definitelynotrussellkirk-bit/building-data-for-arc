# Working notes: 7eba3ddf13bd

## 2026-09-28 — review-cc2260065455028d

Replaced version 2.0.0 with 3.0.1; unchanged canonical rule hash `f97ce42855bc`.

The old generator fixed one pair to color 4, required teleporting through a vertical barrier, and could produce identity outputs. It advertised dead controls and rejected declared dimensions in some difficulty bands. The baseline full battery had 6 green, 4 failed, and 2 advisory stages. A matched 600-case probe found seven identities, 537 tied-route inputs, and zero counterexamples to four canonical-compatible rival rules.

The replacement constructs four sample-index-scheduled modes (`single`, `chain`, `bypass`, `multiplicity`), rotates/reflections geometry, and varies portal colors 4–9. Layouts are sparse tree-derived mazes with additional loops, not precomputed examples. Unique shortest routes avoid learning arbitrary tie-breaks, and a nonzero painted-cell count excludes identity. Mirror search preserves mandatory entry teleport, exact count-two pairing, color-8 input portals, and the canonical U,D,L,R tie order for external fixtures.

Each witness requires actual disagreement with a named rival; multiplicity is rechecked after orientation. Four consecutive indices contain all modes. `lesson_identifiable` ignores query labels and checks only the finite named-rival family. Production labels must continue to execute the canonical Racket program.

Only `grid_h`, `grid_w`, and `portal_color` remain as independently observable controls. There are no ordinary negative textures. Legal dimensions are accepted across all bands. Retry exhaustion raises a reproducible error rather than silently returning the wrong lesson mode.

Candidate 3.0.0 failed the profile floor at 14/60. Version 3.0.1 increases canonical-size weight in five-color modes while retaining all dimension values; the final small census is 18/60 and independent larger census 283/600. Do not erase that failed experiment or claim the 25% threshold is a full distribution assessment.

Final review checks: 12/12 battery stages green; 49 task-local tests and 132 public tests pass. Independent Racket differential probe: 610/610 agreements, 600/600 distinct inputs with unique shortest routes, zero identities. Rival counterexamples in that generated census: color4-only 387; one-jump 150; mandatory portal 150; any-repeated-color 150. The complete review, receipts, seeds, and code patch are in the source-bound return packet.

## Next work, in priority order

Use the returned generator and probe before redesigning the rule. Integrate through normal review intake; rerun both test suites. Then measure whether trained solvers improve on the stored counterexamples and held-out topology, without using query labels to select demonstrations.

Broader topology, three-plus-pair chains, four-plus-occurrence decoys, singleton decoys, and difficulty calibration are not implemented. New modes should each have an explicit rival and independently Racket-verified witness before changing the four-example schedule. There is no downstream accuracy measurement in this review.

The selected canonical authority is synchronized; a preexisting archival solution divergence is reported by the battery and left untouched. Associated historical notes in `evidence/associated_notes.jsonl` are unchanged.
## Current reviewer considerations

Source SHA-256: `5ce1865b3bce007f9510fee7a6a12c33857940280f827cd347627ae99a9d5c6b`.

# Decisions and scope: 7eba3ddf13bd

## 1. Keep the selected Racket rule unchanged

**Original rationale:** the selected program already reproduces all four canonical examples. The original author's reasoning beyond the retained source/comments is unknown.

**Decision:** preserve the exact canonical program and pin its normalized hash. Stepping onto a portal automatically teleports; teleport entry costs one BFS step; colors 4–9 pair only when they occur exactly twice; only originally zero cells are painted 8. Neighbor order for external ties is U,D,L,R. Color 8 may be an input portal before becoming a path marker in the output.

**Alternative rejected:** changing the rule to simpler optional teleporting, excluding color 8, or labeling with the Python mirror. These would alter the existing authority without evidence of a canonical error. Boundary fixtures and independent Racket execution verify the retained semantics. External unreachable fixtures remain unchanged under the rule but are excluded from ordinary training because they teach identity.

## 2. Replace the one-color, one-barrier distribution

**Original rationale:** the baseline comments indicate that one required color-4 pair was intended to make the portal useful. It also made several wrong rules observationally indistinguishable from the intended rule.

**Decision:** retain the task's sparse walled-grid visual grammar but generate four lesson modes: single required pair, two-pair chain, optimal bypass, and exact-multiplicity decoys. Maze carving includes dead ends and some loops; logical route direction, transposition, and reflections vary. Unlike a random unconstrained-grid rejection sampler, construction makes reachability and semantic witnesses inexpensive to obtain.

**Alternatives:** merely recoloring the old portal would refute color4-only but leave one-jump, mandatory-use, and count-based shortcuts untouched. Fully unconstrained dense mazes might be more varied but risk slow rejection, uncalibrated distribution drift, and ambiguous shortest-path labels. The selected construction is a bounded improvement, not universal graph coverage.

**Evidence:** under the matched 600-case protocol, the old generator supplied zero counterexamples to all four named rivals. The replacement supplies 387, 150, 150, and 150 respectively. `checks/portal-probe/witnesses.json` retains exact inputs, true outputs, and rival outputs.

**Limit:** partitioned rooms still expose a recognizable geometry prior. Chain room order is reversed, not arbitrarily permuted. No three-or-more-pair routes are generated.

## 3. Require actual behavioral counterexamples

**Original rationale:** no semantic contract was declared in the baseline; absence of witnesses was not evidence of safety.

**Decision:** each witness means a rival changes the output, not merely that an object or color is present. Bypass examples have an available portal-using route, but the true non-portal route is strictly shorter and paints differently. Multiplicity examples have exactly three cells of the decoy color and are checked after orientation, because first/last row-major pairing changes under reflection.

**Alternatives rejected:** a disconnected unused portal does not test optimization; an irrelevant repeated-color decoy need not refute the rival. Weak witness predicates would overstate coverage.

**Failure mode:** named rivals are not exhaustive. Their diagnostic implementations share traversal infrastructure with construction; the separately executed canonical Racket rule is necessary to catch correlated Python mistakes. The 610-case oracle comparison is evidence, not a formal proof for every grid.

## 4. Make four-example lessons cover all four modes

**Original rationale:** the baseline requested three examples, but all came from one semantic mode. Why three rather than another number was chosen is unknown.

**Decision:** use `sample_index % 4`, set `EXAMPLES_NEEDED=4`, and keep the schedule independent of seed and difficulty. Any four consecutive indices cover all four modes. A two-pair chain necessarily includes a non-4 portal because its two colors differ. Generated lessons therefore contain strong counterexamples to the declared rival family. The lesson hook never reads query output.

**Alternative:** independent random mode sampling can omit a necessary witness from a short lesson. More examples cost training/inference context without serving another currently declared distinction.

**Limit:** sparse/random index sampling defeats the sliding-window guarantee. External consumers must preserve consecutive windows or call `lesson_identifiable`. The semantic gate tested 12 such lessons, and task-local tests exercise multiple seeds and offsets; no claim of identification among all programs is made.

## 5. Reject identity outputs and avoid ordinary ties

**Original rationale:** a separated start/goal with a helpful portal was assumed to make a nontrivial puzzle. Actual baseline cases contradict that assumption: easy seed 27/index 0 paints no cell, and the independent census finds seven identity outputs.

**Decision:** construct a unique shortest route with at least one originally zero path cell. Keep a rule-level tied-grid regression fixture to preserve U,D,L,R semantics, but do not require learners to infer this implementation-specific tie-break from ordinary demonstrations.

**Alternative:** reject only identity and allow all shortest-path ties. This retains arbitrary label choices; in the matched baseline census 537/600 inputs have multiple shortest routes. The new census has 600/600 unique routes.

**Limit:** `self_check` intentionally accepts externally supplied reachable, non-identity tied grids; uniqueness is an ordinary-construction guarantee, not a redefinition of the authority's domain.

## 6. Expose only real overrides

**Original rationale:** broad palette, density, position, and texture metadata appears inherited from a generic generator template. Several names never affect output; a more specific original rationale is unknown.

**Decision:** keep `grid_h=7..14`, `grid_w=9..18`, and `portal_color=4..9`. Height/width refer to final output orientation. A used first-route portal determines observable primary color; bypass scenes have one unambiguous pair. Reject unknown keys, strings, floats, booleans, out-of-range values, and generation-time negative textures. `None` follows the repository's default/no-override convention.

**Alternative:** implement every inherited advertised control. That adds unrelated complexity and conflicting constraints. Removing no-op declarations is more honest than pretending they work.

**Evidence:** 19,350 override draws accepted across 215 cases and all three bands, with zero structured incompatibilities. Tests cover invalid values, observed color, dimensions, determinism, and malformed grids.

## 7. Preserve canonical scale without removing hard cases

**Original rationale:** the old easy/hard dimension ranges provided a size-based difficulty proxy; explicit requested dimensions were incorrectly validated against those narrower bands.

**Decision:** every legal dimension remains available in every band. The ordinary sampler favors canonical 7×10/11 five-color profiles in the single/bypass modes, while chain/multiplicity modes retain a broader geometry distribution. Difficulty also changes loop rate and endpoint distance selection.

**Experiment:** candidate 3.0.0 passed earlier semantic checks but failed the strict small profile census at 14/60, despite 237/600 exact profiles in the retained larger matched-protocol census. That failure is preserved, not overwritten. Version 3.0.1 changes mode-conditioned weights, then passes 18/60 in the pinned floor check and 283/600 in an independent protocol. The checker, seeds, canonical profiles, and threshold are unchanged.

**Alternatives:** lowering the threshold would conceal the issue; fixing all dimensions to the canonical scale would sacrifice useful geometric variety. Neither was used.

**Limit:** the small-census margin is only 3 cases above the minimum, and the weighting is intentional distribution calibration. Report larger and per-mode counts alongside the pass rather than treating one threshold as a complete quality measure. No model-based difficulty calibration was performed.

## 8. Fail loudly and keep review tools local

**Decision:** cap layout retries at 96 and report seed/index/band/shape/color/mode on exhaustion. Do not silently return a fallback that violates the lesson mode. Keep the differential probe, fixtures, and regression tests inside the selected task; findings-only audit scripts and receipts stay under packet `checks/`.

**Evidence:** focused tests, the public repository suite, the complete battery, independent reference comparisons, and negative/failed runs are retained. The probe binds generator, analyzer, canonical program, prelude, and custom-fixture hashes and refuses to overwrite existing evidence.

**Limit:** there was no independent reviewer subagent available. The review used inline source inspection, executable regression checks, and an independent-language authority rather than claiming an external code review. Sources of the randomly drawn audit targets remain unchanged by design.
