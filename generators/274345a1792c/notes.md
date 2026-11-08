# Current notes: 274345a1792c

## Rule and authority

The unique connected maroon (9) component is the prototype. Every magenta (6)
anchor reads the cell immediately above it: 1 means identity, 2 means 90 degrees
clockwise, 3 means left-right reflection, and 4 means left-right reflection
followed by 90 degrees clockwise. Normalize the transformed shape to a bounding
box starting at (0,0), translate that box to the anchor, and paint its occupied
cells cyan (8). An anchor remains 6 if the normalized shape omits (0,0); all
other unstamped cells remain unchanged.

Version 2.0.0 pins the existing canonical rule hash `2a00fd8158ab`. Canonical
Racket semantics and canonical examples are unchanged. The active base
`racket_target.target_code` now exactly equals canonical/raw source; the sole
text change removes a redundant comment that failed authority synchronization.
Python predictions in the generator are diagnostic mirrors and explicit rivals;
they do not label generated training examples.

## Supported input grammar and exact controls

Canvases have 9..24 rows and 12..24 columns. A single four-connected prototype
has 2..8 cells and fits a 3x3 bounding box; there are 1..5 anchors. Input colors
are fixed symbols 0,1,2,3,4,6,9, and each control belongs to an anchor. Stamps
fit in bounds, are pairwise disjoint, and avoid the prototype and every other
anchor/control. The validator accepts every canonical input independently of
difficulty; it is an explicit bounded subset of the wider Racket grammar.

Six independent axes control height, width, anchor count, prototype cell count,
prototype quadrant, and distinct input colors. `palette_size` remains a strict
compatibility alias for `n_distinct_colors`, not an additional degree of freedom.
Both spellings are observed and tested; conflicting values fail. Input palette
size equals three fixed symbols plus the distinct controls, so a requested
palette larger than `n_anchors + 3` is an explicit joint incompatibility. A single
palette override may increase a free anchor count; an exact requested count is
never silently changed. Integer controls reject coercion and unknown keys fail.

`position_bias` names the quadrant of the prototype bounding-box center; a
center exactly on the middle line is classified bottom/right. Placement uses
jittered 4x3 bins, reserving one for the prototype and one per stamp/control.
The smallest canvas has eight bins, so all six required objects always fit.
The previous inert `palette_kind`, `density`, and `texture` controls are removed.
Old malformed texture cases remain rejected inputs, not advertised production.

## Production teaching policy

The declared period is four: residue 0 supplies canonical-size/palette support;
residues 1 and 3 use five anchors, all four codes and an asymmetric six- or
seven-cell prototype; residue 2 draws broadly from every declared size/count
range. Prototype shape, position, control ordering and anchor bins vary.
The full family comprises normalized connected polyominoes fitting 3x3;
it is not an unbounded shape grammar.

Use four demonstrations and one query. Each five-pair cyclic window contains at
least two teaching slots, preserving a refutation if any one pair becomes the
query. Eleven distinct rivals are declared; four fit all five canonical pairs:
once per control, first three anchors, first three distinct control codes, and
at most five prototype cells. The retained repeated-control example in
`counterexamples/repeated-control.json` is labeled by actual public Racket.
The fixed-L shortcut fits the predecessor's generated population but only one
of five canonical pairs; it is not described as canonical-compatible.

Exact overrides can remove teaching cues. `lesson_identifiable` reports a rival
that fits all supplied demonstrations and changes the labeled query; it does
not certify arbitrary restricted-override lessons or hypotheses outside the
finite rival set. Reusing the same seed/index across bands can reuse core/free
inputs, so pooled draw counts must not be reported as unique-input counts.

## Findings, reversals, and limits

The retained lead is `review-24e4a642d527e4f2:v0001`, bound to predecessor SHA
`493922f8d197ad0bf16da0e11c13e320dd517439b185c0094f5240f36190493c`.
Its fixed-L/position and dishonest-axis findings are repaired in this candidate;
source-bound results and the proposed explicit disposition are retained beside
that audit. The protected `evidence/review_index.json` remains unchanged, so a
maintainer must explicitly close that old finding after integrating this source.
Acceptance or a changed source hash alone does not clear it.

