# Current notes: 1e7eb285f158 / training:e88171ec

## Canonical source and remaining scope

Production remains generator v3.0.0, SHA-256
`a934ccbb7d60b6e20c726c87b264b60e23ba8cd76b2a5858b2b321f85c2c9486`, with
canonical rule hash `d40abed3e512`. Its code, frozen fixtures and rule authorities
are unchanged by the parameter proposal. Source approval, variant acceptance and
training admission remain separate; none is granted here.

The inherited `synthetic_texture_residual` remains unresolved: production uses
periodic outside-zero texture. Another teaching limit is that its eligible
rectangles are unique or equal-size maxima, so first/last-rectangle, tallest and
widest shortcuts are not directly distinguished by unequal eligible competitors.
Any nonempty production override also disables its ordinary tie schedule; a
wrapper that forces larger rectangles through overrides would lose tie lessons.

## Proposed parameter family

`workspace/parametric/` contains a separate runnable prototype, exporter and thin
promotion adapter. Episode-fixed `inset_depth` is 1 or 2 and `tie_policy` is
`row_major_first` or `row_major_last`; the default (1, first) returns the exact
canonical Racket text. Last means reverse `(top,left,bottom,right)` among
maximum-area rectangles, including residual ties at an identical origin.

Inputs are matched across settings, with separate local RNG streams for demos
and queries. Supported counts are 3..12 demos and 1..12 queries. Samples use
19..23 grids with 5..7 selected dimensions, deliberately keeping the depth-two
interior nonempty. The first demonstration contrasts a 6x6 area winner with
7x5 and 5x7 losers; horizontal and cross-diagonal ties teach order. Queries
include vertical ties. Random outside zeros replace the lattice in this
prototype only; guard rings and slot geometry remain a limited synthetic grammar.

Certificates fit four parameter settings and ten explicit semantic shortcuts
using demonstrations only. The exporter independently executes all actual labels
and all four parameter fits in protected Racket. Public IDs hash exactly visible
bytes; settings, seeds, programs and query labels are private. Duplicate public
payloads/inputs and non-integer colors are rejected before publication.

Current focused evidence: all four settings on seeds 0 and 17, each with 3 demos
and 4 queries; 56 distinct program/input executions; all four canonical examples
and literal boundary cases; maximum counts and retry failure paths in Python.
The independent adversarial check also compared 112 Python predictions against
brute-force enumeration on 28 irregular grids. See task-local
`workspace/parametric/evidence/current/` and its source inventory; exact limits
and runnable commands are in the prototype README. Finite rival rejection does
not establish arbitrary-program uniqueness or model learning gains.

Next useful action: owner assessment of the proposed grammar/parameter meanings,
then fresh native qualification and explicit variant acceptance if warranted.
The production texture finding is not cleared by these separate prototype checks.
