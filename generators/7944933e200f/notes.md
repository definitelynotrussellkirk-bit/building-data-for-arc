# Current notes: 7944933e200f — version 3.1.1

## Intended rule and authority

Find maximal four-connected monochromatic nonzero components. Rank each component by its color's total frequency over the entire input, preserving first row-major component order on ties. Return the unmasked original-grid crop of the first ranked component. Background holes and foreign colors inside its bounding box remain present. Local component size, the color's union bounding box and numeric color order do not determine the answer.

`RULE_HASH` remains `9b761bca5c45`. The canonical ledger and archival `raw_code` are unchanged. Official selected-only authority synchronization changed active `target_code` formatting to exactly match canonical text; it did not change semantics. Archival raw-code SHA256 remains `9b761bca5c4577e1d0ec28e5747e599423b62a060f51669401ed5238cbceae0d`.

## Sampling and teaching contract

The default period is 40: 20 rich scenes at even indices, 11 public-family nuisance scenes and 9 other general profiles at odd indices. All 15 original profiles remain available, including explicit public overrides. Three demonstrations plus one query use consecutive samples; every query rotation retains a rich demonstration.

A rich scene places a more frequent color first, then a selected ring. Three other colors tie for minimum total frequency; the selected color is numerically between the two later tied colors. The common color is independently selected from the four-color palette. A detached diagonal selected-color cell distinguishes four- from eight-connectivity and component from whole-color crops. Interior foreign colors and zeros distinguish original crops from masked crops. All feasible ring anchors with enough later placement capacity are considered.

The nine declared rivals cover singleton-only output, smallest local component, first object, whole-color bbox, masked crop, last tied object, both numeric tie directions, and eight-connected crop. Only the singleton rival is declared to fit all five canonical labeled pairs. `lesson_identifiable` validates literal integer labels and reports ambiguity under this finite set; it does not prove universal identifiability.

Literal integer request scalars are required; boolean/float/string seeds and indices are rejected, as are negative indices. Integer seed magnitude is unrestricted. Rich easy scenes use 9–10 dimensions, medium 9–14 and hard 13–19. Other constructors retain their original sizes. The validator/mirror support lawful inputs through 30×30; default hard generation does not claim that full size support.

## Findings and reversed decisions

The original seed-0 medium indices 5–8 teach a singleton-only shortcut and then request a 3×3 unmasked ring crop. Prior unresolved review `review-d279da981a00a49e:v0001` supplied the lead; this review reproduced it with actual Racket. Minimal complete lessons and source provenance are retained in `counterexamples/review-17505960f28bc92e/teaching-lessons.json`.

An intermediate forced-canonical-replay choice failed inherited diversity checks at 282/300 and 287/300 unique inputs. It was removed: exact profile support means matching dimensions and distinct-color count, and varied public-family nuisance scenes suffice.

An intermediate eight-rival repair always chose the largest tied numeric color in rich scenes. Independent review reproduced seed-0 medium indices 0–3 where a highest-color rival fit demonstrations but changed the query. Version 3.1.1 adds that ninth rival and the three-way tie construction; the retained old lesson is now rejected. Numeric float labels that compared equal to integers are also rejected explicitly.

The editable task-local test was ported to `reviewer_support` path/import helpers; no frozen task-root fixture was edited. Exact active authority synchronization and archival-byte preservation remain tested.

## Proposed extension and reusable authoring tools

`workspace/parametric/` contains a proposed, unapproved min/max global-frequency parameter. Its default exactly emits canonical Racket; maximum negates the stable sort key. Parameters are fixed per episode, demonstrations distinguish the two settings before queries, and labels execute through Racket. Arbitrary-input acceptance is setting-dependent; its constructor checks both domains.

`workspace/reproduce_teaching_gap.py` replays the original lesson against selected or retained source, explicitly labeling Python mirror outputs. `workspace/evidence_archive.py` packs, verifies and safely restores exact large evidence using paths, sizes and SHA256 manifests without deleting originals.

