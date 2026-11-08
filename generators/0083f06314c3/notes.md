# Working notes: 0083f06314c3

Candidate 4.1.0, reviewed October 2, 2026. Original associated notes remain untouched in `evidence/associated_notes.jsonl`.

The original v4.0.0 passed all 12 battery stages, but reserved disjoint selected-template boxes. Greedy non-overlapping selection therefore survived all three published canonical pairs and ordinary support. The new composite overlap constructor refutes this rival and XOR composition without changing the Racket program. One adversarial slot per default four-example window overlaps; seed parity chooses its selector branch. The two canonical-anchor slots remain unchanged. Explicit one-copy overrides disable overlap and remain observable.

The lesson budget is now four rather than three so every default same-seed window contains the new witness. One-copy default frequency is intentionally lower in the overlapping mixture; the other adversarial slot retains difficulty-aware one/two-copy support. Selector 1 is now reachable. Color 9 is structural-only in this generator domain; panel-internal 9 and non-integer cell values are rejected before motif analysis. The rejected interior-9 mutation still demonstrates a mirror/Racket discrepancy outside the accepted domain; no general arbitrary-input parity claim is made.

Final copied-runtime task tests: 97 passes. Before/after batteries: 12/12 green each. Matched 240-draw sweeps: strict support remains 120/240, overlaps rise 0 -> 60; the final sweep has 240/240 actual Racket agreement. A separate 600-draw sweep has 300 strict, 150 overlap, and 600/600 agreement. All 128 both-branch six-axis min/max cases pass observed overrides, validation, and Racket parity. Exact commands and evidence are in the packet's `RESULTS.json` and `checks/`; `workspace/README.md` explains local replay.

The full repository suite has one unchanged source-only bootstrap failure (165 other tests pass); a pristine-source reproducer is supplied. See root `REVIEW.md`, `DECISIONS.md`, `QUESTION_ANSWER.md`, `AUDIT.md`, and `FEEDBACK_TO_CODEX.md` for the complete evidence and scope limits. Audit sources were not edited. The post-change Python solve passes four visible examples, discloses prior rule exposure, and makes no hidden-query or blind-inference claim.

Remaining support limits: finite connected monochrome masks, distinct template colors, bounded grids, one/two occurrences, and at least one selected match. No trained-model improvement, universal identifiability, or training-safe promotion is established by these checks. No Racket authority changed.
## Current reviewer considerations

Source SHA-256: `fee152a77b997f9a0bf46fabf890cdd3f5d8de027591586357b40c054c187fb5`.

# Distribution decisions: 0083f06314c3

The packet authorizes a bounded selected-task repair, not a library-wide rewrite. The immediate acceptance criteria are unchanged Racket semantics, preserved canonical support, observable override compliance, examples that refute the new canonical-consistent rival, and reproducible source-bound evidence. Original motivations below are inferred from comments and behavior unless explicitly documented; no author intent is invented.

## Canonical schedule and teaching budget

**Inherited:** half the default four-slot schedule consists of strict canonical anchors, using both selector branches. The source explicitly describes these as canonical-linked anchors. **Kept:** both anchor slots and their construction. Increasing novelty by replacing every anchor was rejected because it would weaken the bridge to the supplied examples. Both matched 240-draw censuses retain 120 strict draws; the independent final 600-draw census retains 300. Explicit overrides still opt out of the default canonical-anchor shortcut.

**Changed:** one adversarial slot in each same-seed four-example window now supplies two overlapping matches. Seed parity assigns that slot to A or B. The other adversarial slot keeps the previous difficulty-aware count range. Making both adversarial slots overlap would increase witness frequency but eliminate default single-copy examples from the adversarial distribution, so it was rejected.

**Changed:** `EXAMPLES_NEEDED` rises from 3 to 4. Three consecutive slots still cover both selectors and old adversarial features, but some three-slot windows miss the sole overlap slot. Four guarantees the new distinction within this default schedule. Alternative: retain three examples and force overlap into both adversarial slots, losing the useful one-copy support; rejected. Tests cover sliding windows and the battery finds all 12 sampled four-example lessons identifiable. This is a one-example teaching-budget cost, not an optimized or minimality-proven budget.

## Shapes, sizes, colors, and placement

