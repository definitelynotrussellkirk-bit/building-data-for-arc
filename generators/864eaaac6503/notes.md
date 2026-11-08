# Working notes: 864eaaac6503 — version 2.0.0

## Authority and domain

The selected authority remains `(rule! rotate-ccw)`, normalized rule hash
`56583247080a`. Python transforms are diagnostic rivals/mirrors; production labels
come from Racket. No canonical rule, catalog, or shared checker was edited.

The sampler retains the original at-least-two-color domain. Rotation itself also
works on monochrome inputs, but this generator intentionally does not teach from
them. `self_check` checks rectangular ARC integer grids, dimensions 1..30, and at
least two colors. It accepts lawful singleton, line, block, and symmetric shapes;
foreground geometry is not part of the rotation rule. Generated dimensions are
2..30. Every generated palette includes black; arbitrary nonblack backgrounds
are outside this sampler's default support, not outside the authority's domain.

## Reversed distribution choices

The imported 1.1.0 sampler used broad random texture canvases (default dimensions
2..18) and difficulty-dependent palette caps, despite advertising 2..30 and 2..10.
Its source did not document why. The baseline battery reproduced missing exact
overrides, coerced invalid controls, absent semantic contracts, and weak canonical
profile coverage. We now alternate canonical and extended examples by the actual
sample index: C,E,C,E,... . Canonical examples are 3×3, black plus one nonzero
color, and are not 90-degree identities. Extended examples vary size/palette and
refute every other dihedral orientation. Some are rectangular; rotation swaps
their dimensions. Difficulty grows the extension, not the legal override range.

This intentionally concentrates sampling near the observed small examples while
retaining size generalization. Canonical examples are not memorized templates:
noise sampling gives every nonidentity two-color 3×3 arrangement positive
probability, including all five canonical inputs. Default shapes, colors, and
densities are not claimed to exhaust the rule's lawful domain.

## Lesson contract and its limits

The contract is three demonstrations and one query from the production sampler,
which advances through indexed samples and discards duplicate pairs. Every raw
four-sample window contains two extended witnesses. Their minimum dimensions
alternate even/odd, so neighboring extended pairs cannot be duplicates; canonical
and extended dimensions are disjoint. Deduplicating canonical pairs can only add
draws, not remove either extended witness. Holding out any one accepted pair
therefore leaves an extended demonstration. Each extended grid distinguishes CCW from
identity, CW, half-turn, horizontal/vertical reflection, and both transposes. It
also refutes `only_three_by_three`, a rival that fits every canonical pair but
rotates only 3×3 inputs, and three partial-foreground construction rivals. The
spatial rivals reproduce the checker's measured mutation behavior on square
inputs using the input and a diagnostic CCW mirror, with first-component rotation
on rectangles. They are explicit competing programs, not authoritative labels.
The finite eleven-rival screen is not a proof of unique
induction against arbitrary programs.

The guarantee applies to default generation only. Explicit non-None overrides,
even numerically default-valued ones, select lawful controlled samples without
an informativeness promise. A downstream assembler that filters, replaces,
reorders, or samples examples independently must gate its final labelled episode.
The four-index period declares C, E-even, C, E-odd profile selection, not repetition
of grid data. An initial two-index version was rejected: seed 21212, easy, start 0
produced duplicate E pairs at raw indices 1 and 3; the runner accepted indices
0,1,2,4 and query rotation lost its sole extended witness. The fixed geometry
cycle and production-dedup regression replace that invalid raw-window argument.
Fixed-seed period enumeration covers every start residue at that seed only.

## Exposed controls

Dimensions and realized palette count are exact and observable. Plain integer
dimensions 2..30 and palette sizes 2..10 work in every band; booleans, numeric
strings, unknown keys, and nonfinite/out-of-range numeric values are rejected.
`None` omits a known override. Capacity conflicts name their active axes. Only
unpinned dimensions may grow to fit all colors or a uniform border.

Textures, background density, noise, and border selection are procedural controls
(`exact: False`), not promises of recoverable image statistics. Palette repair
may modify a texture; border constraints remain intact. The old `rot4_symmetric`
negative texture was removed: it could be rectangular or monochrome, and rotation
symmetry is lawful, so it was an invalid negative fixture. Honest malformed-grid
fixtures now cover ragged rows, booleans, out-of-range colors, and monochrome
inputs excluded by this sampler's documented domain.

## Evidence and open decisions

Focused regressions live in `tests/test_rotation_contract.py`; minimal examples
live in `counterexamples/`. The return's `checks/` preserves before/after batteries,
Racket-labelled lesson evidence, failed development attempts, and exact commands.
The shared defect detector has a confirmed canonical counterexample: its named
`solid_2x2` impostor equals the first canonical input. A proposed exact-match
calibration patch is included as feedback evidence only. Other generic
mutation-power/minimal-shape warnings must be assessed against this broad
rotation domain, not suppressed by arbitrary foreground restrictions. The shared
semantic detector recognizes applied/lambda forms of a rotation authority but
misses the exact first-class callable `(rule! rotate-ccw)`. The return includes a
tested whitelist-only proposed calibration, kept outside the canonical patch.

