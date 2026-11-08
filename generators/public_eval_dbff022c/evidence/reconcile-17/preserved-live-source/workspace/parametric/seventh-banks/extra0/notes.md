# dbff022c — edge legend and enclosed regions

## Current rule and scope

The canonical rule reads the unique isolated dense two-line multicolor legend from the canvas edge inward: the outer row/column contains owner colors and the adjacent inner line contains fill colors. It finds four-connected zero regions that do not reach a canvas edge and have exactly one nonzero cardinal boundary color. Mapped regions are filled; unmapped regions, open contours, mixed-color boundaries, the legend and every existing colored cell are preserved.

The authored general Racket rule matches all three supplied demonstrations and the official test gold. A square 2×2 legend is resolved by its unique touched edge, not an arbitrary orientation convention. Legend isolation uses eight-neighbor foreground connectivity; cavity connectivity is four-neighbor. No supplied grids or answers are embedded in the implementation.

`fill_scope=all` is canonical. `largest_per_owner` fills all maximum-area cavities separately for each mapped owner, preserving every tie. It consumes an input-dependent per-owner maximum map rather than a global rank or colored-object size. The settings happen to agree on all supplied originals because repeated-owner cavities have equal area there; generated unequal-area examples distinguish them.

## Generated family

The ordinary generator uses GenCtx and declares `RULE_TASK_ID = 'ee_dbff022c'`. Its observable axes are owner_count 2–5 and legend_edge top/right/bottom/left. The native family supports 2–6 demonstrations and 1–4 queries, materializing a full six-demo/four-query bank before count prefixes. Query order is privately shuffled independently of source ordinal. Inputs are identical across settings for a fixed seed and count request.

Shapes include rectangles, diagonal diamonds, notched cavities, stairs, multi-chamber contours, repeated owners, unequal areas, and tied maxima. Each input also has an unmapped closed contour and a mapped open contour. The first two demos expose bottom/right legend direction and distinguish hole area from colored perimeter and global/first/last selection. The native model and ordinary input builder are self-contained copies; exact-input parity is tested. Black is the background; foreground palettes vary over colors 1–9. Legends and other foreground are separated by a full black moat, including diagonal separation.

The bounded sweep passed 664 distinct inputs, 166 at each owner count, with all four legend edges and exact ordinary/native input parity. Its 152 substantive 30×30 cases contain 112–175 nonzero cells and 47–113 mapped cavity cells. The constructor retains every requested hard contour and attempts bounded placement; failure is explicit if the unchanged contour set cannot be placed within 30×30. Finite sampling is not a universal placement guarantee.

## Executed current evidence

Evidence paths below are relative to WORK/checks/public_eval_dbff022c/.

- `family-tests-v2/`: 59/59 tests pass in the native copied checkout, with no staged source drift. The suite includes protected original labels, all eight dihedral transforms of the official test, and a literal per-owner maxima/tie/open/unmapped witness under both settings.
- `preflight/`: all four original labels, two ordinary base generations, and four native jobs (two settings × seeds17/43), with the minimum two demos and four queries. The preflight and inventory are unapproved authoring evidence.
- `rival-v3/summary.json`: 64/64 rival–lesson comparisons demonstration-refuted; 48 selected labels,128 rival demos and256 rival queries executed;432 protected executions, zero errors, wrong labels or harmful survivors. Every query executes after refutation. Full programs and predictions are retained.
- `inference/semantic-review.json`: a frozen independent Python oracle matches the four originals and68 generated/stress labels;13 tested rivals have no demonstration-supported query conflict. Its four-neighbor foreground discovery agrees on the documented eight-isolated legend domain, not every malformed input.
- `boundary-v2.json`:20 protected maximum-seed labels at six demos/four queries across both settings, including substantive30×30 inputs.
- `causal/witness.json` and `causal/replay.json`: an executed and independently replayed30×30 largest-per-owner case changes13 cells when owner-specific maxima are replaced by one global maximum. This binds the required geometry-dependent selection.
- `export/`, `public-probe.json`, `public-files-command.json`:16 single-query views; exact private answer pairing and first-turn/future-query invariance; four corrupted bundles rejected; all16 visible files pass structural checking.

## Findings and resolutions

- A fixed top/left table reading fits all three original demos but fails official test gold. Generated minimum lessons deliberately include bottom/right orientation.
- The initial palette call used a positional count for a keyword-only GenCtx argument. Both self-contained copies were corrected; final tests, sweep and protected execution pass.
- Initial Python legend discovery used four neighbors. A diagonal attachment regression exposed disagreement with the Racket eight-neighbor isolation rule. Both copies now use eight neighbors for the legend, retaining four-neighbor cavities.
- The new native public-task test snapshot intentionally has no canonical ledger. Earlier test helpers incorrectly relied on that ledger and could resolve the live checkout. Tests now bind their own staged root and load their own generator directly; the fresh59-test stage passes. Production behavior was unchanged by this test-only fix.
- Rival v1 was invalidated by an overlapping legend-source edit despite matching labels. Rival v2 and the first boundary report preceded the test-only portability correction. The current source-bound receipts are rival-v3, boundary-v2 and preflight; earlier receipts remain explicitly superseded.

No current finding remains in the reviewed scope. Finite examples and named rivals do not establish universal rule uniqueness. Owner registration, source review, native qualification and fresh acceptance are still required; training admission is not granted.
