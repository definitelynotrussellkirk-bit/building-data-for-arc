# Working notes: 41851e57e1a5

## Current design, version 3.0.0

The canonical Racket rule is unchanged and pinned by `RULE_HASH =
"b8f48f4e78e4"`. It takes the inclusive intersection of the global red(2) and
blue(1) bounding boxes, and fills that entire rectangle with the first
non-{0,1,2} color in row-major order on a blank, same-size canvas. The authored
input domain keeps one connected shape per fixed role, one isolated key cell,
and a nonempty bounding-box intersection. Arbitrary disconnected objects,
multiple keys, and empty intersections are outside this generator's domain,
even though the Racket function has behavior for some of them.

## Reproduced defects in version 2.0.2

The baseline's three/four-cell restriction rejects all four canonical training
inputs, whose shapes include five cells. Its four fixed orientations produce
only singleton or length-two intersections. The canonical length-three line
and two-dimensional full-area witnesses have no support. Six advertised
style controls are unused or unobservable. Unknown controls are silently
accepted, and the canonical size/palette profile has no default support.

Three retained baseline lessons expose teaching failures despite correct
labels. At seed 0, indices 0..2 have singleton targets; `corner_only` agrees
with every demonstration and fails the length-two query at index 3. At seed
8, `occupied_only` agrees on the demonstrations but misses the previously
blank query cell (6,6). At seed 42, all three demonstration keys are 3;
`fixed_key_3` fails the query with key 7. `workspace/probe_lessons.py` retains
these exact inputs and source identity; it does not depend on an external
review directory. Review evidence also records actual Racket outputs for
these twelve inputs, all five canonical inputs, and a literal 3x3 empty-area
witness. No prior return was used as measurement of this source.

## Distribution and teaching choices

Every consecutive three sample indices contain two rich examples and one
compact example. Rich examples use opposite connected Ls with optional
inward teeth, D4 orientation, color-role exchange, and translation. Their
bounding-box overlap is at least 3x3 and contains an empty interior cell.
This distinguishes full rectangle filling from a corner, perimeter, or
occupied-cell recoloring. Rich keys are isolated, outside the overlap, and
away from the upper-left corner. That last condition distinguishes the
`upper_left_key` shortcut that fits all canonical pairs.

Compact examples use six normalized geometry motifs, including canonical
four/five-cell shapes and a small area-fill extension. Rotation/reflection,
role exchange, placement, and key color vary. They supply singletons, both
orientations of length-two and length-three lines, and a 2x2 intersection.
They use canonical canvas profiles 8x8, 8x9, and 9x9 by default. These are
shape templates rather than a sampler for every connected polyomino; the
limited shape grammar is an intentional, remaining distribution restriction.

The default key is `3 + (seed + sample_index) % 7`. Three consecutive
demonstrations have distinct keys. A bundle of four consecutive pairs retains
at least one rich example and multiple keys after holding out any pair.
Those properties refute all fourteen declared rivals in the retained tests.
The guarantee concerns three demonstrations, one query, consecutive indices
with a common seed and difficulty, and default controls. It does not cover
arbitrary subsets, independently overridden pairs, or undeclared hypotheses.
The production census separately checks the actual materializer and retained
query rotations; the task probe covers twelve consecutive start offsets.
Finite rival checks do not prove unique induction of the intended rule.

## Controls and compatibility

The only exact controls are integer `grid_h` and `grid_w` in 8..20 and
integer `key_color` in 3..9. Omitting a control uses the schedule-aware
default. Explicit `None`, booleans, floats, strings, and out-of-range values
are rejected. Caller controls pass through typed GenCtx draws, and
`observe_overrides` measures their realized values on the returned grid.
The obsolete `palette_kind`, `palette_size`, `n_distinct_colors`,
`position_bias`, `density`, and `texture` controls are removed. Callers still
passing them receive a clear error and must migrate; the major version bump
makes this deliberate interface change explicit.

Difficulty affects rich canvas dimensions and overlap-size support: easy
uses 3x3 overlap, medium/default permit sides through four, and hard permits
sides through five. Compact geometry remains available in every band.
`strict_canonical_like` requires the canonical canvas profiles and four/five
cells per shape, in addition to the domain validator. It accepts all five
canonical pairs and rejects enlarged, otherwise lawful augmented examples.
The declared minimum strict fraction is 20%; the default three-step schedule
supplies one compact stratum per three draws. It is a measured support
criterion, not an alias for general validity.

## Self-review and limits

The two-rich/one-compact schedule introduces a size/profile correlation. The
key cycle also makes color predictable from generation provenance. Neither
is a proof against feature-conditioned or provenance-aware rival programs;
the recorded claim is limited to the named executable rivals and measured
assembly. Rich keys avoid (0,0), but compact keys may occupy that cell.
`max(nonzero colors)` equals the key throughout this single-key domain, so
numeric-rank selection is answer-equivalent here; this repair does not claim
to distinguish that equivalent algorithm or broaden to multiple distractor
colors. Red and blue remain fixed semantic colors.