A first candidate exposed palette count under two AXES names; lint correctly
identified the duplicate quantity. The current declaration collapses the axis
while preserving a separately documented and exhaustively checked alias.
An iterator-consumption bug in the first normalizer was caught by regressions
and fixed by materializing its input once; the real failure is retained.

An independent review found that the initial validator admitted overlapping
stamps although production never emitted them. Public Racket paints the overlap
in the retained `counterexamples/overlap-domain-boundary.json`; a canonical-
fitting paint-once rival differs there. The current domain explicitly requires
disjoint stamps instead of claiming to teach overlap. This is a deliberate
support restriction, not a Racket repair or proof that overlaps are unlawful.
Expansion to overlaps, clipping, distracting symbols, larger/disconnected
prototypes, or more than five anchors needs a separate distribution and teaching
review. Disjoint placement also admits coordinate/bin regularities; random
placement and finite rival tests do not prove universal induction.

`tests/` retains portable contract and teaching regressions. The reusable
`workspace/probe_distribution.py` saves all sampled inputs, seeds and source
hashes; the return's Racket batteries and lesson/schedule censuses provide the
reported verification. No approval or training admission is inferred locally.


## Current owner acceptance

Accepted the scoped generator, portable tests and task-local authoring tools using the October 3 lightweight policy. All semantic batteries, Racket comparisons, censuses, solves and replay counts in the reviewer evidence remain reviewer-reported; no routine maintainer rerun or model training admission is claimed. Exact source/rule approval records bind the accepted bytes. Both random audits remain independent findings, and shared tool requests remain proposals unless separately implemented.

The supported disjoint, in-bounds stamp domain and 2..8-cell/3x3 prototype bound are explicitly accepted. Racket union semantics outside that domain are preserved; overlap rejection is a documented generator boundary. The prior fixed-L, repeated-control and exact-axis finding is explicitly resolved against this replacement source on the reported evidence, with finite-rival and pooled cross-band-duplication limits preserved.
## Current reviewer considerations

Source SHA-256: `3bbaba80d999266c004e3bd4fd823e0694b419bcd7c9046cf1d0332645376dd9`.

# Decisions: 274345a1792c

Assignment `review-beea677bae51f429`; final version 2.0.0; final generator SHA-256 `3bbaba80d999266c004e3bd4fd823e0694b419bcd7c9046cf1d0332645376dd9`. The selected baseline was version 1.2.0, SHA-256 `493922f8d197ad0bf16da0e11c13e320dd517439b185c0094f5240f36190493c`. Original design intent beyond the source and retained notes is unknown; the rationale below is this review's reasoning.

## Rule and production geometry

| Choice | Previous behavior and plausible rationale | Decision and alternative considered | Evidence and limit |
|---|---|---|---|
| M1: prototype geometry | A constant four-cell L cheaply exercised the four transforms but let the input prototype be ignored. | Enumerate normalized four-connected polyominoes of 2..8 cells in a 3×3 box; teaching draws use asymmetric 6/7-cell shapes. An unbounded component grammar was deferred because it would change placement feasibility and require new teaching coverage. | Final 600-call probe finds 89 normalized shapes. The fixed-L rival is checked directly; it fits only 1/5 canonical pairs. Finite 3×3 support remains a restriction. |
| M1: prototype position | Always `(1,1)`, presumably simplifying clearance. | Randomize its selected bin, local position and requested quadrant. Jittered bins permit constructive collision-free placement, including minimum dimensions and maximum anchor count. Free-form rejection sampling was considered but would make tight exact combinations less predictable. | 204 observed prototype origins, all four exact quadrant endpoints tested; 1,664-case placement sweep retained on the preceding source. Bins still introduce positional regularities. |
| M2: repeated controls | A shuffled code list assigned a distinct transform to each anchor, omitting repeated instructions. | Allow 1..5 anchors and repeat controls; five-anchor/all-four-code teaching draws force a repetition. All anchors are processed, including repeated codes. | Once-per-control and first-three-anchors rivals fit 5/5 canonical labels; actual Racket counterexamples differ at 4/6 and 12 cells respectively. Final comparison has 408/600 repeated-control calls. |
| Fixed color roles | Colors encode the control instructions and fixed prototype/anchor/output symbols. | Preserve fixed roles 9,6,8 and control codes 1..4. Do not add arbitrary palette permutations. | The canonical program distinguishes numeric symbols; a legal ARC color is not automatically a lawful role permutation. Palette size controls the number of distinct control codes, not symbol relabeling. |
| Anchor origin | An anchor is the transformed bounding-box origin, not necessarily an occupied pixel. | Stamp only transformed occupied cells. An empty top-left corner can leave the original anchor 6. | Canonical checks, positive T-shape regression, and the preserve-anchor/fill-box rivals exercise this distinction. |
| M5: overlap | The repaired sampler used disjoint bins, while an intermediate validator still accepted overlapping footprints. | Explicitly restrict the supported domain to disjoint in-bounds stamps; preserve the reference-lawful overlap witness. Expanding production to teach overlap unions was deferred because it would require collision policy, sample support and lesson design beyond this repair. | Canonical-fitting paint-once rival differs at shared cell `(7,6)` (actual 8, rival 0). Added regression: 1 failure/287 passes before restriction; 288 contract passes afterward. Racket semantics remain broader. |

