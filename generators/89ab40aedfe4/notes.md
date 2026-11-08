# Working notes: 89ab40aedfe4

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review review-2ed797d31c1c35a6

The topmost-conflict profile now combines an interior marker-only column with a
distinct stable tie. Together with the unchanged separate tie and marker
profiles, this preserves each declared teaching distinction under every query
holdout of five consecutive samples, with four demonstrations. The canonical
anchor and all declared integer axis ranges are retained.

Foreign top-row colors now return validation errors before marker parsing.
None overrides retain scheduled defaults; non-integer exact controls are rejected.
The keyed RNG namespace VERSION=2.0.0 is intentionally retained so unchanged
profiles replay exactly; use the full generator source hash for repair identity.

Selected authority synchronization changed whitespace only. New focused tests and
a reusable cyclic schedule diagnostic live in tests/ and workspace/. Full review,
source-bound before/after evidence, rationale, two audits and visible-only solve
records are in the corresponding returned review ZIP.
## Current reviewer considerations

Source SHA-256: `2800dab77009ba054309c218507cd1e4a735860dc0f790ade8399d33888deb6b`.

# Distribution decisions: 89ab40aedfe4

## R1: overlapping teaching support within four demonstrations

The selected baseline is the source hashed f0808f35cb4aca9528f263bfdbba177ef76c1172e8d54dc6dc7f8df5270de27e.
Associated notes cite the prior return review_response_external-local-random-921f8c90c420_x
and its four-profile schedule as a lead. That archive itself was not supplied or
replayed; its historical claims were not used as current measurements.

The rule remains stable ascending population sorting of the bit column adjacent
to each carrier. The public examples have distinct populations and no marker-only
bit columns. Consequently reverse-tie and fixed-marker rivals fit all five usable
canonical pairs. The old four-profile window teaches both, but its five-pair
rotation can put the sole distinguishing pair into the query. The exact baseline
seed-7001 witness and the wider seed-0..9 diagnostic are retained under checks/.

The repair combines two equal-population patterns and an interior count-one
marker into topmost_conflict. The separate stable_tie and marker_only profiles
remain untouched. Every five consecutive samples contain a combined witness and
the two separate witnesses. Removing the combined one leaves both separate ones;
removing a separate one leaves the combined one. The movable marker also refutes
first-active-row ordering because population puts it first and first-active-row
puts it last. Identity and descending order are refuted by every nonidentity input.

Alternatives rejected: seven demonstrations would unnecessarily increase the
lesson budget; query-specific filtering would hide support problems and change
rejection behavior; deleting marker/tie queries would shrink the intended domain;
independent random branch choices would leave nonzero probabilities of missing
teaching evidence. The deterministic four-profile schedule is retained.

## Geometry, palette and joint domains

The domain stays height 8..16, slot count 3..6, regular spacing 3..5 and one
foreground color in 1..9 against fixed background 0. Carriers remain full-height;
the top row contains marker pairs; the last bit column ends the grid. These
choices come from the selected canonical grammar and preserve its reference.
Canonical anchors keep height 13, five slots, spacing three, dense distinct
populations 7..12. Defaults remain difficulty-banded elsewhere.

The combined case uses populations [4,4] plus distinct nonmarker populations and
one count-one marker placed strictly inside the source order. The existing
first-body construction still fits the entire declared joint domain. At the
tightest repeated-count case it has at least three distinct patterns available
for the two ties. Tests cover heights 8..16 crossed with slots 3..6 and both
spacing/color boundaries. Public override and self-check batteries cover the
remaining advertised control requirements.

The anchor remains one of four scheduled profiles. Separate tie-only and
marker-only cases prevent perfect co-occurrence of those conditions. The new
combined profile reduces the fraction of scenes with all-distinct positive
counts; anchors and marker-only profiles retain that support. Identifiability
against unlisted conditional rivals remains unknown. No new augmentation,
rotation/reflection covariance or arbitrary-background palette claim is made.

## R2: validator termination

