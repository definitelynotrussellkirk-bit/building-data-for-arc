# Working notes — review-5fa7fbe55f2eb5ca

Selected generator: `11ebef5b0986`, final version `3.0.0`.
Final generator SHA256: `3058ecb8478de8e7241d56a367b4c52da4402501662a6a961492ff78fc430d03`.
Canonical Racket SHA256: `fb5b12ff981f492cb40ea9138fc8b1bb89fcb75b16e3602ceb6327feb7645f1e`.
Canonical ledger SHA256: `08f88dbbda5279692992bc90a689c7b5cc6d426832557708666ecf8532146e41` (unchanged).

## Decisions carried forward

M1: The imported palette excluded canonical gray 5 and canonical dimensions were incompletely represented. Restore 2..8 and canonical-scale shapes, but keep role colors 0/1/9 fixed and palette length exactly three. Historical rationale for excluding gray is unknown.

M2: The old small rooms and shallow insets left fixed-canvas clipping and a seven-step cap indistinguishable from the rule. Deep insets and corner-seeded large rooms expose these rivals without introducing a new object grammar. Schedule witnesses in three-example lessons rather than merely hoping a random batch contains them. The exact imported geometry bounds had no retained rationale beyond the summary.

M3: Remove advertised no-op/constant axes, honor all remaining overrides within their declared domain, reject unknown keys and malformed grids, and validate the entire legend/frame/seed grammar. Do not weaken validation to admit arbitrary stray colors or broken walls. The declaration changes are intentionally versioned as a major version.

M4: Keep Racket behavior fixed. Synchronize only a redundant comment in the selected base authority; do not edit the canonical ledger, unrelated tasks, catalog approval, or shared runtime.

M5: An intermediate candidate repeated canonical-scale scenes across difficulty bands. A failing distinct-input regression exposed this despite a green standard battery. Key the palette RNG by difficulty. The final census rose from 492 to 886 unique scenes out of 900 draws; witness counts were preserved. These are input counts, not independent lesson counts.

## Evidence and useful tools

The compact review return includes `checks/evidence_index.json`, full before/intermediate/final logs, exact JSON counterexamples, solve attempts, reports and source patch. `workspace/review_probe.py` stages actual Racket and reports exact source hashes, sample manifests, unique inputs, overlapping windows and concrete rival disagreements. It accepts either canonical single-dict or list encodings of `test`. `workspace/audit_probe.py` reproduces findings for the two audit-only tasks; it makes no edits to them.

Main verification: 57 task-local tests pass; 12/12 battery stages green; final 900-draw Racket census has no failures. The unrelated root suite had 169 passed and 1 failure: an unchanged timeout test assumes the child prints within 0.2 seconds, whereas this environment's ordinary Python startup took 0.42..0.45 seconds to first output. Its isolated failure and normal versus `-S`/longer-timeout diagnosis are retained; do not describe the entire repository suite as green.

The fresh solve phase used only visible examples, with earlier rule exposure explicitly declared. One revision matched 3/3 visible demos and nine visible/metamorphic probes. Hidden-query labels remained closed and correctness is unknown; no training admission or blind-solve claim.

## Next maintainer action

Apply the source patch to the matching packet baseline, rerun the explicit task tests and final battery, then independently score the retained masked-query predictions. Review the two audit targets separately: canonical overlap coverage and ignored minimum height in `d414585aa873`; control-rotation lesson ambiguity and an absent-anchor validator hole in `4199aa353fa1`. Do not silently promote those tasks or this task to approved from this review alone.
## Current reviewer considerations

Source SHA-256: `3058ecb8478de8e7241d56a367b4c52da4402501662a6a961492ff78fc430d03`.

# Decisions and compact handoff

Assignment: `review-5fa7fbe55f2eb5ca`; task: `11ebef5b0986`.
The source identities and denominators in `REVIEW.md` / `checks/evidence_index.json` apply throughout this document.

## M1 — Restore demonstrated support, not arbitrary novelty

The old summary specified three legend colors from {2,3,4,6,7,8}, small canvases, one blue frame and one maroon seed. The reason for excluding gray 5 is **unknown**; a canonical example uses it. The reason for the precise historical height/width bounds is also **unknown**. Those exclusions were not treated as authority over demonstrated cases.

Use all palette colors 2..8, keep them distinct and ordered, and include canonical-scale shapes. Preserve exactly three colors and the legend's row-0/columns-1..3 convention: variable-length or relocated legends would change the teaching problem without a canonical requirement. Preserve role colors 0/1/9 and a single closed rectangular chamber. Do not globally permute blue/maroon/background roles, introduce distractor colors, or copy stored input/output pairs into the generator.

Warm and cool palette overrides now select actual different pools. A varied palette explicitly contains 5; this is a documented coverage profile, not evidence that 5 has a special output role. Slot 0 uses that profile so any ordinary three-demo window includes the formerly missing color. Final gray frequency is 563/900, not a claim of a uniform palette distribution.

## M2 — Expose the frame and unbounded periodic rule

A rival can reproduce all canonical pairs by ignoring the actual wall extent and clipping rays to rows 2..h−3 and columns 2..w−3. Another reproduces them by stopping at distance seven. Both also reproduced all 900 baseline generated outputs. This is a distribution defect even though ordinary generated input/output pairs are individually valid.

A shallow inset merely moves the wall onto the rival's last paintable cell, leaving no paintable blank outside it. The repair chooses a side and a margin of 3..5, constrained by canvas dimensions. That creates a genuine blank stripe beyond the real wall but inside the rival's false chamber. The frame remains one closed rectangle; no concave wall or obstacle semantics are introduced. A second profile uses a corner seed in a room large enough for distance-eight-or-longer paint, refuting the seven-step cap without altering the palette cycle.

