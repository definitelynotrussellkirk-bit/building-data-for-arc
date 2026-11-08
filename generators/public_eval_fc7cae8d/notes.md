# Framed-picture orientation: current authoring decisions

## Rule and scope

The supplied parent has one interior connected picture with two adjacent,
one-cell colored side bars. The bars' colors identify two adjacent sides of the
outer canvas. Remove the bars, then apply the unique rotation or reflection
mapping both inner sides to their corresponding outer sides. Preserve every
picture cell, including black notches. All three training labels and the
provided test gold will be executed through the new general Racket reference.
The immutable public-parent provenance is retained. This is unapproved public
creation; owner registration, source review, native qualification and acceptance
remain separate from authoring preflight and training admission.

The admitted grammar has one nonzero four-connected component not touching the
canvas edge, two distinct reserved marker colors on adjacent complete inner
bars, and unique dominant canvas sides for those colors. Their missing shared
corner is zero. Marker and other outer-frame colors are absent from the picture.
An outer edge can contain a small spill from a neighboring marker: the official
test requires this. The picture is a rectangular crop, not its nonzero support.

## Design and implementation plan

Using the packet's own task notes and check receipts for the plan and progress;
the fresh extraction is isolated and contains no Git repository.

- [x] Author `reference.rkt` and `workspace/parametric/native_family.py` after
  focused tests: independently parse the frame, identify its D4 transform, and
  preserve the full picture. Check every supplied label and all ordered adjacent
  marker-side mappings, strict types and malformed-frame rejection.
- [x] Build a standalone `generator.py` and a deterministic native `sampler.py`.
  Two distinguishing demonstrations precede four optional demonstrations. Four
  novel queries cover the smallest lawful profile, rectangular intermediate
  cases and a substantive 30x30 canvas. Finish each bank before independent
  prefix selection; never use a sibling workspace or global random state.
- [x] Add a thin adapter and promotion contract with episode-fixed
  `marker_pairing=match|swap`, default `match`, 2..6 demonstrations and 1..4 query
  prefixes. `swap` exchanges which outer marker color each inner bar must match.
  Inputs remain exactly matched across settings; asymmetric pictures expose the
  difference. The canonical setting returns the exact reference bytes.
- [x] Self-review finite competing orientations, one-marker rules, incorrect
  crops and notch filling through protected Racket. Repair any demonstrated
  demo-fitting/query-conflicting rule before authoring preflight.
- [x] Run public authoring preflight, protected causal replay, and strict
  one-query public projection checks. Bind current source hashes and retain
  every actual check receipt before starting the second assigned parent.

Approach chosen by the reviewer: reconstruct the two-color frame explicitly.
A fixed rotation cannot explain the supplied reflected outputs. A crop-and-fill
rule changes supplied black cells. General D4 alignment is both faithful to the
parent and reusable on freshly generated pictures.

## Sequential dependency

A extracts the framed picture and derives the unique side correspondence from
the two inner bars and the outer marker distribution. Its input-dependent
intermediate is the picture crop plus the D4 side mapping. B applies that mapping
to the picture. Omitting alignment or supplying the wrong frame correspondence
changes the final output; protected witnesses will retain both executions.

## Review focus

Reflections as well as rotations; corner spill on a noisy outer edge; preservation
of zero notches; independent demo/query prefixes and matched settings; strict
source-bound, single-query public serialization. Finite rival checks do not
establish uniqueness against arbitrary programs or downstream learning benefit.

## Concrete findings and decisions

The reference reproduced all four supplied labels, and protected execution
checked all 128 ordered adjacent frame/setting mappings. The current input parser
preserves the official test's corner spill; literal uniform-side validation
would incorrectly exclude that parent.

An arbitrary-index sampler regression at seed 76 / index 6 exposed a disconnected
payload corner after two neighboring edge notches. Such orphan corners are now
absorbed into the notch, preserving the connected scaffold.

Independent protected review found that seed 9 / match taught only a reflection
and a half-turn. Their inverse transformations fit both demonstrations and
disagreed on a quarter-turn query. A corresponding swap-setting gap occurred at
seed 43. The first demonstration now uses an axis reflection and the second a
quarter-turn; swapping the correspondence exchanges those roles, so both settings
refute the inverse. Both first demonstrations also have identical canvas and
picture dimensions to remove an aspect/dimension cue.

A further protected audit found eight setting-specific failures of first/last
edge-sample rules: these fit the old demos and disagreed on queries. The first
teaching scene now deliberately places misleading first, last and middle samples on the
opposite sides while keeping each color's true side dominant. The full frame
correspondence remains well-defined. Historical failing inputs, both executed
programs, and labels are retained under `checks/public_eval_fc7cae8d/independent-audit/`.

The base generator uses the shared keyed random context, declares the real bounded
`max_frame_depth=1..3` override and validates its input grammar in `self_check`. These are
the owner's portable base-generator requirements, independent of the native
adapter's authoring checks. Its current static lint reports zero errors and
warnings, and the focused sampler/contract suite has 47 passing tests. The final source-bound audit and authoring preflight pass; current evidence
is listed below. Earlier passing source hashes are not reused for changed bytes.

## Current reviewer-ready evidence

Final task suite: 92 passed. Core audit: 128/128 demo-refuted comparisons; independent
audit: 220/220 demo-refuted comparisons, zero query conflicts or execution errors.
All four original labels and four authoring-preflight jobs pass. Maximum seed/count
probe executes 20 labels. Two protected causal cases replay; 16 single-query views
verify, with four corrupted bundles rejected and original bytes unchanged.
Current reports are `checks/public_eval_fc7cae8d/native-tests-final.xml`,
`audit-final/audit.json`, `independent-audit/frame-rivals-v2.json`,
`boundaries-final.json`, `preflight/`, `causal/` and `public-probe.json`, all under
that same task check directory. The assigned shortcut question is answered by
`checks/public_eval_fc7cae8d/question-generator-shortcuts.json`: the first-edge
sample rival fits all three official demonstrations but fails the current first
generated demonstration at seed 17. Both outputs were executed in protected Racket.

Status: reviewer-ready authoring prototype. Owner registration, source review,
native qualification and fresh acceptance remain pending; training is not admitted.

## Current private repeated-parent reconciliation

Retain exact accepted match/swap programs and both constructors. Original incoming seal_top cannot decode some current marker palettes/outer edges (protected modulo #f failure). Preserve original incoming program as provenance; active seal_top composes its post-orientation top-connected zero filling with current generalized decoder. No current program replacement. Matched two-demo lessons distinguish all three settings; query constructor alternates by seed. Candidate native qualification and fresh acceptance were exercised in this isolated library; root publication remains separate. See evidence/repeat-next-union and the current private qualification receipt.