**Inherited and retained:** small connected monochrome masks, selected sizes 3..5, template widths 3..4, board widths 8..12, grid heights 6..8, selected and unselected occurrence counts 1..2. The earlier source makes constructive finite-shape packing and bounded canvases explicit; any broader original pedagogical rationale is unknown. Arbitrary polyominoes, disconnected/multicolor masks, same-color templates, absent matches, and larger counts were rejected for this patch because they introduce additional semantic/distribution questions and require separate evidence. They remain limitations, not claims of full rule support.

**Changed packing:** enumerate compatible shifted two-copy unions from the existing shape vocabulary. Require genuine shared nonzero cells, exactly the intended two match positions, and at least one unoccupied wildcard cell inside each copy's bounding box. Pack the union as one object and reserve the union of its two boxes. This avoids the old separate-box exclusion and avoids writing/deleting shared cells during recursive placement. Explicit original occurrence counts are still checked after filling and distractor placement. Naively letting separate mutable objects overlap was rejected because backtracking can erase another copy's shared cells. A label-only change was rejected because the Racket union semantics were already correct.

**Kept adversaries:** same-color rotated distractor, same-shape wrong-color distractor, arbitrary nonzero filler in wildcard positions, and occurrences of the unselected template. The overlap construction does not replace these tests with easier scenes. Existing and new rivals remain in the semantic contract; post-change gate results show all registered witnesses and claims verified.

**Selector support:** add color 1 to the B selector palette. The semantic condition is “2 selects A; otherwise B,” so omitting 1 had no documented semantic rationale. Colors 0 and 9 remain excluded as selectors within the generator domain: 0 is background, 9 structural. The fix deliberately leaves distinct template colors and the separation of adversarial selector color from those colors as inherited teaching choices.

## Overrides and difficulty

Explicit overrides win, including `selected_copies=1` in a normally overlapping slot. In that case the builder emits one exact selected occurrence, not an overlap and not two copies mislabeled as one. Default overlap slots request two; non-overlap slots retain difficulty-dependent one/two support. All six axis boundaries were tested together in 128 Racket-checked combinations (64 corners per selector branch), in addition to the repository's override battery. These checks are finite and do not establish all-seed/all-combination correctness.

The one-copy frequency drops from 60 to 32 among the matched 240 draws. This is an intentional sampling cost of retaining 50% anchors while introducing overlap, not an accidental loss hidden behind the new witness. Hard defaults already favor two copies; explicit single-copy overrides still work there. Dimensions and template-size ranges are unchanged.

## Validation boundary

**Defect:** a canonical input with `input[0][1]=9` passed the original `self_check`; its Python mirror disagreed with actual Racket because the two crop treatments differ for an interior structural-color cell. **Decision:** reject any 9 not in a full-height divider, and validate integer ARC cells before motif/color-set analysis. Keep the malformed counterexample and the disagreement in evidence. Do not change Racket or silently normalize the malformed input. Widening the mirror to cover all arbitrary Racket inputs is a separate task and was not claimed here.

Exact built-in integers in 0..9 are accepted; booleans, floats such as `0.0`, and malformed cell values are rejected. This matches the intended JSON-grid boundary. It is not a promise to accept every NumPy scalar type or arbitrary numeric object.

## Rivals and lesson assertions

Add `disjoint_matches` (greedy row-major non-overlapping matches) and `xor_matches` (toggle membership instead of union). Both can survive examples with disjoint copies; the former fits all three published canonical pairs. The exact fixture has two three-cell occurrences sharing one cell: intended output has five marks, greedy output three, XOR four. Register a specific overlap witness and link it to both rivals. Mere witness counting without checking actual rival disagreement was rejected; the gate verifies both claims, and the standalone witness is executed through Racket.

No claim is made that these are the only remaining rivals. A program can still memorize this finite shape vocabulary, infer schedule artifacts, or fail on ungenerated semantics. Four-demo identifiability is relative to the registered competitors, not a proof against every possible program.

## Verification and tooling choices

Use the supplied runtime copier and Racket bridge; no substitute reference engine. The copier's static runtime mapping does not carry newly added task tests/workspace, so the task-local launcher copies these explicitly into a fresh temporary runtime and records the actual command, cwd, and manifest digest. It does not add sibling/predecessor checkout imports or claim OS-level isolation. Avoid editing the shared runtime mapper under a selected-generator assignment.