The supported domain also excludes clipped stamps, noise, disconnected/larger prototypes and more than five anchors. These are distribution boundaries, not statements that the canonical Racket program is undefined for every such input. Python transformation mirrors are used only for diagnostics and rival comparison; generated target labels continue to come from the selected Racket reference.

## Exact controls and compatibility

Six independent `AXES` expose `grid_h` (9..24), `grid_w` (12..24), `n_anchors` (1..5), `prototype_cells` (2..8), `position_bias` (four quadrants), and `n_distinct_colors` (4..7). These ranges apply to exact overrides in every difficulty band, even when ordinary draws have narrower preferences. `observe` measures them from cells. Integer overrides reject booleans, strings and fractional values instead of coercing them; unknown keys reject.

The earlier draft declared both palette spellings as axes. That failed the battery lint as duplicated information (`checks/after-v2/`, source `d81d64cfce52cff7c694d2214eca5404cc617cbb7cf29211e983a7896b2e8357`). The final API has one axis plus `OVERRIDE_ALIASES = {'palette_size': 'n_distinct_colors'}`. Both names remain usable and observable, but simultaneous values must agree. Retiring the compatibility spelling entirely was unnecessary; declaring it a second independent quantity was misleading.

A grid always uses 0,6,9, plus its distinct control codes, so palette size must be at most `n_anchors + 3`. When only palette size is exact, the sampler may raise an otherwise free anchor count to fit it. When both are exact, incompatibility is reported rather than silently changing either request. The full 120-case matrix covers both spellings, all count/palette combinations and every unequal simultaneous-alias combination: 42 feasible cases and 78 structured rejections. The old `palette_kind`, `density`, `texture` and former position name are explicitly removed; keeping names that do nothing would preserve the original defect.

The validator now checks grid structure and symbols, one connected prototype, valid controls above every anchor, no orphan controls, bounds, prototype/control/other-anchor avoidance and disjoint stamp footprints. All five canonical authoring inputs remain accepted across difficulty settings. The task tests use `reviewer_support` to work in both source and copied runtime layouts.

## M4: lesson assembly and finite rivals

The selected policy is **four demonstrations and one query**, materialized from five consecutive accepted pairs. Production uses the first four as ordered demonstrations and the fifth as query. The supported rotation diagnostic holds each of the five pairs out once, retaining the relative order of the remaining demonstrations. `EXAMPLES_NEEDED=4` and `LESSON_SCHEDULE_PERIOD=4` declare this policy.

| Requested sample index modulo 4 | Purpose | Default construction |
|---|---|---|
| 0 | Canonical size/palette support | Three anchors with three distinct control codes; canonical-compatible profile dimensions and counts. |
| 1 | Teaching | Five anchors, all four codes, asymmetric six- or seven-cell prototype. |
| 2 | Broader supported distribution | All declared size/count ranges available; randomized shapes, positions and code multiplicity. |
| 3 | Redundant teaching | Same teaching requirements with a fresh randomized input. |

