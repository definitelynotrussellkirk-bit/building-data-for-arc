# Postrepair visible-only solve work log

## Phase, preparation, and exposure

This is the separate postrepair solve in WORK/solve. The completed blind lane
is left unchanged. The parent reviewer prepared this challenge before this
agent began, reporting exit 0 and final source SHA
ff79193bed2cc537c82a56abd6235304e2f2fb791eda67050b68bb84b048f328.
Preparation evidence is WORK/checks/postsolve-prepare.receipt.json. I did not
run prepare again or open generator files to verify the parent-reported hash.

The reviewer/root has already seen the authoring rule during repair, so this
phase must record --earlier-exposure yes. This solving agent has not read the
main generator, Racket rule, reference solution, canonical data, or private
labels. My conversation context contains my earlier blind phase and its
example-derived inferences, but I did not reopen prior solution notes or use
an authoring explanation. The present challenge is solved from its own public
README and challenge.json. During this phase, --reference-consulted remains no.
This is a concise work record, not a raw internal token trace.

## Current public observations

There are four visible training pairs and two masked query inputs. All
examples retain their dimensions, background color, and colored cell counts.
The visible inputs place filled squares at the four corners on a uniform
background of color 7.

- Training 0 has four one-cell squares of color 5. Each moves one row and one
  column inward, diagonally toward the grid interior.
- Training 1 has color 2 at three corners, with two one-cell squares and one
  four-by-four square. All three move inward: one cell per axis for the small
  squares and four cells per axis for the large square. The single color-8
  square stays at the upper-right corner.
- Training 2 has two four-by-four color-5 squares on opposite corners; both
  move four cells per axis. The unique color-2 and color-3 squares stay.
- Training 3 has two color-3 one-cell squares and two color-4 two-by-two
  squares. Both repeated colors move; each square uses its own dimensions.

## Candidate and rejected alternatives

Move a corner object when its color occurs in more than one separate object.
Translate it inward by its own height vertically and width horizontally.
Keep objects with unique colors in place. Preserve all colors and shapes.

Moving every corner object conflicts with the stationary unique colors in
training 1 and 2. Moving only the most frequent color conflicts with training
3, where both colors move despite different occupied-cell totals. A fixed
one-cell movement conflicts with the large squares. These alternatives were
rejected by reading the public examples; no failing implementation or failed
official check is claimed for them.

## Revision 1

Implemented a standalone solver using the modal background color and
four-neighbor monochromatic components. Count components per color, determine
the object's own bounding-box dimensions, and shift repeated-color corner
components inward by those dimensions. Original locations are erased before
the translated objects are placed, avoiding dependence on traversal order.

A public-data probe, probe_corner_moves.py, prints each object's color,
size, bounding box, proposed displacement, and exact training comparison.
It prints predicted query cells without reading or claiming their labels.
The command runner run_with_receipt.py records exact public-command argv,
working directory, TMPDIR, timestamps, exit status, and combined output in
WORK/checks/postsolve-command-receipts.json and per-command logs.

All task commands run from /tmp/arc_review_121953_mount in the approved
namespace, with TMPDIR=/tmp/arc_review_121953_mount/tmp. No official solver
revision has yet been checked at this point in the log.

## Remaining uncertainty

The visible examples support repeated-color selection and size-dependent
inward movement. The masked queries have no provided expected outputs.
Their correctness must remain unknown during this phase.

## Public probe result

The recorded command `python3 WORK/solve/probe_corner_moves.py` exited 0.
All four visible training predictions matched exactly, with zero differing
cells in each case. Both query inputs produced predictions, but their labels
remain unknown. Evidence: WORK/checks/postsolve-public-probe.log and the exact
argv entry in WORK/checks/postsolve-command-receipts.json.

No source change followed this probe. Revision 1 is now submitted to the
official visible-only checker with this note: Revision 1: move colors appearing in multiple corner components inward by each object's own height and width; current public probe matches all four visible pairs.
