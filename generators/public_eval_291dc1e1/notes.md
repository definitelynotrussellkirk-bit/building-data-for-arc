# public_eval_291dc1e1 — authoring decisions

The corner 0 joins two full border strips. Read components along the axis
marked 1 from that corner, then advance tracks along the axis marked 2.
Exclude the two strips, crop each four-connected non-8 component, preserve
horizontal-axis bar contents, and rotate vertical-axis bars 90 degrees CCW.
Stack their two-row normalized images in scan order, centered to the longest
bar with background 8. Preserve repeated identical bars and all interior colors.
The four training pairs and one supplied test gold must all execute exactly.

The episode-fixed parameter is stack_order=forward|reverse. Forward is the
canonical reading sequence; reverse reverses the complete component sequence
after its input-dependent border/track ordering. Stage A produces ordered,
cropped, normalized bars and their lengths. Stage B consumes that sequence and
its maximum width to center and stack the bars. A wrong-order intermediate
will change the protected Racket output without altering any input pixels.

The declared grammar uses top-left or top-right origins, fixed border colors
0/1/2 and background 8, one to fifteen filled even-length bars of thickness 2,
and input dimensions 5–30. Lengths are 2–28, so both output dimensions stay at
most 30. Components may touch the unmarked outer edge or the marked strip;
strip removal occurs before component discovery. Even lengths avoid an
unobserved odd-centering tie convention. Bottom origins are excluded.

Patterned squares rotate according to the visible primary-axis orientation,
even when square aspect ratio alone gives no direction. Horizontal right-start
bars preserve their internal orientation. These are explicit extensions taught
by patterned examples, because the corresponding original bars are monochrome.
Use core scenes H/right, V/left and V/right, with staggered offsets, internal
border colors, mixed squares and duplicate bars. The minimum is three: all
23 frozen rivals were defeated by those scenes in ten checked episodes, while
each two-demo subset admitted a query-changing rival (30/30 subset checks).
This is a finite teaching result, not universal rule uniqueness. Four query
scenes cover both physical axes and both top corners, including a substantive
30×30 input with a 28-long bar.

The independent oracle was frozen before candidate exposure and agrees on
103 inputs under both settings: five original pairs, eight frozen handcases,
eight boundary cases, 32 independently constructed random scenes and 50 sampled
scenes. Both Python and protected Racket agree on all 206 labels. Boundaries
include 15 bars with a 30×28 output, length 28 under all four axis/corner
combinations, and diagonally touching components that remain four-disconnected.
Sixteen objects are rejected. Count-prefix checks cover 96 requests. Exact
seeds, source hashes, rival definitions and smaller-demo counterexamples are
retained under checks/public_eval_291dc1e1/ in the return.

Root generation is standalone and input-only. Keep a byte-identical adjacent
sampler copy and canonical Racket resource inside workspace/parametric/. Owner
registration, qualification, acceptance and training admission remain separate.

## Current repeated-parent reconciliation

Retain exact forward/reverse programs and add exact incoming width_walk. Preserve both constructors by alternating complete query episodes. Keep incumbent first two demo profiles; a demo-only third-lesson search rejects all declared incoming canonical/walk shortcuts and finite mode rivals. Three demos remain sufficient, 3..6 supported. Ordinary base source and inputs remain unchanged. Current evidence resides in evidence/repeat-fourth-union. Private native acceptance and root publication are separate.