An early planning note sketched two alternating roles. The implemented four-phase cycle reserves explicit profile and free slots while retaining two teaching slots in every five consecutive indices. Consequently, a one-pair query holdout still leaves a teaching refutation. This is a raw-index construction argument; the production censuses additionally record actual accepted indices so rejection behavior is not silently assumed away.

The four canonical-compatible shortcuts are once per distinct control, first three anchors, first three distinct control codes, and at most five prototype cells. The seven other lesson competitors test fixed-L copying, identity only, exchanging controls 2/4, counterclockwise code 2, reversed composition for code 4, filling the whole bounding box, and preserving every anchor. The census discovers the actual declarations; its 19 namespaced entries represent 11 distinct hypotheses. The fixed-L rival's 1/5 canonical fit is explicitly separated from its validity as a predecessor-distribution shortcut.

Measured final production support is 300/300 lessons clear and rotations 1,500/1,500 clear, with 100 lessons/500 rotations per band, starts `0..99`, and the deterministic hashed seed recipe in the census. The seed-0 schedule run separately covers all four residues in all three bands: 12/12 productions and 60/60 rotations clear, only 16 distinct inputs because windows overlap and bands share some draws. The final 17 teaching tests also check the declared rivals, canonical fits, labeled witnesses, a constructed ambiguous query and 48 bounded schedule windows. The full battery's 12-lesson smoke and 600-draw witness test are additional finite checks.

Exact overrides can remove necessary contrasts: forcing a small prototype or one anchor can make some rivals observationally equivalent. The hook checks supplied demonstrations and each labeled query; it reports a rival that survives the demonstrations and changes that query. A restricted lesson with no predicted disagreement is not thereby evidence about every rule outside the chosen rivals. No arbitrary override-constrained curriculum, every-seed claim or universal identifiability claim is made.

## Distribution tradeoffs

The final comparison uses seed `70000+i`, sample index `i`, for `i=0..199` in each of easy/medium/hard, no overrides. All 600 draws from each version were retained with grid hashes and features. The repaired counts span all 2..8 prototype sizes, all 1..5 anchor counts, and all 4..7 input palette sizes; teaching naturally weights six/seven-cell shapes and five anchors heavily. This weighting is intentional so complete lessons contain refutations, while residue 2 maintains broader support.

The final sample has 200 unique grids in each band, but only 396 pooled unique grids because seed/index reuse across bands recreates some profile/free scenes. Baseline pooled uniqueness is 543/600; it is incorrect to claim pooled duplication improved. A future data exporter should use independent seeds or deduplicate inputs when combining bands. This review leaves the existing deterministic seed interface unchanged and records the limitation rather than redesigning seed semantics after final verification.

## Authority and prior audit disposition

Canonical rule hash `2a00fd8158ab` and canonical ledger SHA-256 `a1af567baabfe06f90d62dac826fa51e4d50bf322e6712cbaf6bc6aabc4a757b` are unchanged. A comment in the active base JSON target code caused exact authority synchronization to fail despite semantic parity. Only that comment was removed; no transform, output, canonical example or raw Racket body was changed. `checks/authority-sync-edit.json` binds both JSON file versions; the final battery reports synchronized authority and execution parity.

Prior finding `review-24e4a642d527e4f2:v0001` is a relevant source-bound lead. The fixed-L/position and ignored-control defects it described are repaired by the candidate, but accepting a new source does not implicitly close a finding. The packet disallows edits to its protected `evidence/review_index.json`; its SHA remains `f66a7cc0211b6f3809806b5b964245973b5feccba7ac2de5e10a0f2d78c22d6a`. A reviewer disposition sidecar in the retained finding's counterexample directory supplies a reason, final-source evidence and the explicit maintainer audit-status command. No unrelated audit status or training approval is changed.

## Actual reversals, retained failures and episode integrity

