# 538503abef57 — current generator decisions

## Rule and domain

Racket rule hash `2fbbe9d88e5d` is unchanged. Each same-color 4-connected
component is anti-transposed inside its own square bounding box, retaining its
top-left anchor. Because the actual Racket code crops the entire input bbox,
this sampler leaves a blank row or column between whole bboxes. Colors may be
reused by separate components. Labels always come from the selected Racket rule.

The current sampler uses 8..16 rows/columns and connected shapes in 2x2 or 3x3
frames. Validation also accepts the three canonical inputs. It rejects malformed
cells, blank grids, non-square frames, wrong component counts and overlapping
frames. Square identity cases remain validator-lawful but are not default draws.
Rectangular frames are an intentional domain exclusion: the old claim that the
Racket transpose is undefined on rectangles was incorrect.

## Reversals from v1.1.1

- Rejection-grown 3..5-cell blobs → finite connected shape pools and constructive
  separated placement. The old validator accepted every destructive mutation in
  the baseline check; the new validator checks actual component geometry.
- Unread palette/texture aliases and fixed density/position descriptions → four
  exact pixel-observable controls: grid_h, grid_w, n_objects and total
  n_distinct_colors (including 0). Unknown controls now raise. Impossible count
  combinations are explicitly declared; all legal boundaries work in every band.
- No teaching contract → period-2 default curriculum. Core samples have two
  distinct-color 3x3 objects. Witness samples have three objects/two foreground
  colors, with an unequal-size repeated-color pair in opposite NW/SE quadrants.
  Every sample has a 3x3 shape distinguishing all dihedral orientations.

## Teaching support and limits

Three demonstrations plus one query, consecutive accepted sample indices.
Each four-pair window contains two witnesses, so every query rotation retains
one. The declared by-color and fixed-three rivals fit all three canonical labels;
the generated counterexample in counterexamples/repeated_color_variable_frame.json
refutes both with actual Racket outputs. Main-diagonal and half-turn rivals are
also checked. Explicit overrides are individual-instance controls and do not
inherit the default lesson guarantee.

Finite evidence: final 12-stage battery green; 33 focused tests; 300 materialized
lessons/1,200 rotations with zero declared-rival ambiguity; all six fixed-seed
schedule starts and 24 rotations pass. See the return RESULTS.json for hashes
and commands. No prior task audit index existed at this pinned baseline.

Open distribution limits: defaults use only two or three objects and three total
colors; four objects and additional palettes require overrides. Frames remain
2x2/3x3, repeated-color default pairs have unequal sizes and positive-diagonal
placement, and larger/rectangular/interleaved frames are untested. The finite
rival set does not establish universal identifiability or training admission.
## Current reviewer considerations

Source SHA-256: `ef7c0b0e3b5615546734915c0258e749960614810dcd7690f8e92304cc06227d`.

# Decisions — 538503abef57 v2.0.0

## Authority and geometry

Keep the existing Racket rule and all canonical examples unchanged. The canonical
inputs are 9x11, 10x12 and 11x13; all have two differently colored, five-cell
components in 3x3 frames. The previous notes contain no rationale; original intent
beyond the source comments is unknown. The Racket program transposes full crops,
so separating occupied cells alone is weaker than separating their frames.
The chosen full-frame moat prevents crop contamination and transformed collisions.
It also guarantees that reflection preserves component/color counts.

A finite pool enumerates connected shapes spanning 2x2 or 3x3 squares. Shapes
symmetric about the intended anti-diagonal are excluded from defaults; a rigid
3x3 shape with all eight dihedral views different is included in every sample.
This broadens the previous 3..5-cell random-walk output to varied 3..8-cell
shapes, avoiding placement retries that could drop an object. A random row and
column cut supply four regions, each at least 3x3 even on the minimum 8x8 grid.
Random shapes and positions still vary within those regions.

Alternatives considered: retain growth with more retries (still risks omissions
and only sparse small shapes); allow overlapping frames (Racket crops another
object's pixels); expand to arbitrary rectangles (legitimate separate scope,
with swapped dimensions/clipping interactions). The square-frame task needs
neither a new reference rule nor a new subsystem.

## Exact controls and compatibility

The four real axes are grid_h/grid_w=8..16, n_objects=2..4 and
n_distinct_colors=2..5, counting background. A palette count cannot exceed
n_objects+1. Only (objects,colors)=(2,4),(2,5),(3,5) are declared incompatible;
all other combinations work constructively. A color override alone increases
the default object count as needed. Every advertised bound works in all bands.
Boolean/coercible scalar values, invalid sample indices, unknown difficulty
labels and unknown axis names are rejected explicitly. Difficulty is None or
one of easy/medium/hard; it changes shape-density weights, not exact bounds.

Unused palette_kind, palette_size and texture controls and singleton density/
position descriptions are removed. Their old advertised behavior was not
implemented. Callers relying on those names now get an error rather than an
apparently successful ignored override. This is a deliberate interface cleanup
in the new version, not silently retained compatibility. No external caller was
changed in this packet.

## Canonical support and lesson design

An independent profile mixture favors canonical (H,W) pairs in every band,
while maintaining random support over every 8..16 size. All default inputs have
three total colors. The measured strict profile check has 12/20 exact hits in
each band, 36/60 overall, and 39/60 envelope hits. This measures height, width
and distinct-color support; it is not replay of canonical grids.

Both by-color grouping and fixed-three-frame reflection fit all 3 canonical
labels. Defaults alternate two-object 3x3 core examples with three-object
mixed-size witnesses. The repeated-color pair in a witness has 2x2 and 3x3
frames in opposite NW/SE quadrants. Whole-color reflection exchanges these
unequal frames, while component reflection keeps their anchors; their size
mismatch prevents accidental agreement. A 2x2 frame also refutes fixed-three.

Three demonstrations and one query are the measured production assembly.
Every four consecutive indices contain two witness slots. Removing any query
retains at least one, so all query rotations refute both canonical shortcuts.
The fixed-seed native enumeration checks both residues in all three bands:
6 lessons/24 rotations at seed 0, with 15 unique inputs among 24 overlapping
pair uses. The independent random native census checks 100 lessons per band:
300 lessons, 1,200 distinct inputs and 1,200 rotations, all without detected
ambiguity against the four declared rivals. No generation rejections occurred.
Do not apply this lesson statement to arbitrary explicit overrides, fewer
than three demonstrations, edited sources, or rival rules not tested.

## Retained failures and limits

The baseline battery had four failures plus profile/semantic advisories.
The first after pass exposed 39 invalid call-argument acceptances and omitted
the separately required schedule receipt. Focused failures and both battery
attempts remain in checks/. The final source fixes the argument contract and
consumes its own final schedule receipt; all 12 stages pass. Task-tests initially
failed infrastructure preflight because pytest was only installed in user site;
a fresh isolated local environment with copied installed distribution files
resolved this, and all 33 tests passed with no skips. The failed preflight is
retained and is not misreported as a failed generator test.

Defaults deliberately remain a finite shape family and use two/three objects;
four objects and other palettes are override support. Repeated-color witnesses
retain a position/size relationship. No universal uniqueness, performance gain,
model mastery, approval, or training admission is claimed. Future expansion
should add same-size and arbitrary-position repeated-color witnesses and
larger frames with new rivals, then recheck actual assembled lessons.