`workspace/parametric/` is a separate proposed clockwise/counterclockwise episode
prototype with its own instantiated Racket rules. It does not change or approve
the selected canonical task. `workspace/export_gate/` provides a finite-rival
check at the final episode boundary; it neither establishes label correctness nor
measures any language model's training improvement.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`; prior unintegrated return claims were not used
as measurements of this pinned baseline.
## Current reviewer considerations

Source SHA-256: `5d809c80e9693a9a0b2747ef50cad89f8bd6dca44d6dceafaa851c8aadff0354`.

# Decisions: 864eaaac6503

## D1 — Keep the authority and make distribution repair explicit

The exact canonical rule is `(rule! rotate-ccw)`, hash `56583247080a`.
Its five labelled canonical pairs agree. There was no evidence justifying an
authority change. Version 2.0.0 changes the sampler and diagnostic contract only;
no catalog, approval, baseline fixture, or shared executable is patched.

## D2 — Restore canonical support without memorizing the examples

The original source exposed broad textures and sizes, with no recorded rationale
for its 2..18/difficulty palette limits. The baseline covered canonical dimensions
and palette in only 3/60 draws and missed hard entirely. Default canonical samples
are now 3×3 with black plus one nonzero color. Nonidentity noise has positive
probability for every arrangement in that small domain, including all canonical
inputs. Larger extensions preserve the rule's size generalization. We rejected
sampling only the five known inputs and rejected a default of only large generic
canvases. Evidence: before/final profile-floor JSON, 26/60 final hits.

## D3 — Exact dimensions/colors; honest procedural controls

Dimensions 2..30 and realized palette sizes 2..10 are legal across difficulty
bands. The palette is repaired after textures/noise/borders without erasing an
already unique color or changing a fixed border. Only unpinned dimensions may
grow for capacity. Impossible joint constraints raise an explicit conflict with
axis names; invalid types, booleans, strings, unknown keys, and nonfinite numbers
fail early. Known values of None mean omitted controls. Textures/density/noise/
borders describe construction procedures and are marked non-exact. A texture is
not promised to survive exact palette realization unchanged. The removal of
`rot4_symmetric` is intentional: the old negative branch could be rectangular or
monochrome, and rotational symmetry alone is a lawful rotation input.

## D4 — Check the production assembler, including duplicate rejection

The first repair's C,E,C,E argument checked raw windows, not accepted episodes.
Independent review reproduced seed 21212, easy, start 0: raw E indices 1 and 3
were identical, accepted indices became 0,1,2,4, and one query rotation left only
canonical demos. The failure and old source remain in checks/code-review and the
task counterexamples. Consecutive E minimum dimensions now alternate parity.
C and E shapes are disjoint and neighboring E shapes cannot coincide; duplicate
filtering cannot remove either of the two E witnesses in the initial four raw
positions. Canonical duplicate rejection can only draw extra examples. Period
4 declares the C,E-even,C,E-odd cycle honestly. Enlarging the demo count without
addressing the duplicate mechanism was rejected as an incomplete fix.

Default lesson policy is **three demos, one query, production duplicate filtering,
all four query positions supported**. Native evidence covers 300 lessons/1,200
rotations and fixed-seed enumeration covers 12 lessons/48 rotations. These are
finite checks. Other assemblers, dropped examples, explicit overrides, or fewer
demos require their own final-episode screen. The required solve episode uses
three demos and two queries; it is a solve record, not a claim that a different
lesson-census policy was measured.

## D5 — Teach whole-grid processing, not just orientation

The first after battery retained an actual partial-construction mutation witness
at easy seed 163210477420611, start 11, rotated query 2. A larger demo still had
only one component and did not teach that all foreground participates. We added
three independent input-only rivals: rotate only the first component; apply only
nearest-first-component changes; and the latter with reversed distance ties.
Each E sample now refutes these as well as seven dihedral alternatives and the
3×3-only shortcut. Shared component helpers are reused. Canonical sampling and
the validator still permit single-component lawful inputs. Requiring every
input in the rule's domain to have multiple objects was rejected. Final native
witness checks verify three witness families; the searched ambiguity disappears.

## D6 — Retain lawful validation despite generic warnings

Rotation has no special foreground grammar. The original at-least-two-color
sampling domain is retained and distinguished from the broader executable rule.
`self_check` checks shape, ARC cell types/range, and that palette domain. It
accepts singleton/line/block/symmetric examples when they meet those conditions.
The shared self-check-power denominator includes transformations that preserve
valid rotation inputs; final rejection 12/48 is therefore not by itself evidence
of an invalid validator. The named solid_2x2 probe equals a canonical input.
An exact canonical-match calibration proposal is included, but does not pretend
to resolve singleton/line or power warnings. The maintainer must decide the shared
policy. Arbitrarily rejecting such shapes to make the battery green was rejected.

## D7 — Do not manufacture a counterexample to the reference operation

