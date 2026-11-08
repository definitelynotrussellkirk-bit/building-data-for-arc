# Working notes: 5ccdbe078da6

## 2026-10-02 · review-083504bc1ff4c2ff

Replaced version 2.1.0 with 3.0.0 after tests reproduced missing line/negative-
diagonal support, weak type validation, and dishonest override behavior. Racket
and archival authority were not edited. Previous rationale was not retained in
the associated notes.

The selected implementation is `generator.py`; review and teaching tools live
under `workspace/`. Tests are task-local. Final battery: 12 green stages; final
task tests: 52 passed; independently staged test set: 59 passed (including seven
existing audit-target tests). Racket census: 600 valid, nonidentity, unique final
inputs and no mirror mismatch. Source-bound reports are in the review return.

Important limitation: 24/60 uncurated three-demo windows retain a named rival
that changes the query. The cover tool constructs lessons whose demonstrations
refute six explicit rivals, not every possible program. Thirty research lessons
were built with 68 demonstrations and 30 queries; all 98 outputs matched a fresh
Racket execution. No model performance or training admission was measured.

The root repository suite has one reproduced environment-sensitive Python-
startup timeout failure; it was not silently fixed or suppressed. The task-local
runtime diagnostic and return feedback record it.

The fresh public-example solve passed three visible cases in one genuine
attempt, with earlier reference exposure disclosed and no reference consultation
during that phase. Hidden-query correctness was withheld.

Next work: see `workspace/HANDOFF.md`. Do not mistake a green per-input semantic
gate for guaranteed lesson identification or rerun a task draw to avoid a defect.
## Current reviewer considerations

Source SHA-256: `1e9b22b4d321df7f35c39ee40cded3698f24390b7d331b81daaf4ff1ea70fe5f`.

# Distribution decisions: 5ccdbe078da6

## 1. Preserve the reference; correct the input contract

The old summary required nondegenerate diagonal pairs and asserted marker
preservation. Its rationale is not retained: associated notes are empty. The
canonical inputs and actual Racket execution contradict those restrictions, so
I changed the generator contract and documentation rather than narrowing the
reference to the old sampler. Four retained canonical pairs still match Racket.
No canonical or archival authority was edited.

The new generator keeps exactly two cells per foreground color, one to three
colors, and zero background. Racket can also preserve non-pair color groups, but
that extension has no demonstrated need in this training envelope; adding
singleton distractors as a normal mode would dilute the intended pair relation.
The Python review mirror covers that preservation behavior; the public generator
validator intentionally rejects it. Invalid examples live in mutation fixtures.

## 2. Include collinear pairs and both diagonal signs

Horizontal and vertical pairs are lawful because they occur in the retained
canonical examples. Keeping the old “diagonal only” restriction would exclude
actual evidence. Down-left pairs are a bounded symmetry extension of the same
bbox operation, not an invented new transformation. The baseline never samples
them; the revised 600-draw census contains 289 such grids.

Public line endpoints have distance at least two cells to avoid deliberately
identity-only training examples. The validator accepts lawful adjacent pairs
rather than claiming they are invalid ARC inputs. All finite declared shape
pins remain realizable on the minimum 4x5 public grid.

Alternatives rejected: rotating canonical templates would over-constrain the
input distribution; rejecting negative diagonals would preserve an easy
canonical-fitting shortcut. Random placement alone under-supplies discriminative
intersections, so explicit crossing constructions are also included.

## 3. Make paint priority observable

Two constructive modes create crossing outlines and marker-overwrite cases.
Coordinates and colors remain sampled, and numeric colors are independent of
layout order. The intended priority is first occurrence in row-major input
order, not numeric color order and not “always keep markers.”

This is a support increase, not a claim that all old overlap cases were absent:
numeric-descending witnesses already occurred in 108/600 baseline inputs and
marker-restoration witnesses in 86/600. Final counts are 188/600 and 179/600.
Some easy-looking thin outlines cannot distinguish filling from outlining;
other demonstrations must supply that witness. `SEMANTIC_WITNESSES` therefore
measures actual output disagreement with each rival, not morphology alone.

## 4. Balance canonical support and breadth

A two-thirds core branch selects height 5..6, width 6..7 and two foreground
colors; the wider branch selects height 4..10, width 5..12 and one to three
colors. This avoids the old near-absence of canonical-size/count profiles
without hardcoding canonical grids or restricting all data to their small range.
Difficulty selects an independent layout RNG stream; it never changes the
validity of a declared override.

All-wide defaults were rejected because the existing profile-floor evidence
showed poor canonical support. All-core defaults were rejected because they
would teach fixed dimensions/count. Two-thirds is an engineering mixture,
not a learned optimum. The measured profile floor is 30/60 exact and 40/60
within the envelope; it does not establish a best downstream training mixture.