Preserve baseline and failed red tests. Run before/after batteries, direct all-draw Racket comparisons in two seed ranges, both-branch override corners, and all task tests in the copied layout. Run the whole repository pytest command as well. Preserve its one unrelated failure and prove the same failure in original uploaded sources instead of suppressing it or installing a package solely to make the report greener.

An initial ad hoc direct import did not reproduce the expected runtime `scripts` layout. It was replaced with the supplied copier, not with a fragile source-depth `sys.path` workaround. One stability run timed out at the tool boundary; the later completed invocation has a separate evidence directory. Neither is erased from the report.

## Scope, solve, and stopping

No Racket authority or shared code changed. Audit targets are findings-only and remain byte-identical. The fresh solve starts after the generator was frozen; it uses visible examples, one independently authored standard-library Python revision, deliberate diagnostic negatives, and visible-only checking. Prior exposure from required generator work is disclosed; the episode is not blind and masked correctness is unknown.

Stop with the concrete shortcut repaired, required checks/solve/audits complete, source scope bounded, and remaining failures explicitly recorded. Further distribution expansion or the shared bootstrap fix requires maintainer prioritization rather than silently enlarging this patch. `RESULTS.json` is the command ledger; `REVIEW.md` maps measured claims to evidence.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/0083f06314c3/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->


## Review review-e308b5f71b36818e: native orientation family (2026-10-24)

Current canonical generator v4.1.0 remains SHA-256
`fee152a77b997f9a0bf46fabf890cdd3f5d8de027591586357b40c054c187fb5`;
canonical rule hash remains `6a4eb398052b`. No production or authority change.
The separate `workspace/parametric/` family adds `orientation=fixed|rotations`,
with an exact canonical default and one final matching-mode change for rotations.
Selector-directed template choice remains the causal intermediate for the board
search and union. The native protected witness substitutes the wrong selected
template and changes the final answer.

The two-demo minimum now teaches both selector branches, wildcard zeros, exact
colors, overlapping union, rotations versus reflections, and varied match counts.
Independent self-review found a concrete initial teaching hole: three small demos
always had two positive groups under fixed orientation, while a query needed four;
a demo-fitted group cap survived. Demo two now has the maximum supported positive
group count (11 fixed / 12 rotations), and a named cap rival is refuted there.
Demo one contains a dense unselected-color distractor that also refutes selecting
the most frequent template color. All 13 finite rivals are parameter-aware.
The retained pre-repair fixture and independent reproducer are in
`checks/main/teaching-gap-before.json` and `probe_teaching_gap.py`.
The protected replay in `teaching-gap-before-racket.json` executed eight cases: 
both programs fit all three original demos, and the cap rival gives the retained
wrong held-query answer. Current source bindings and original sampler hashes are
recorded separately.

The sampler supports independent 2–6 demonstrations and 1–4 queries, ordinarily
3/4; four distinct queries include a 30×30 input / 30×20 answer with active content
across the enlarged board. Query prefixes and inputs are independent of parameter
settings and count requests. An episode demonstrates selector 2 plus one B code;
all queries use those demonstrated codes, with all seven B codes reached across
seeds. This is an explicit episode-support restriction, not a uniqueness claim
about unseen codes. Public files expose exactly one query input; full banks,
settings and programs stay private and IDs hash only visible bytes.

Actual current checks: 87 focused tests passed; 72/72 bounded Python episodes
succeeded across both settings and demo counts 2–6. Native qualification passed
four jobs at seeds 0/17 with 40 protected Racket evaluations. The source-qualified
audit passed 106 additional evaluations, including 2/6-demo boundaries, both
settings' 13 rivals on the first two demonstrations, and the dependency witness.
Four retained native example episodes each preserve four private queries and one
public first-turn projection. Evidence: `checks/0083f06314c3/qualification/`,
`audit/`, `examples/`, `sampling-final.json`, and `tests-final-command.json`.

The native inventory is `workspace/parametric/evidence/manifest.json`. This is
reviewer-ready, not owner-accepted or training-admitted. Exact-source owner
qualification and acceptance remain required after integration. The historical
selector-1 audit index is preserved, including its existing needs-triage status;
this prototype does not rewrite that record. Scope is finite tested rivals and
seeds, not universal learnability.
