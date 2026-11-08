# Prototype matching and transform transfer

This reviewer prototype preserves the exact canonical `prototype` Racket
program. The meaningful alternative, `transfer`, identifies the unique D4
transform from the displayed matching prototype to the query, applies that
transform to the other displayed prototype, and paints its tight support in the
query color. Production generation, canonical examples and approval state are
separate and unchanged. Reviewer readiness does not constitute owner acceptance
or training admission.

## Public input grammar

Inputs are built-in nonempty lists of equal-length built-in lists, with both axes
in 1..30 and exact integer colors 0..9. For width W, let p=floor((W-2)/3), with
p>=1. Three width-p panels start at columns 0, p+1 and 2p+2. Separators at columns
p and 2p+1 are full-height color8. The remaining zero, one or two rightmost
columns must be zero. This matches the canonical quotient geometry and admits
30-column scenes (p=9, one zero tail column).

Each panel contains one nonempty monochrome, four-connected support. The three
support colors are distinct nonzero values; color8 is allowed in every role.
Shapes may touch panel edges, contain holes, or have arbitrary admitted size and
topology. The two prototypes have eight distinct normalized D4 orientations and
belong to different D4 classes; the query matches exactly one. These conditions
make both the prototype identity and the transferred transform unique.

This native family deliberately excludes symmetric prototypes. The exact
canonical program remains byte-identical and remains defined on symmetric
original examples; its wider historical domain is not silently claimed as the
transfer family's grammar. The sampler's small shape pair and tall profiles are
constructive examples, not additional restrictions in `analyze` or `solve`.

## Rule settings and sequential dependency

`{"mode":"prototype"}` is the exact canonical default. A geometrically splits
panels, normalizes their nonzero supports, and identifies the matching prototype.
B returns that displayed prototype's normalized support in the query color.

`{"mode":"transfer"}` also stores the unique transform code T taking the
displayed matching prototype to the query. B reads that code, transforms the
other displayed prototype, normalizes it, and renders it in the query color.
The causal control replaces only the code computation by identity while leaving
prototype selection and B's transform/render expression unchanged. Nonidentity
rotation and reflection examples expose this dependency. The witness retains
executed intermediate values and final protected-runtime outputs.

## Counts, streams and teaching design

Seeds are exact integers in 0..2**63-1. Demos and queries are independent exact
integer controls: demos4..6 (default4), queries1..4 (default4). An omitted setting
is selected from a separate deterministic SHA256-derived settings stream.
Explicit settings share identical inputs. Separate demo/query streams always
build full banks of six/four inputs before slicing, preserving prefixes and
isolation from requested counts. Each call returns fresh lists.

Four required demonstrations pair match indices0/1 with rotations and
reflections: (0,rot90), (1,rot270), (0,flip-h), (1,transpose). The small prototypes
have equal area and bounding dimensions but distinct D4 classes. Independent
display poses, offsets, colors and class order vary. Color8 is explicitly present
in prototype0, prototype1 and query across the first three examples.

The four-demo minimum is a teaching cost: a rotation-only matcher with constant
fallback0/1 requires two reflection cases with both match roles; a reflection-only
matcher with those fallbacks requires two rotation cases with both roles. For
full-eight-orbit supports these categories are disjoint. Fewer than four cannot
refute all four controls in this design. The native contract states this narrower
range openly; qualification explicitly requests six demos and four queries.

Demo sizes are4x14,5x18,6x22,7x23,18x26,30x30; query sizes are3x11,16x23,24x29,
30x30. Tall supports use a left spine, top/bottom rows, asymmetric end rows and
random middle full rows. Their non-square bounds, full/partial end-row pattern
and opposite-side spine exclude all nonidentity symmetries and D4 equivalence
between the pair. Only size-preserving transforms are sampled for these tall
panels; the small scenes exercise all eight orientations. The two30x30 profiles
contain453 and468 foreground cells respectively, including separators, with
substantive content in all four quadrants.

## Evidence and limits

`audit_native.py` evaluates independently authored Racket rival programs using
the protected current runtime. Only the first four demos fit a rival; all four
private queries score every survivor without filtering its hypothesis by query
answers. Literal/isolation tests, full execution ledgers, exact task/runtime
closure, sampler reports and any retained failed attempts accompany the result.
The finite rival set and finite seeds do not establish uniqueness among every
possible program or exhaustive correctness over all admitted inputs.

`promotion.json` uses the current native protocol. Source-bound evidence lives
under `evidence/current-native`; the manifest binds the adapter, implementation,
canonical rule, README, audit and focused tests. Qualification, causal witness
and shuffled one-query-per-turn public preview are separate native receipts.
The private four-query episode is retained, while each public turn reveals one
query and no private output, parameter, program, or future query.
