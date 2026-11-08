# Review be547a6168f77dde — two public creation families

- Targets: public_eval_62593bfd and public_eval_e376de54; both reviewer-ready, neither owner-accepted.
- Both lacked references; new general Racket rules reproduce all eight supplied labelled pairs, including all test golds.
- 62593bfd: match shapes under D4, dock matches upward/unmatched downward; alternate selects largest post-docking connected group.
- e376de54: infer aligned endpoint baseline and middle-line length; alternate selects largest actual clipped edit.
- Staged tests: 25/25 and 26/26. Combined final run with importlib collection: 57/57 including six patch-verifier tests.
- Each audit: 20 seeds, 800 count/setting requests, 5,200 repeated pair instances, 200 distinct inputs, 156 protected Racket evaluations.
- Each preflight: four setting/seed jobs passed. Each saved-export checker: 16/16 single-query public files passed.
- Four source-bound causal cases passed build/replay and independent replay. Owner native qualification remains pending.
- Self-review repaired a color-count rival tie discrepancy and an executed singleton-ignoring teaching shortcut.
- Needs attention: register both new sources, review canonical fidelity, then separately run native qualification and fresh acceptance; no training admission.

## 62593bfd — shape matching before final connectivity

The default identifies eight-connected same-color objects against the modal
background and matches exact geometry under rotations/reflections, ignoring color.
Matches move to the top, unique shapes to the bottom, with columns/orientation
preserved. `dock_policy=largest_docked_group` then selects a four-connected
multicolor group on that docked grid. The 30x30 witness has original object sizes
[4,4,6,7,4,6,6,4,4] and resulting group sizes [20,6,6,6,7]. Neither the largest
original object nor skipped docking recovers the twenty-cell joined group.

Current preflight: checks/public_eval_62593bfd/preflight-final/preflight.json.
Audit: checks/public_eval_62593bfd/audit-v2/audit.json. Causal evidence and separate
replay are under that target's checks directory. The color-count rival initially
used an implicit Racket mode tie-break inconsistent with Python; explicit smallest
color ordering fixes it. It was never counted as a successful rival elimination.

## e376de54 — actual edits after reference-based normalization

The default uses the spatially middle segment, not the numerical median length.
The alternative computes cell additions plus deletions after clipping and marks
the largest change. The 30x30 case has reference length 12. A three-cell segment
gains nine cells; a singleton requesting eleven additions can gain only five.
Requested-change selection and median-length substitution each change the answer.

A real shortcut ignored singleton candidate lines. Protected execution showed it
fit both original lessons yet failed a lawful singleton-winner query. The first
lesson now contains both a clipped and an unclipped singleton, making the latter
the genuine winner. The second still teaches truncation. Retained historical
inputs/programs/labels and replay_shortcut.py verify the old hole and repaired
lessons at seeds 0,17,43 (18 protected evaluations); no historical data are
regenerated from the revised sampler. Preflight: checks/public_eval_e376de54/preflight/preflight.json.

## Runtime, tooling and exact scope

Both adapters are independently relocatable, read only local canonical.rkt,
support 2..6 demos and independent 1..4 query prefixes, use matched setting-neutral
inputs, and privately shuffle the full four-query bank before prefix selection.
Public turns whitelist only demonstrations and the current input. Audit counts
include repeated prefix requests; 5,200 is not an independent-scene count or a
Racket evaluation count. Current references are copied byte-for-byte into each
native folder; immutable public-parent records and shared runtime are unchanged.

Reusable audit.py files check executable rivals, Python/Racket agreement,
count boundaries, privacy mutation invariance, prefixes and hash-named exports.
verify_return_patch.py replays the patch on fresh originals and checks source,
runtime, canonical copies, immutable parents and preflight evidence; six tests
include source/runtime/parent/canonical corruption rejection. It checks bytes,
not the authenticity of self-authored receipts or owner approval.

The first aggregate pytest command hit duplicate module basenames; importlib
collection passed without editing frozen source. A grouped shell command timed
out during a preflight attempt; a fresh independent run passed. An exploratory
relative-runtime probe was refused; all reported checks use protected same-checkout
Racket. These attempts are recorded separately from successful final runs.

Final review was an author self-review, not an independent review. The first
sampler uses noncolliding dockable hooks and exact-shape distractors; the second
uses separated straight parallel segments with one aligned baseline. These are
explicit constrained grammars, not unrestricted parent coverage. Finite seeds,
rivals and counterfactuals do not prove universal identifiability or training
benefit. Owner registration, source review, native qualification and exact-source
acceptance must occur independently for BOTH builds.

Fresh return-patch replay passed: 22 changed source files apply cleanly to original
task homes; all 159 unique source/runtime bindings match. The retained receipt
binds the unchanged patch and original ZIP, before adding that receipt itself.