## Current limits

Rich cases emphasize rings and the middle of three tied numeric colors. The finite nine-rival guarantees are not arbitrary-shape/color induction or exclusion of every alternative program. The compact parametric constructor is a demonstration, not production approval. Current review counts, exact commands, independent-review dispositions and fresh patch replay are in the returned `REVIEW.md` and `RESULTS.json`; audit-only sources are unchanged.


## Current public prototype identifiers

Public filenames now derive only from visible demonstrations and query inputs. The original source/report is retained under `workspace/parametric/evidence/reviewer-original/` and `reviewer-reported/`; the corrected Racket-backed export is in `owner-current/`. The twelve focused naming/writer checks passed across six tasks. This correction does not approve the prototype or rerun its full repair battery.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-d279da981a00a49e:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `5b2e0eb65c42a9cd61ad2f041463a0db226957cec6b6e8be1213280dbad74473`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve singleton/min-frequency teaching and editable task-test portability findings:3.1.1 includes multi-cell and symmetric numeric-tie witnesses,9 rivals and portable helpers; reviewer114 tests,300 lessons/1200 rotations and120 fixed-seed lessons/480 rotations pass. Current source a0ccc92d7b4cb372cbd538f12851b45efdb78245fb5666af31965714424ad7cd. Evidence remains reviewer-reported and finite; no universal or training-admission claim.

### Assessment or prior finding

## 7944933e200f

**Classification: reproduced teachability defect, plus a portable-test defect.** Generator SHA-256 `5b2e0eb65c42a9cd61ad2f041463a0db226957cec6b6e8be1213280dbad74473`; rule hash `9b761bca5c45`.

The strongest canonical-fitting shortcut is `first_minimum_frequency_cell_only`: count each nonzero color globally, then return a 1×1 crop containing the first row-major cell whose color has minimum total frequency. It ignores connected components and bounding boxes. This rival matches all 5/5 canonical labeled pairs because every canonical selected crop is a singleton.

An ordinary generated four-pair window reproduces the ambiguity:

- seed `0`, difficulty `medium`, sample indices `5, 6, 7, 8`
- three demonstrations: profiles `public_5`, `public_4`, `public_5`; selected object sizes `1, 1, 1`
- query: profile `crop_with_intruder`; selected object size `8`
- every input passes the target validator and belongs to a declared generator profile
- the rival fits all three demonstrations, but predicts `[[1]]` for the query
- the selected Racket authority returns the unmasked 3×3 crop `[[1,1,1],[1,5,1],[1,1,1]]`

The exact lesson, input, rival, Python oracle, Racket output, source hashes, and replay command are retained in `checks/audit/7944933e200f/probe.json` and `checks/audit/7944933e200f/counterexample.json`; the Racket receipt is `checks/audit/7944933e200f/racket.json`.

The official semantic gate also fails because this generator declares no `strict_canonical_like`, semantic witnesses, or `lesson_identifiable` contract: `checks/audit/7944933e200f/semantic-gate/checks/7944933e200f_after_semantic_gate.json`.

The retained task tests do not run in the portable selected-task layout. Preflight reports a fixed-depth canonical path under `generators/7944933e200f/data/...` and recommends `reviewer_support.find_root/canonical_path/canonical_pairs`: `checks/audit/7944933e200f/task-tests/result.json`.

**Suggested repair.** Add the missing semantic contract and a deterministic lesson schedule that puts at least one non-singleton selected crop in every complete lesson; declare the singleton rival. Independently, migrate the test’s fixed `parents[...]` canonical lookup to `reviewer_support`. No audit-target files were changed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-d279da981a00a49e-v0001/audit_assets.json), manifest SHA-256 `02e34af9f3a5652453d2fe8a42ae565ba5d443fbbce2a016eba8c56aeb0116f3`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `a0ccc92d7b4cb372cbd538f12851b45efdb78245fb5666af31965714424ad7cd`.

