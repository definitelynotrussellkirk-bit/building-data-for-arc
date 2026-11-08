# Current account: cfadc43e5098

## Intended rule

Treat each nonzero monochrome 4-connected object as its bounding box. Bridge two same-color boxes when they are separated horizontally or vertically, overlap on the perpendicular axis, and have equal midpoint sums on that axis. Paint cyan 8 across the full facing-edge gap and the *interior* of the overlap. A third **same-color** bounding box intersecting that bridge suppresses it; a different-color box does not.

The selected canonical Racket authority and the Python mirror are unchanged semantically. The selected `target_code` fields in the training and augmented solution records were synchronized to the exact canonical `program_solution`; archival `raw_code` was preserved.

## Distribution decisions

The generator retains four exact public families and eight general profiles at canonical 25–30 square scale. Each general profile now places a differently colored 3×3 rectangle inside an otherwise unblocked bridge. This is overwritten by the intended rule and refutes the strongest canonical-fitting rival, “any intersecting color blocks.” The 12-profile schedule interleaves public and general profiles so every cyclic four-pair lesson, after any one holdout, has at least one refuting demonstration.

Strict API behavior now rejects bool/non-integer seeds and sample indices and rejects negative sample indices. `scene_profile` remains the only supported override.

## Retained prior-review evidence (not rerun in this return)

- Portable task-local repair tests: 19/19 (`checks/new-tests-final.console`).
- Final 300-lesson census: 0/300 ambiguous production lessons and 0/1200 ambiguous query rotations (`checks/lesson-census-final-3.summary.json`).
- Exact shortcut witness: `checks/shortcut-witness/witness.json`; the Racket and rival outputs differ by 40 cells.
- Full period semantic enumeration: `checks/after-final/` (the earlier explicit receipt remains in `checks/semantic-after-enumerated/`).
- The frozen legacy fixture still has a non-portable fixed-parent path and cannot be edited under this assignment; official task-test preflight is therefore an inherited blocker, while the new portable tests pass.

These checks refute the declared `any_color_blocks` rival only; they are not a proof against every possible hypothesis. The public profiles themselves do not distinguish blocker color, so the general profiles and lesson schedule are required teaching evidence.

## Proposed parameter extension

`workspace/parametric/` contains a separate two-value prototype `blocker_policy ∈ {same_color, any_color}`. `same_color` is the canonical default. Both settings materialize exact Racket text and private 2-demo/4-query episodes; this prototype is not an approved production rule variant.

## Current prototype export correction: version 1.1.0

Assignment `review-09488583837b67e1` corrects the separate prototype's public writer and analyzer. Public files now contain only train/test data; filenames hash the exact shared-helper bytes, including the final newline. A complete preflight rejects duplicate visible challenges before creating an output, existing destinations are refused, and the public batch is written in sorted content-ID order. Private settings, seeds, programs, cached IDs and query answers cannot affect a public artifact while its visible content is fixed.

The analyzer filters the two policy settings using demonstration labels only. It accepts multiple survivors when their query predictions agree, rejects mismatched true-rule labels separately, and validates independent demo/query counts and distinct inputs. Each count supports 1–16 with a combined limit of 24.

Fresh verification on the final prototype: 21 focused tests passed (16 new regressions first failed on the old implementation). Seed 17 produced both settings with two demonstrations and four queries each: all 12 labels came from the exact Racket programs, every episode had six distinct inputs, and the demonstrations distinguished the policy for every query. The full batch and command receipts are in `checks/parametric/`; `workspace/parametric/evidence/manifest.json` binds current source, tests, programs and the compact complete episodes at `evidence/private/export-v1.1.0.json`. Old examples and reviewer-reported batches remain historical.

Canonical generator and rule semantics, production interfaces and approval/admission records are unchanged. This is a proposed bounded two-policy prototype; the checks do not cover all possible puzzle hypotheses. No production battery, prior 300-lesson census or frozen legacy fixture was rerun. The inherited fixture portability issue remains outside this prototype-only correction. The next useful action is owner review/import of this source-bound delta; variant approval remains a separate decision.


## Current public-export finding resolution

The earlier public-export finding is resolved only on prototype `c2801f6bf81741e5bd936f9d527a8260e7356353a33b450efa072e806b08a7da`: visible-only public IDs and public-ID-sorted emission are now present. 21 focused tests and two 2-demo/4-query Racket-backed settings reported pass; owner statically confirmed preflight then separate sorted(public_records) write pass. Exact old source and the original owner capsule remain under `generators/cfadc43e5098/evidence/parametric-external-followup-597e2d03726aa4c9/historical`; the owner inventory points to those same old bytes. Other audits/frozen-fixture limits remain unchanged and rule variants remain proposed. Source-bound decision: `generators/cfadc43e5098/evidence/parametric-external-followup-597e2d03726aa4c9/manifest.json`.