The semantic checker recognizes `(rule! (rotate-ccw g))` but misses the equivalent
first-class callable spelling `(rule! rotate-ccw)`. Its generic rot270 obligation
would require poisoning a reference label. A six-identifier exact whitelist patch
and positive/negative tests are proposed under checks/authority-calibration only.
Declared rivals remain subject to their obligations. The current unmodified
battery stays red; this proposal is neither silently applied nor counted as an
official semantic pass.

## D8 — Separate parametric prototype from canonical execution

A direction parameter has a clear small domain: ccw/cw. Sampling it once per
episode produces a coherent distinct rule, and asymmetric demonstrations distinguish
it. The runnable prototype executes every label with the chosen instantiated
Racket rule, records hashes, and separates public from private examples. It is
proposed only. More parameters such as independent per-pair direction, arbitrary
angles, or unrelated foreground operations would change the task or break lesson
coherence; they were not added. See checks/parametric and workspace/parametric.

## D9 — Build a cheap final export gate

The answer to qwen9-data-value is implemented as workspace/export_gate. It screens
the actual final labelled assembly against a caller-declared, domain-justified
rival set, optionally at every query position. It does not regenerate labels or
infer a universal rival language. It retains a deliberate teaching negative and
a corresponding two-witness positive executed with actual Racket labels. This
adds a concrete check where an assembler can invalidate a previous census.
Production integration requires a separate shared-tool decision (F1).

## D10 — Storage recovery preserves identities and failed evidence

A full extraction exceeded the shared filesystem's available space/inodes. The
original ZIP was fully streamed and verified; a single seed was persisted before
the official draw. Only selected/runtime files were materialized. Audits likewise
use one recorded seed and unchanged official draw functions. A tested source-view
adapter supplies exact immutable archive bytes to the unchanged official builder;
selected changes and protected paths cannot be concealed by archive fallback.
The official portable task-test snapshot could not fit. A separate manual replay
therefore authenticates and extracts 210 original files (46,876,942 bytes) into
a new RAM directory, verifies the exact WORK Git root, and applies the official
patch. All 14 changed/new file hashes match before and after 65 passing focused
tests in an independent Python environment; three subtests also pass. Imported
project modules come only from the fresh source. The existing Racket installation
is reused as a toolchain. This narrower replay is explicitly not the official
runtime-closure replay or a passing official task_tests stage. No unrelated
workspace files were removed; an unused GUI binary was removed from the
reviewer-created Racket installation cache to fit native checks. Failed
extraction, census, test setup, parser import, and intermediate repair evidence
is retained where available. See checks/final-replay.

## D11 — Upgrade the retained direction prototype to the four-query contract

**Choice:** Keep `direction=ccw|cw` as the sole episode parameter and upgrade the
existing prototype in place instead of adding another family. Support exact demo
counts 2–6 and exactly four distinct queries. Use deterministic structured
profiles whose query side reaches 11×15, 16×21, 24×29, and a dense exact 30×30.

**Why:** Direction is a genuine rule-level alternative with the canonical `ccw`
default preserved byte-for-byte. The old prototype already had the right semantic
axis, but only emitted three demos/two queries on 2..8 grids and used positional
public filenames. Upgrading one artifact avoids duplicate execution evidence and
meets the controller's four-query/sequential-reveal contract.

**Evidence:** The focused suite checks both directions at every demo count 2..6,
four distinct queries, fixed episode settings, exact Racket label replay,
demonstration-only sole-survivor checks, and substantive 30×30 content. The
retained two-episode batch covers ccw/cw and passes the packet's strict public
export checker.

**Limit:** The finite rival certificate distinguishes only the two declared
rotations. It is not a proof against arbitrary programs or a measured training
benefit.

## D12 — Bind public identity to visible bytes and add a native promotion boundary

**Choice:** Export sorted SHA-256 filenames computed from the repository's exact
`public_challenge_bytes`; keep seeds, settings, programs, rival evidence, and
query answers private. Reject duplicate visible payloads before creating the
destination. Add `sequential_turn` so turn zero is byte-identical to ordinary
single-query use and later turns reveal one query input only. Add a thin exact-
adjacent-path adapter plus bounded `promotion.json`.

**Why:** Numeric filenames and ad hoc projections could leak ordering or drift
from the bytes actually shown to a model. The native worker is the correct
independent boundary: the adapter makes deterministic Python claims while the
worker re-executes every label through protected Racket and checks demo-only
identifiability.

**Evidence:** Private-only mutations leave public IDs unchanged; visible demo or
query mutations change them. Duplicate batches and invalid sequential indices
fail. The native manifest is current at
`86e764d305f213bbd82be57d00c7c6ab7fb135d063723cf51d7a64ed7fc890d5`.
Protected-Racket qualification passed both settings at seeds 0 and 17 with three
demos/four queries. The family remains unaccepted and `training_admitted=false`.

**Limit:** Qualification is finite owner-review evidence, not acceptance,
production use, or permission to train on generated episodes.