## 5. Remove fake controls instead of preserving silent success

The old `palette_size`, `n_distinct_colors`, `position_bias`, `density`, and
`texture` controls were redundant metadata, ineffective options or invalid
training modes. No retained rationale justifies their silent behavior. They
are removed from the public contract; unknown keys now raise TypeError.
Palette selection remains, but actually changes the sampled color pool.

This intentionally breaks callers that supplied obsolete keys. Such callers
must remove metadata-only pins or use the five documented controls, rather than
receive a misleading successful call. An undeclared compatibility layer was
rejected because it would recreate the very override defect being repaired.
Integer overrides reject booleans, floats and strings. All declared tuples use
the same ranges across difficulty bands; no incompatibility exceptions are
needed. The final matrix checked 28,170 draws with zero findings.

## 6. Teach with evidence, not just a green generator gate

A separate audit of 60 three-demo/one-query windows found 24 with a named rival
that fits all demonstrations but changes the query answer. These 240 draws are
a separate audit population, not extra rows added to the 600-input census.
A green semantic witness gate is not enough to claim each assembled lesson is
identifiable.

Rather than weakening the rival set or using query correctness to cherry-pick
lessons, the supplied selector requires demonstrations to refute the entire six-
rival registry. Exact bitmask dynamic programming finds a minimum-cardinality
cover with deterministic tie-breaking; the registry is capped at 16 rivals.
A greedy cover was rejected because an included regression case proves it can
miss a valid two-demo cover. Arbitrary brute-force subset search was unnecessary.

The tool partitions 600 unique Racket-labeled inputs into 30 disjoint pools of
20. The final pool member is reserved as query; only the other 19 candidates'
labels enter selection. The selector API receives query inputs but no query
outputs. Source-wide integrity checks can inspect stored labels for consistency;
query labels are not used to optimize, accept or reject the cover. Failure
pools are recorded and produce a nonzero exit, not silently discarded.

All 30 pools succeeded with two or three demonstrations. This guarantees only
refutation of the declared finite rivals. It does not certify universal rule
identification, learned-model success, unbiased sample frequencies or training
approval. Integrating this optional selector into the shared exporter is a
separate, authorized follow-up; ordinary default lessons remain unchanged.

## 7. Keep review infrastructure failures visible

A whole-repository timeout test failed and reproduced five times. A diagnostic
with and without Python site initialization showed that the 0.2-second startup
assumption is not portable to this environment. I did not alter the shared test
or suppress it, because those paths are outside the selected task. Its exact
failure and supporting probe are included in `RESULTS.json` and feedback F3.
The review is complete for its assigned scope, not a claim that every repository
test is green.

## 8. Bound the fresh solve claim

The episode was prepared only after stabilizing the generator. Its visible-
example solver was written during an isolated no-reference phase, but earlier
rule exposure occurred and is disclosed. One genuine attempt passed all three
visible examples. No artificial failed candidate was manufactured, and hidden
query correctness remains withheld. Curated rival examples elsewhere in this
return are diagnostics, not natural model-error trajectories.

## 9. Native parametric occlusion-fill handoff (2026-10-24)

The production generator and canonical rule remain unchanged at generator SHA-256
`1e9b22b4d321df7f35c39ee40cded3698f24390b7d331b81daaf4ff1ea70fe5f` and
canonical program SHA-256
`d8da2d7cc24bf7494d55936b92c67f375f8352f916589caa54932d1e9722543a`.
The new native family preserves that exact `finish=outline` default and adds
`finish=fill_most_occluded`: first paint all pair bounding-box outlines in
input reading order, measure each outline's loss after later overwrites, select
the earliest maximum-loss color, then fill its strict original-box interior.

The sampler is deterministic, setting-independent and prefix-stable for 2–6
demonstrations and 1–4 queries. Its first two demonstrations refute the retained
six canonical-outline and ten occlusion-selector rivals without consulting query
answers. The fourth query is a substantive 30×30 boundary scene. Public turns
contain one masked query and no future inputs, settings, program or total-count
hint; private examples retain all four controller-side queries.

Native qualification passed both settings at seeds 0 and 17 with 3 demos and 4
queries per episode (40 protected-Racket labels). The reusable self-audit replayed
24 additional protected-Racket labels and found no survivors in the finite rival
registry. The causal witness changes the Step-A intermediate from overwrite loss
to largest planned perimeter: the selected color changes from 7 to 5 and 76 final
cells change under protected Racket.

Current decision: reviewer-ready only. Owner integration must preserve the exact
source inventory, rerun native qualification and perform fresh owner acceptance;
no training admission is claimed. The next useful action after acceptance is to
monitor broader learned or newly proposed rivals beyond the finite self-audit set.