Random mixture alone was rejected: globally present witnesses can still be absent from a short lesson. Use sample-index slots 0/1/2 for canonical-scale/gray, deep inset, and long ray. Any consecutive ordinary three-demo window contains each slot. Difficulty affects the long-ray room defaults; seed, palette order, chamber side, dimensions and seed position still vary. The finite rivals are explicit callable diagnostics, and `lesson_identifiable` checks them against demonstrations before deciding whether an unresolved rival changes the query.

This does **not** identify the intended rule among all possible programs. A future rival beyond these two can survive. An overridden small canvas or forced frame mode can deliberately remove a witness, so the guarantee applies only to the unoverridden consecutive schedule. Do not weaken the statement into “all possible episodes are identifiable.”

## M3 — Truthful controls and complete grammar

Keep only `grid_h`, `grid_w`, `frame_mode`, `seed_pos`, and `palette_kind`. Remove inert/constant advertised controls and invalid-input texture knobs instead of simulating effects unrelated to the rule. Unknown override names fail early. Explicit size overrides use the full 7..16 by 8..16 declared domain for every difficulty; difficulty is not a silent restriction on the caller's legal range. Noninteger and boolean dimensions are rejected. All combinations of the remaining declared axes are supported.

The validator checks rectangularity, integer ARC colors, exact legend placement and membership, a single closed hollow blue rectangle separated from the canvas edges/legend row, exactly one seed strictly inside it, and no stray body colors. Broken walls, duplicate seeds, illegal legends, malformed grids and missing structure are negative cases, not new valid generation modes. The diagnostic arithmetic mirror is independently structured from Racket's directional stepping but remains **test-only**; the production label source is Racket.

The public control change is deliberate and reflected by the major version increase. Consumers using removed no-op axes must remove those overrides; silently accepting them would preserve the original defect.

## M4 — Cosmetic authority synchronization only

The imported bound base JSON contained a redundant line comment in `racket_target.target_code`, absent from the same file's `raw_code` and the canonical text. The unmodified canonical rule already matched stored outputs. A new test demonstrated the exact-source discrepancy. Delete only `;; Position of the first color 9 cell` and retain the rest of the JSON byte-for-byte. `checks/authority_comment_sync.json` binds before/after file hashes and records all other fields unchanged.

Changing canonical semantics or relaxing the authority gate was rejected. Exact synchronization makes independent intake simpler without asserting a behavior repair that did not occur. No catalog approval or shared code change was made.

## M5 — Measure actual scenes, not just requested draws

The first repaired candidate passed the standard battery but reused many same-seed canonical-scale scenes across difficulty bands: 492 unique inputs among 900 draws. A targeted regression showed only 20 unique scenes among 60 selected cross-band anchor draws. Key palette randomness by difficulty while retaining the intended common canonical geometry. The regression and the final 57-test suite pass; final uniqueness is 886/900, with unchanged 300 fixed-frame and 345 long-ray witnesses and 780/780 refuting windows for each rival.

Cross-band independence is improved, not guaranteed. Fourteen duplicate draws remain in the measured finite sample. We did not add a global cache or rejection machinery merely to force perfect uniqueness; that would alter deterministic indexing and create hidden state. Deduplication and overlapping-window denominators are explicitly retained in the reusable census.

## Reusable tools, evidence and rejected shortcuts in the review itself

`workspace/review_probe.py` stages the actual runtime and runs Racket for every reported case, rather than treating a Python mirror as ground truth. It records source/rule hashes, exact samples and outputs, finite-rival disagreements, unique scenes and overlapping lesson windows. It accepts both canonical test encodings (single dict and list); a 30-draw run on `4199aa353fa1` tested the dict case. An initial direct-import failure (`scripts.comment_solutions` missing) is retained; the tool was corrected to use the repository's real runtime staging. This was a tooling setup failure, not a generator semantic failure.

`workspace/audit_probe.py` provides concrete findings-only reproductions for both assigned audit targets. Do not import its rival behavior as a reference oracle or patch audit tasks under this assignment. Exact small witness JSONs carry generator/rule hashes, inputs, actual Racket outputs, rival outputs where meaningful, validator/domain status, commands and actual runtime locations. Contract-only failures use null rival outputs rather than inventing them.

The root timeout suite failure was investigated, not silently rerun until green: it failed both broadly and in isolation. A read-only 15-observation startup/timeout comparison identifies a 0.2-second test deadline shorter than normal startup in this environment. Shared runtime/test hashes remain identical to the packet. T1 stays an explicit remaining failure.

## Final state and next owner

The final generator hash is `3058ecb8478de8e7241d56a367b4c52da4402501662a6a961492ff78fc430d03`. `census_final_v2.json` and `final_v2/` supersede earlier candidate artifacts; all failed iterations remain available. The final generator was frozen before the visible-only solve, and no generator edits followed preparation. Earlier exposure is declared; masked labels were not opened and training was not admitted.

Independent intake should apply and verify this one-task patch, score retained masked predictions, and decide approval. Separate assignments should address A1/A2 and B1/B2; T1 is shared test infrastructure. Do not repeat this entire investigation or redraw the assignment: reuse the counterexamples, tests, exact command records and compact findings table first.

### Packaging constraint

The complete evidence initially exceeded the return format's 256 top-level members, not its 25 MiB expanded-byte limit. Keep the safety limit intact. Bundle only battery receipt/ok-marker duplicates, preserve all original paths/sizes/hashes in `checks/retained_receipts_manifest.json`, and retain every log and JSON report. `checks/RESTORE_EVIDENCE.md` gives a standard-library restoration and hash-verification command. This change is evidence layout only; it does not change the tested source patch or erase failed iterations.