# Decisions — review-17505960f28bc92e

## Scope, authority and ordering

The assigned original family is training `d9fac9be`, generator `7944933e200f`. The exact recovered request archive is SHA256 `5775c5b7ff73d307ae355afa19f53398b0639bbf9c318fb8b2369f5c065078ad`. The assignment was drawn once and retained. The official verifier checked all 103,278 workspace inventory files and both outer entry files after full extraction. A full extraction in the ordinary workspace failed because the host filesystem was full; an executable temporary memory filesystem allowed complete verification and execution without changing packet contracts or deleting unrelated files.

The separate blind solve was finished before reading any selected-task source. The parametric authoring priority was honored: a runnable min/max extension executed actual Racket before the canonical repair agent was released to modify production. Later independent audits were drawn once after the generator work. Their findings remain separate from the selected repair.

The canonical transformation is unchanged: find monochromatic nonzero four-connected components; rank each by its color's whole-grid population; retain row-major component order on equal populations; crop the original grid to the selected component's bounding box, preserving every interior cell. A component's local area is not its rank, disconnected components of the same color remain separate, and an unmasked crop can contain other colors and background.

The selected solution's active `racket_target.target_code` was synchronized by the official selected-only authority tool to the existing canonical multiline text. This was a whitespace-only authority repair: canonical ledger, normalized rule semantics, `RULE_HASH=9b761bca5c45`, and archival `raw_code` remain unchanged. The unchanged ledger SHA256 is `9d46eb627dac0d3f096b8b1a63dd95e012039cf72d0d08f3d1bbbc109211965f`; the archival raw-code SHA256 remains `9b761bca5c4577e1d0ec28e5747e599423b62a060f51669401ed5238cbceae0d`. The selected executable text SHA256 is `89116268dbf1746b792e3f5d1508d920d7e053dee7a11d1519fea6c426f055a8`. No catalog, approval record or shared runtime source was changed.

## D1 — Repair a teaching failure, preserving the rule

The original generator was version 3.0.0, SHA256 `5b2e0eb65c42a9cd61ad2f041463a0db226957cec6b6e8be1213280dbad74473`. Prior unresolved `review-d279da981a00a49e:v0001` supplied the lead; its claims were not substituted for fresh measurements. Reproduction at seed 0, medium, indices 5–8 confirms a three-demonstration lesson that permits the singleton-only rival and then asks for a 3×3 crop. All four original inputs were checked with executed Racket, independently of the Python mirror.

The original author's rationale for allowing this sequence is unknown. Correct individual labels did not teach the intended component crop. Purely increasing random sample count was rejected because it would not constrain complete lessons. Discarding every singleton output was rejected because singleton crops are canonical and legitimate. Changing the Racket rule to a singleton rule was rejected because it would erase intended lawful behavior.

The repair controls the schedule while keeping all 15 original scene profiles and explicit overrides. The default lesson contract uses three demonstrations and one query, with four consecutive indices. Every even index is a rich semantic witness, so every four-pair window has two such inputs and every held-out query rotation retains at least one rich demonstration. The executable contract checks labels and the declared finite rivals; it does not assert uniqueness among arbitrary programs.

| Slots in the 40-step period | Count | Role and rationale |
|---|---:|---|
| Rich semantic scenes, every even index | 20 | Teach global counting, spatial ties, four-connectivity and unmasked component crops together |
| Public-family nuisance scenes, odd indices | 11 | Preserve canonical dimensions/component multisets and strict family support, while varying placement and colors |
| Other general scenes, odd indices | 9 | Preserve every remaining original profile; rich scenes already provide global-tie cases |

This intentionally concentrates training on the witnessed distinctions. The 27.5% scheduled public-family allocation exceeds the declared 25% strict-family floor, but measured random gate fractions, exact-profile counts and envelope counts are reported separately in the final battery. A profile-floor exact hit means the joint tuple of height, width and distinct-color count; it does not mean a byte-identical canonical grid.

