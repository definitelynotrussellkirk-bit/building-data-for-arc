# Current design — public parent 195c6913

This is a new public-evaluation creation, not an accepted native generator.
The immutable `workspace/public-parent.json` is its original-source linkage.

## Inferred canonical rule

The top-left color is wall. The dominant other terrain color is corridor.
Detached 2x2 swatches, in reading order, specify a repeated color sequence and
then the collision-marker color. Repeated swatches matter. Left-edge seeds
start eastward traces. At each wall, paint the forward blocked cell with the
collision color and turn at the immediately preceding free cell: east, north,
east, north. Continue the cyclic sequence without resetting at corners. Stop
at the canvas edge or when the new leg is immediately blocked. Erase swatches.
Python and protected Racket reproduce all three original demonstrations and
both provided test-gold grids; this is a general geometry rule, not a lookup.

## Native family

`turn=north|south`; north is the byte-exact reference default. The alternative
uses the same legend, collision, and phase rules but alternates east/south.
Inputs are identical across settings. Two demos are sufficient for the finite
named rivals. Counts support 2–6 demos and 1–4 queries; always construct the full
four-query bank before privately shuffling presentation and taking a prefix.

Generation uses irregular corridor ribbons, one or two independent origins,
arbitrary distinct role colors (including zero), repeated 2–4-swatch sequences,
rectangular canvases, jagged boundaries, and a 30x30 two-origin stress query.
Two-origin traces are separated; overlapping traces/overwrite precedence are
not admitted. Top-left is deliberately wall; swatches are detached, and the
corridor is the largest non-wall color. These are grammar limits, not claims
about all conceivable extensions of the public parent.

## Sequential dependency and self-review

A traces the first horizontal ray, producing the last walkable pivot and phase.
B uses that pivot to launch the next vertical leg and hence later turns.
The causal counterfactual shifts only the first origin's first pivot left by one
cell. The live protected witness retains exact input, programs and both labels.

The finite executable rivals are opposite turn, stop after first collision,
reverse sequence, deduplicate swatches, first color only, keep legend, shift
phase, reset phase at turns, pivot too early, and omit collision markers.
The bounded sampler refuses a minimum lesson when a declared rival fits both
demos but changes any query. The audit cross-checks Python claims with Racket;
finite checks do not prove universal identifiability or measured learning gain.

## Delivery and limits

Use `adapter.generate` for private labeled episodes; `adapter.present` returns
controller-only public/private bundles. Only one `public` entry is model-visible;
never expose the bundle, directory listing, source indices, program, or answers.
Racket labels are independently checked by public authoring preflight and the
bounded audit. Owner registration, source review, native qualification and fresh
acceptance are still required. No training admission is performed.

A same-size, same-mtime source-mutation test exposed path-only module caching.
Both family adapters now key by path plus source content and compile those exact
bytes, avoiding stale Python bytecode or previously imported generator code.
The ordinary `task-tests` wrapper cannot resolve this unregistered ID; the
complete task-local suite is run directly until owner catalog registration.

## Native source closure
The adapter reads an exact canonical copy inside `workspace/parametric/canonical.rkt`, explicitly declared as a resource. This keeps program bytes inside the native promotion source inventory rather than relying on the task-root `reference.rkt`. Regression tests relocate only generator.py and the prototype directory, then produce a complete lesson; a separate default equality test requires the copied rule to remain byte-exact with the root reference.

## Current repeated-parent reconciliation

Preserve exact north/south programs and add exact phase-restart program. Both constructive samplers remain. Three demonstrations reject known retained shortcuts without consulting queries. Current routing constructor is sampled per input with geometry-only validation, replacing inherited query-label-dependent bank rejection. No Cartesian south/restart setting is invented. Current evidence resides in evidence/repeat-third-union. Private native acceptance and root publication are separate.