A foreign top-row color was already invalid but did not advance the parser's
foreground/zero run scanner. Return the error before scanning. Seven positions
of a hand-constructed valid top row are mutated to a third color in a subprocess
with a deadline. This is a real invalid-input termination regression, not a
claim that reference execution is meaningful on those malformed inputs.

## R3: exact controls and None

The context helper treats None as omission, but the local scheduling helper
previously treated key presence as an override and selected its full range.
The repaired helper follows the existing None convention. Non-None exact axes
must be Python integers, excluding bool; coercible strings/fractions are rejected
instead of silently changing the requested value. The shared legacy helper was
not modified. Integer min/max ranges and unknown-key errors are retained.

VERSION stays 2.0.0 as the existing keyed-RNG namespace, preserving exact streams
for unchanged canonical, tie-only and marker-only profiles. The repair identity
is the new full source SHA-256, not an assertion that old source bytes are still
approved. New source approvals remain the maintainer's intake responsibility.

## R4 and R5: source binding and portability

The selected authority JSON claimed exact synchronization while storing collapsed
whitespace. The canonical program and selected target had identical normalized
text. The selected copy now uses the canonical bytes; canonical ledger, normalized
rule hash and archived raw source remain unchanged. Both source parity and exact
selected-authority checks passed afterward.

Retained test assertions are preserved. Only canonical-data and generator path
resolution changed to locate the current library/runtime tree. An intermediate
attempt fixed task-local placement but failed the automatically copied legacy
placement; that failure is retained, and the final helper supports both layouts.
The frozen baseline fixtures were never edited.

## Evidence policy and remaining limits

The schedule probe scores raw directed samples with Python-mirror labels and
records every observed index and exact first counterexample. It iterates actual
CANONICAL_SHORTCUTS/LESSON_COMPETITORS declarations instead of duplicating their
names. The larger census independently labels via the selected Racket runtime.
The two evidence sets are reported separately. Neither finite enumeration nor
declared-rival agreement proves uniqueness against every possible rule.

## Review review-9649387d21cfe799: legend-selected prototype

Public focus task `d59b0160` was used only as inspiration. Its visible rule reads
non-background colors from the color-3 bordered legend and erases each external
four-connected non-7 region containing every legend color. The transferred
dependency is narrower: in the opt-in `contains_key` prototype, the first bit
column names required body rows; only later columns containing every required
row participate in the existing stable ascending population sort. The key and
nonmatching columns remain fixed.

Production `generator.py` remains byte-for-byte SHA-256
`2800dab77009ba054309c218507cd1e4a735860dc0f790ade8399d33888deb6b` with
VERSION `2.0.0` and RULE_HASH `4bc48cdc5789`. `all_slots` returns the exact
canonical Racket source; `contains_key` is task-local workspace code and is not
selected, approved, catalogued, or admitted to training.

Each forced setting has three demonstrations and four distinct queries at the
retained seed. Exact Racket/Python verification covered 28 executions; every
retained demonstration and query distinguishes the settings. A bounded
adversarial pass added 70 executions over five diverse seeds and checked ten
public/private projections, exact integer colors, hidden-field omission, query
label masking, metadata-invariant public bytes, and copy isolation. The final
self-review also caught and repaired two boundary gaps: both Python and the
proposed Racket rule now fail loudly for an empty key body or fewer than two
matching candidates, and public materializations now use exact canonical visible
bytes under opaque content-derived names rather than hidden setting names. The
verifier also rejects duplicate demo/query inputs, confirms paired sampler
inputs across settings, and only replaces known generated artifacts whose prior
manifest, byte counts, and SHA-256 values match; modified/foreign files are
preserved and abort the run. Evidence is under
`checks/parametric-legend-selector/` and `checks/final/`.

Limits: generated scenes use one fixed 12x17 six-slot grammar with three
matching and two nonmatching candidates; finite examples do not establish
uniqueness against every participation or ordering rule. The public parent test
prediction is visible-rule evidence only; no private label was available or
consulted. The next useful action, if this extension is desired, is independent
review of the task semantics before any production/catalog integration.