## D2 — Reverse two intermediate choices using actual failures

An intermediate attempt forced literal canonical replays to increase profile support. Inherited diversity tests failed at 282/300 and then 287/300 unique inputs. This was unnecessary: canonical-profile tuples and component-family support can be maintained by varied nuisance draws. Forced replay and a subsequent seed-specific replay adjustment were removed. These failed logs remain in `checks/teaching-preserved-behaviors.log` and `checks/teaching-full-task.log`. Exact public overrides remain available deliberately.

The first fully green eight-rival candidate, version 3.1.0 at `a36a0ee107846ac05d9f819cf122516021202444ce3db3fa0bc43e9c3dfc1e06`, exposed a new shortcut under independent review. Its rich inputs chose the largest numeric tied color. A highest-numeric tie rival therefore fit demos 0–2 at seed 0, medium, but predicted `[[7]]` on query 3 instead of `[[1]]`. Actual Racket verified all four labels. This rival fails one of the five canonical examples, yet remains a genuine generated-lesson failure; canonical-fit screening alone would miss it.

The final version 3.1.1 uses three colors tied for the minimum global population, with the selected color numerically between the other two, plus a fourth more frequent color. The common color is chosen independently from four sampled colors; it is not pinned to a fixed numeric rank. The selected ring appears before both other minimum-frequency colors, while a common object appears earlier. This single input refutes both numeric tie directions. All feasible anchors with enough later cells are considered, preserving spatial variation instead of forcing a corner.

The rich scene retains a detached diagonal cell of the selected color, an internal foreign color, holes, and a later tied color. Together these distinguish all nine declared rivals: singleton-only; smallest local component; first nonblack object; whole selected-color bounding box; masked component crop; last minimum-frequency object; lowest numeric tied color; highest numeric tied color; eight-connected crop. Only singleton-only is asserted to fit all five canonical labeled pairs.

The additional color populations need at most 69 foreground cells. Rich easy scenes therefore use 9–10 dimensions; medium uses 9–14 and hard 13–19. Other public/general profile sizes are retained. This is a measured support choice, not a claim that every validator-accepted size is produced by default.

## D3 — API and portable tests

Seed and sample index must be literal Python integers, not booleans, floats, strings or `None`; the sample index must be nonnegative. Seed magnitude remains unrestricted because the shared generation API accepts arbitrary integers. Unknown difficulty and override values remain errors. Explicit `scene_profile` overrides retain all original public/general choices. The selected-rule algorithm and existing semantic helpers were not rewritten.

The lesson hook now rejects malformed/nonliteral output grids before equality comparisons. This closes the independent review's small float-equality issue without changing the underlying task rule.

The inherited editable file under `tests/` had a fixed-depth canonical path and a private module alias, causing the portable test stage to fail before execution. It now uses `reviewer_support.find_root`, `canonical_path` and `load_selected_generator`. The archive-preservation assertion pins exact original `raw_code` bytes rather than incorrectly requiring historical one-line source formatting to match the active canonical multiline text. The active selected/canonical equality assertion remains exact.

The immutable-fixture instruction applies to a baseline task-root `test_generator_*.py` file, which this task does not contain. The existing `tests/test_generator_7944933e200f.py` is explicitly within the return validator's allowed task scope; it was not a frozen fixture. Shared tooling and test-discovery rules are unchanged.

## D4 — Parametric extension: proposed, unapproved prototype

One small parameter is suitable: `frequency_extreme` in `{minimum, maximum}`, default `minimum`. It preserves the original object roles, global counting, component selection, stable tie handling and unmasked crop. The maximum variant negates only the sort key; reversing a sorted list would reverse tie order and was rejected. The minimum instantiation exactly matches the existing canonical rule text.

