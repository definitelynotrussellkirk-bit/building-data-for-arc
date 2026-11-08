# Current authoring state — public parent 71e489b6

Unapproved creation, reviewer-ready only after the accompanying final preflight/audit. Owner registration, source review, native qualification and acceptance remain separate. No training admission. All three supplied train labels and both supplied test-gold labels were used for authoring verification, not blind evaluation.

## Rule and scope

The canonical program identifies original-grid monochromatic 4-components. A component containing a solid 2x2 core is structural; a coreless component is a thin irregularity. Blue irregularities and blue tips with at most one cardinal blue neighbor are erased. Black thin irregularities and black tips surrounded by blue on at least three cardinal sides (or every available side at a canvas corner) receive an eight-neighbor orange outline. Defect cells stay black; outline painting follows blue removal. Detection must use the original input: removing blue first changes two cells in the second supplied test. A substantial black cavity and a narrow channel attached to it are not globally filled.

This is an explicit general interpretation consistent with all five available labels, not a proof of the unknown author's intention outside the observed/domain grammar. Solid 2x2 black regions are structural by contract; isolated coreless blue strokes are noise. Those choices should not be silently generalized to arbitrary binary art.

`all_rims` is byte-exact reference.rkt. `largest_rim` draws every rim, then retains the largest cardinal-connected orange component, with row-major ties, restoring other rim cells to the cleaned binary grid. Several small black defects may produce a merged winning rim, so selecting the largest original black defect is wrong. The witness is a real protected-Racket wrong-order execution, not an asserted label.

## Sampling and teaching

Two through six demonstrations; four independent stored queries (the native prefix API accepts 1..4, but public projection requires the complete bank). Matched inputs across settings. Keyed GenCtx scene RNGs are separate from the presentation RNG. Inputs cover 16..30 per side, minority-blue islands, majority-blue fields, thin channels, structural cavities, attached and detached blue noise, clipped defects, diagonal contacts, original-size queries and a substantive 30x30 query. Geometry varies across seeds; colors 0/1/7 retain the parent's semantic roles.

Self-review enlarged the initial sampler's coverage from large blue fields to original-sized and majority-black scenes. This exposed an eight-connected-rim shortcut: seed 4's old two demonstrations fit it, while query 1 disagreed. `regression-diagonal.json` retains that old lesson. The repaired second demo constructively contains three rims connected diagonally but not cardinally, without raising demonstration cost. The audit replays old and repaired cases with standalone Racket programs. A separate hand-derived count tie rejects bounding-box-area selection.

## API and privacy

Production `generator.py` returns inputs only, declares no override axes and rejects unknown controls. `self_check` is a binary/core/defect structural check, not a claim of exact sample-support recognition or uniqueness. Use the adapter for labeled parametric claims and protected Racket for authoritative verification.

`public_turn` shuffles the full bank by an independent presentation seed, then whitelists demonstrations and one input. It does not read settings, programs, hidden answers or future inputs. Filenames hash exact public bytes. The entire directory listing, source order and private manifests remain controller-only.

## Reproduction

From the packet root, run the focused pytest suite through `review.py run` with `--import-mode=importlib`, then `arcpuzzles.review_public_creation preflight public_eval_71e489b6`, then task-local `workspace/parametric/audit.py --preflight ... --out NEW --seeds 64`. The tool checks current hashes, rejects stale source, audits all supported demo counts, executes Racket labels and the causal witness, and tests the real public checker against a deliberately leaked answer.

All finite-rival results are bounded, mostly Python claims; Racket execution counts are separate. Author self-review, not an independent review. The earliest audit invocation was interrupted by the command timeout and is not a passing receipt. Superseded preflights/tests are development evidence; only final source bindings apply.

Final packaging caught a witness schema mismatch (full runtime identity in the minimal marker). The audit now preserves the full identity separately and invokes the frozen intake validator; a failing/passing regression covers it. Earlier audit and candidate-package records are superseded. Current source receipts use `preflight-release/` and `release/`.

Owner worker API correction: use the existing worker input/findings contract. Earlier author checks used the incompatible return convention. Reference programs are unchanged; owner preflight and native acceptance determine current readiness. See evidence/owner-base-api-repair.json.

## Current repeated-parent reconciliation

Preserve exact all/largest-rim and ordinary generator API with root bool-to-findings repair. Add exact smallest-rim program. Three demonstrations preserve incumbent first two and add an explicit order counterexample, rotated to defeat first-rim selection. Fixed counterexample has only four possible rotations; broader random query constructor remains unchanged. Retain incoming smallest-rim teaching scene source. Current evidence resides in evidence/repeat-fifth-union. Private native acceptance and root publication are separate.