The baseline battery's six green/two advisory/four failed stages are retained. The first shape normalizer consumed an iterator twice and failed 97/167 tests; materializing once fixed that new defect. The duplicated alias axis failed lint and was collapsed. The overlap-domain mismatch survived an earlier green battery and was found by independent adversarial review, then captured by an additional red regression. Each report is labeled before, intermediate or final, with source snapshots and hashes; no green intermediate evidence is relabeled as final.

The blind solve was completed before repair work, with no reference exposure and 3/3 visible matches in one revision. The exposed solve was prepared on final generator bytes, used only its visible challenge during the episode, matched 4/4 demonstrations in one revision, and declared earlier exposure. Both private query scores remain unknown. No artificial failed solve was created to populate a negative example; the retained notes are assistant-authored summaries.

The first `review.py start` selected this task but ran out of space before saving its random seed. The failed path identifies the selected task; recovery kept that selection and used a new, recorded random seed constrained to its original pool residue through the supported draw API. The lost original seed is not reconstructed or claimed. `checks/draw-recovery.json` preserves the interruption/recovery facts. The passive F1 proposal journals a draw before baseline copying and was tested with partial writes, process exit and fresh-process resume; it does not retroactively repair the lost seed or alter the packet's shared executable.

## Final handoff strategy

The exact builder-produced patch `13a6290696e23131bb232f9ec5e2f46b39229468670b21d2c4b2f31f772f0eee` was applied to a new extraction of the original ZIP, inside the asserted independent Git root `/dev/shm/arc-round2-fresh-packet/WORK`. A separately created interpreter passed 305 focused tests and 305 portable task tests; public Racket application reproduced the retained 15×14 production fixture exactly. `checks/replay/fresh-return/report.json` binds all ten changed paths before and after verification, including every path covered by the portable runtime manifest, and records actual commands/directories. A checkpoint verified all 60,388 regular files before the active materialization was removed for space; restoration later matched that complete inventory. Fresh replay receipts were copied outside its temporary tree and verified before that materialization was removed. The original ZIP, earlier return/checkpoint and current full checkpoint remain retained.

Large reports are transported losslessly with original-path/size/SHA mappings, including complete census instances and every failure. Shared proposals and generic replay tools stay in `checks/`; only selected task files and its allowed active authority JSON enter the authoritative delta. `Acceptance: needs attention` records the explicit domain and prior audit-status decision with all final execution checks passing and separately reported.

The first independent-runtime installation encountered inode exhaustion on the scratch filesystem. Its failed command and import receipts are preserved in `checks/replay/runtime-setup-failed-overlay.json`; only the newly created incomplete runtime was removed, and a separate venv at `/dev/shm/arc-round2-fresh-venv` passed isolated dependency/import checks. This infrastructure recovery did not change generator source or either solve episode.

## 2026-10-24 native parametric reviewer addition

Assignment `review-eadf51744a104eb4` adds a task-local native family without
changing accepted production generator SHA-256
`3bbaba80d999266c004e3bd4fd823e0694b419bcd7c9046cf1d0332645376dd9` or the
canonical rule. `transform_family=mixed` returns the exact selected 1,373-byte
canonical program; `rotations` reinterprets controls 1..4 as 0/90/180/270-degree
clockwise rotations on matched inputs. Requests independently support 2..6
demonstrations and 1..4 queries. The four query profiles include a substantive
30x30 visible input whose prototype/control markers touch all four boundaries.

The required dependency is prototype discovery -> exact normalized occupied-cell
set -> per-anchor transform/stamp. A protected-Racket wrong-intermediate witness
replaces only that set with a fixed L and changes the final 30x30 output. The
bounded self-review ran eight jobs over seeds 0/17, demo counts 2/3, four queries,
both settings and twelve executable rivals: 677 protected-Racket evaluations,
zero surviving rivals. This is finite evidence only.

Final focused tests pass 25/25 and the portable task suite passes 330/330. Native
qualification passes both settings at seeds 0 and 17 (40 protected-Racket
evaluations); `qualification.json` and `execution.json` were byte-identical on a
fresh replay. Inventory manifest SHA-256 is
`edf66b00339aaee299cb810857d56ca521331ff1bb3ab2dfecd3a84e9fc4d94f`.
Reviewer status is ready for exact-source owner intake, not accepted or admitted
to training.
