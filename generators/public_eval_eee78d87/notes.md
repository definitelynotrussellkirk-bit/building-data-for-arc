# eee78d87 — motif extraction and periodic texture, authoring v1.0.0

## Current rule and deliberate extension
The three supplied training pairs and one supplied test-gold pair recover the tight
non-orange bounding-box motif, repeat it over a 16×16 canvas, recolor foreground
in the central two-by-two motif copies to maroon (9), and recolor remaining
foreground to black (0). Orange (7) remains background. Both general Racket and
Python implementations match all four labels; no supplied grid/answer lookup is used.

The official data only establish 6×6 inputs with 3×3 motifs. For generated inputs,
this family explicitly extends output size to (2H+4, 2W+4), centers the two-by-two
highlighted region, and allows different crop sizes. That extension is a design
choice, not a uniquely established consequence of the original examples.
The alternate `tiling=alternating_mirror` reflects odd tile rows and columns;
`tiling=translation` is the exact default reference. The floor/modulo convention
also applies to tile coordinates before the centered origin.

## Sampler and dependency
Both settings share exactly the same inputs. Support is 2–6 prefix-stable
demonstrations and 1–4 prefix-stable queries; the entire four-query bank is
independently shuffled before taking a prefix. A single-query public view contains
only demonstrations and the currently requested input. The 13×13 stress input
contains a substantive 10×10 mask and produces 30×30 output.
A recovers the crop, period and centered origin. B consumes those values to tile,
reflect and highlight. The retained protected-Racket counterfactual replaces the
crop with the whole padded input and changes the final grid.

## Decisions and repairs
Author review found that the original ordinary wrapper returned episodes instead
of following `generate(seed, sample_index, *, difficulty=None, **overrides)`.
Ten regression failures across the two homes were retained before the repair.
The wrapper now returns one canonical input, has observable size bands, rejects
invalid controls, and works after relocation without predecessor files. The
native adapter remains separate and self-contained within `workspace/parametric/`.

## Verified scope
47 task tests pass; the combined two-home suite passes 96 tests. The 32-seed,
two-setting audit covers 64 episodes, 1,280 supported prefix combinations, 256
one-query views, 512 finite-rival comparisons and 232 protected-Racket executions.
Eight named rivals have no dangerous survivor in that bounded census. This is
not a proof against every possible shortcut. The authoring preflight passes for
both settings, seeds 17 and 43, two demonstrations and four queries, and all four
original labels. Its 155 current source entries are bound to the causal witness;
the bounded audit independently binds 13 task files including rival resources.

## Reproduction and next owner action
From the repository with the packet's protected Racket environment, run
`python3 -m pytest --import-mode=importlib -q generators/public_eval_eee78d87/tests`.
Use `workspace/parametric/audit_native.py --seeds 32 --racket-seeds 2 --out FRESH`
for the finite audit and `authoring_witness.py --preflight PREFLIGHT --recipe
RECIPE --out FRESH` for fail-closed causal replay. Exact commands and retained
receipts are in return RESULTS.json and checks/public_eval_eee78d87/.

Reviewer-ready, owner-pending. Catalog-backed staged checks return “Unknown
puzzle” until owner registration; no catalog/runtime bypass was made. Register
provenance, review the explicit size extension, reconcile any overlapping work,
then run fresh native qualification and owner acceptance. No training admission
or measured training benefit is claimed. Final review was author self-review.