Tests are in `tests/test_generator_contract.py`. The independent Python
oracle in the probe is checked against stored canonical labels and clearly
distinguished from actual Racket validation. Preserve the packet's native
after battery, portable task-test report, lesson census, exposure declarations,
and fresh replay receipt when accepting a return. Passing checks does not
change catalog training approval.
## Current reviewer considerations

Source SHA-256: `63afd378c86e85eab21af83120b4ae502271469f3fcb289ce68206ffa9be7224`.

# Design decisions

## Preserve the reference and authored domain

The selected canonical Racket implementation agrees with all five stored
pairs and the broader connected-shape witnesses. The failure is distribution
and validation, not the reference transformation, so no rule or shared
authority file was changed. Keep red=2, blue=1, background=0, one connected
component per shape, nonempty bounding-box overlap, and one isolated key in
3..9. Multiple keys and arbitrary disconnected objects would introduce new
semantic questions without addressing the reproduced defects.

## Separate lawful support from the compact canonical stratum

Remove the obsolete three/four-cell maximum. General validity admits larger
connected shapes; the strict predicate additionally requires canonical
8x8/8x9/9x9 canvas profiles and four/five cells per shape. This admits all
canonical pairs while keeping larger area witnesses explicitly augmented.
Declaring every lawful input strict would conceal distribution drift. The
declared 20% floor is supported by one compact draw per three indices; the
native semantic sample measures 207/600 strict inputs.

## Build examples that distinguish full-area filling

Opposite connected Ls create a controllable 3x3-or-larger box overlap while
their actual cells remain disjoint. Optional teeth, orientation, role exchange,
size, translation, and key placement add variation without losing an empty
interior cell. This creates direct counterexamples to corner-only,
occupied-only, and perimeter-only rules. Compact motifs maintain singleton,
line, and canonical-size support. Sampling all connected shapes would require
more rejection and make these teaching guarantees harder to check; it was
not necessary for this repair. The bounded motif/L grammar remains documented.

## Define the lesson assembly precisely

Three demonstrations and one query use a common seed/difficulty and consecutive
indices. The profile sequence is rich, rich, compact, repeating with period
three. Any four consecutive draws contain at least two rich examples, so
holding out one leaves a rich demonstration. Default keys have period seven,
so every such set of three demonstrations has multiple distinct colors.
Together these properties refute the fourteen declared rivals for ordinary
order and every permitted single-query rotation. The production census and
task-local cyclic-window tests check the actual implementations separately.

Reject relying on random chance to occasionally supply a decisive example:
baseline seeds 0, 8, and 42 show that labels can be correct while demonstrations
leave a wrong query answer plausible. Reject treating a second inference
guess as a training-data repair. Reject calling an agreeing rival ambiguous:
the rival must fit all demonstrations and disagree on the held-out query.
Do not promote the finite rival result into a claim of unique induction.

## Replace inert controls and make the compatibility cost explicit

Version 3 advertises only `grid_h`, `grid_w`, and `key_color`. They are consumed
through typed draws and measured by `observe_overrides`. Explicit values must
be exact integers in their stated range; omitted values use scheduled defaults.
Old palette/style/density controls are rejected rather than silently ignored.
This is a breaking call-interface change and is the reason for the major
version bump. Difficulty influences rich dimensions and overlap sizes, while
compact support remains present in every band.

## Keep evidence routes distinct

Racket supplies native check/census labels. The independent Python probe is
faster and enumerates cyclic starts; it cross-checks canonical labels but does
not claim to execute Racket. The retained 18-input reference application binds
the three baseline teaching failures and the hand-built area witness to actual
Racket behavior. Probe completion and semantic success are separate states.
The overlapping-window probe and unique-input census denominators are reported
explicitly. No broad repository pytest run is claimed for this scoped packet.

## Preserve integrity when the archive does not fit

The initial full extraction failed from inode exhaustion. Only regenerable
source-backed bytecode caches and this task's incomplete extraction were
removed; user source and evidence were not discarded. The original archive
and complete manifest remain unchanged and were streamed for hash verification.
Main and audit seeds were saved once before target selection; native draws
used those seeds and were never rerolled.

The final delta is produced by the packet's unchanged `_diff` and `_allowed`
helpers and tested in a fresh task-scoped extraction. The full native builder
was permitted to fail at its original missing-source guard. A recovery ZIP
preserves completed work and provides a capacity preflight and full-extraction
finalizer for a suitable environment. It is not relabeled as an official
return, and no private solve labels, symlinked predecessor sources, modified
guards, or fabricated intake attestations are used.

## Remaining limitations

The rich/compact sequence correlates morphology with position. Canonical-like
means the stated dimensions and shape sizes, not exact canonical motif identity.
The singleton-key domain makes numeric maximum an equivalent way to select
the key; that equivalent algorithm is not claimed to be refuted. Arbitrary
independent per-pair overrides, nonconsecutive subsets, new distractor colors,
and undeclared feature-conditioned rivals need separate assessment. Both solve
query labels remain unknown to the reviewer, and catalog approval is unchanged.