The setting is selected once per episode. Demonstrations are executed first, both possible settings are checked against those demonstrations, and exactly the chosen setting must remain consistent before query construction/execution. Public JSON exposes only demonstration input/output pairs and query inputs. Program, parameter, seed, metadata and query labels stay in separately marked authoring evidence.

The runnable prototype lives in `workspace/parametric/prototype.py`, with usage and domain details in its README. The constructor has an independent local random stream and does not depend on repaired production internals. The finite evidence includes minimum at seed 1, maximum at seed 0, six demonstrations, two queries, one shared differing input and four semantic witnesses, totaling 30 actual Racket transformations. The source-bound final record is `checks/parametric/frequency-extreme-v2/private/manifest.json`. Earlier prototype failures and the superseded v1 record are retained.

Minimum program SHA256: `89116268dbf1746b792e3f5d1508d920d7e053dee7a11d1519fea6c426f055a8`. Maximum: `c9e12ff790f133228b3a65844783e7bcb8802d02786da7e92c36a25e38cbd08b`. Source bytes and bridge/prelude hashes are pinned in the manifest. Only the outer controller registration wrapper is removed when applying the unchanged lambda through `RacketBridge`; the callable hash is recorded separately.

The two arbitrary-input domains can differ because each setting requires its own selected box to be smaller than the input. For example, an otherwise solid 5×5 color-2 grid with a central color-3 cell passes minimum and fails maximum. The constructor explicitly checks the intersection of both domains. The README and metadata were corrected after independent review; this clarification does not change any generated episode or emitted Racket.

This compact two-setting prototype establishes finite execution and parameter identifiability. It does not establish broad diversity, all-grid correctness, exclusion of unrelated shortcuts, a production parametric API or training approval.

## D5 — Evidence, reusable tools and honest limits

`workspace/reproduce_teaching_gap.py` accepts a selected or retained source and reproduces the original seed/index lesson. Its Python labels are explicitly named `mirror_output`; Racket authority receipts are separate. `workspace/evidence_archive.py` preserves large evidence as deterministic gzip files with original paths, byte sizes and SHA256 hashes, supports verification/restoration, and does not delete originals. The final source patch also includes the isolated prototype and focused regressions.

The complete after battery, explicit portable task tests, 100 lessons per band and all 40 fixed-seed starting residues are required evidence. Production and rotated-query verdicts are separate; the final brief reports actual denominators and unique input counts. Fixed-seed enumeration establishes only the declared period at seed 0 across the three bands. It does not exhaust every seed or every admissible input.

Self-review: the rich constructor concentrates on ring-shaped witnesses and uses a median numeric color among three tied minima, so it does not prove arbitrary-color or arbitrary-shape induction. Public/general profiles and explicit overrides retain broader behavior, both numeric-extreme rivals are now tested, and the final claim remains limited to the nine declared rivals rather than all possible programs.

The validator/mirror accept lawful inputs through 30×30, but hard general/rich scenes use dimensions 13–19 and public-family scenes retain canonical dimensions. The prototype's shared constructor is compact. Audit-only defects remain open for their owners. Masked solve correctness is withheld and unknown; earlier exposure is honestly recorded. Neither passing checks nor accepting this canonical repair changes training approval or approves the proposed variant.

Large retained evidence is restored using `checks/compressed/MANIFEST.json`; summaries and failure logs remain directly readable. The fresh-return replay uses the official runtime closure and reports its partial extraction scope. Focused tests run in that fresh copy's own environment, after verifying the applied source hashes; patch replay alone is not called a test pass.


## Curriculum assessment

The canonical task composes object extraction, global counting, stable selection and cropping inside one fixed transformation. It is not evidence of arbitrary cross-task program composition. The min/max extension is a parameterized family with one rule fixed per episode, not a per-pair hidden switch. Transfer to unrelated shapes, larger default grids or undeclared hypotheses remains unknown. No extra approval or broad curriculum annotation is inferred from the finite checks.
