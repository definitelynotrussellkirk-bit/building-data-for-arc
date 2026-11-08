# Current authoring status — da515329

Unapproved public-evaluation family. All three supplied train labels and the
supplied test label match the general clockwise Racket contour construction.
Default: infer hollow-cross center/color/arm radius; use k=max(2,radius), extend
four arms by k, then repeat clockwise groups (2+4*n, inward k-2, forward k).
Path motion is unbounded; only painting is clipped. Later segments may re-enter
(the supplied 22x22 example includes an isolated bottom-right cell).
Alternative: reverse every turn (counterclockwise), with exactly matched inputs.

The base generator is standalone. Native engine.py is a byte-identical snapshot;
tests enforce identity because native resources cannot import the root generator.
Canonical.rkt equals reference.rkt byte-for-byte. No labels are looked up.
Two minimal demos: radius one exposes the spacing floor; radius three/four
exposes the inward elbow. Both centers are off the geometric middle. Four query
sizes, variable radii/colors/centers, rectangular orientations and a 30x30 output
with >300 painted cells provide lawful diversity; the input stays a sparse cross.
Demos 2..6 and queries 1..4 are independent and prefix-stable. Presentation
shuffles the complete four-query bank before taking a one-query prefix.

Bounded self-review includes opposite turns, fixed radii 2/3/4, canvas/swapped
centers, missing radius floor, stop-at-edge, incorrect growth, fixed cyan ink,
filled center and identity. 32 seeds x two settings x five demo counts give
320 audited episodes with no harmful declared-rival survivors. This is not a
uniqueness proof. All labels in authoring preflight and the causal radius
replacement are independently executed through protected Racket; the larger
sampler audit uses Python claim/rival implementations. Owner registration,
native qualification/acceptance and training admission remain pending.

## Current repeated-parent reconciliation

Preserve exact clockwise/counterclockwise programs and broad arm-length/off-canvas reentry domains. Port longest completed component highlight to the incumbent contour engine, using color 2 and first scan-order maximum on ties. Incoming contact-avoidance/visible-arm algorithms remain proposals, not replacements for incumbent geometry. Current evidence resides in evidence/repeat-ninth-union. Private native acceptance and root publication are separate.
