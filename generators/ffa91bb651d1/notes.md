# Working notes: ffa91bb651d1

## Review repair `review-4f4dddb9578ba804`

Baseline generator SHA-256:
`b6313c84a93bd8addd04311c398f9aaccc0336c2c3e8dd8def2cc40ad052c2af`.
Final generator SHA-256:
`a989f2a63eab83e202a0b2d38e2ce18f7903404fe8bcf1833899ba5dcb73c303`.
The selected Racket rule was not changed; `RULE_HASH` is pinned to
`021dbc79a954`.

The prior return `review-982f0e4fdc7f4c34:v0001` was used only as a lead. Its
source-bound audit reported four inert controls and the missing rule pin. The
current packet reproduced those issues independently in the before battery.

### Design decisions

- Replace nine partly fictitious axes with five exact, observable controls:
  `grid_h`, `grid_w`, `n_targets`, `scene_pattern`, and `palette_count`.
- Keep the full legal ranges constructive in every difficulty band; difficulty
  changes profile weights, not legality.
- Weight exact canonical size/palette profiles heavily without copying canonical
  layouts.
- Alternate `canonical` and `comprehensive` scenes. Every consecutive
  three-demonstration lesson contains a comprehensive scene even under any
  one-query rotation.
- In one comprehensive scene, combine a repeated pair plus singleton, a gapped
  vertical exact pair, and two rather than three target rows. These independently
  refute the three declared canonical-fitting rivals.
- Reject unknown and invalid controls instead of silently accepting them.

### Retained probe

`workspace/reference_probe.py` independently reimplements the intended rule and
all declared rivals, checks all 128 boundary joint-override combinations,
exercises 100 draws per band, and verifies all four query rotations for 40
consecutive schedule starts per band. It is intentionally separate from the
semantic helpers in `generator.py`.

### Remaining limit

The declared rivals are the strongest task-specific alternatives found, not an
exhaustive proof of unique induction over all possible programs. The generator
also deliberately limits lawful inputs to 6–16 rows, 8–16 columns, six or seven
total colors, two or three target rows, and the documented negative-row family.
## Current reviewer considerations

Source SHA-256: `a989f2a63eab83e202a0b2d38e2ce18f7903404fe8bcf1833899ba5dcb73c303`.

# Decisions: ffa91bb651d1

## D1 — Keep the selected authority unchanged

**Choice.** Pin `RULE_HASH = "021dbc79a954"` and leave the selected Racket rule and canonical data untouched.

**Rationale.** The rule smoke and independent Python mirror both reproduce all five canonical outputs. The defect was in generation and teaching support, not in the transformation. Changing the rule would enlarge risk without resolving the inert-control or ambiguity defects.

**Alternatives rejected.** Reinterpret a row as “fill every color that appears twice,” or allow the same exact-pair rule in columns. Both fit all canonical pairs but are not the written/selected whole-row rule. Their disagreement is now encoded as executable rivals.

**Probe and failure mode.** The task tests compare an independent whole-row oracle with all canonical pairs. Authority sync and rule smoke cover source identity and execution. A future selected-rule change will fail the pinned hash, canonical oracle test, or authority checks.

## D2 — Replace fictitious controls instead of cosmetically wiring them

**Choice.** Remove `palette_kind`, `n_spans`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture`; expose only `grid_h`, `grid_w`, `n_targets`, `scene_pattern`, and `palette_count`.

**Original rationale.** Unknown. The imported baseline described a broad generic sparse-grid template, but ordinary generation ignored several advertised controls and mixed helpful and degenerate texture meanings.

**Rationale for repair.** A small exact surface is easier to honor, observe, and test. Each retained control is semantically relevant or structurally visible in returned pixels. `observe_overrides()` is the explicit inverse used by the shared checker.

**Alternatives rejected.** Keeping aliases for backward compatibility was rejected because aliases would preserve ambiguous provenance and make joint-control verification harder. Adding separate warm/cool palette names was rejected because ARC colors do not have a task-relevant semantic temperature here.

**Probe and failure mode.** The final override stage covers 260 cases and 23,400 accepted draws. Task tests exercise every joint exact combination at the smallest legal shape and reject unknown, wrong-type, and out-of-range controls. A dead or dishonest control becomes an override mismatch rather than silently surviving.

## D3 — Use 6–16 rows and 8–16 columns

**Choice.** Legal dimensions are `grid_h=6..16` and `grid_w=8..16` in every band.

**Rationale.** Height 6 is the smallest size that can simultaneously host two targets plus the required negative rows in a comprehensive scene. Width 8 leaves enough separated columns for a vertical witness, gapped horizontal pairs, a triple, and a pair-plus-singleton at the smallest boundary. Upper bounds preserve the packet’s intended ARC-scale grids.

**Alternatives rejected.** The baseline’s `grid_h=5` and `grid_w=6/7` claims were not retained because the full semantic contract is not constructively realizable there. Band-specific legal ranges were rejected because exact controls should not unexpectedly become invalid when difficulty changes.

**Probe and failure mode.** All boundary joint combinations pass in `checks/reference-probe.json`. The shared override gate samples the full ranges. `self_check()` rejects out-of-domain dimensions.

## D4 — Use six or seven total colors, including background

**Choice.** `palette_count` is exactly 6 or 7 total distinct colors including zero.

**Rationale.** These are the canonical palette counts. Six colors are sufficient to assign the independent roles in the smallest comprehensive case; seven adds variation and owns every canonical profile. Colors are selected from 1–9 without attaching extra semantics to specific values.

**Alternatives rejected.** A two-color minimum was rejected because it cannot independently vary the target and negative roles without creating accidental alignments and extra shortcuts. Nine foreground colors was rejected because it drifts from all canonical profiles and adds no rule evidence.

**Probe and failure mode.** `self_check()` measures the returned palette directly. Profile-floor and independent probe results record exact cross-band support. Joint override tests cover both counts for both scene types and both target counts.

## D5 — Weight canonical profiles, but do not copy canonical layouts

**Choice.** Draw a weighted anchor from the five canonical `(height, width, palette_count)` profiles, then give every legal axis value nonzero support with an 80-copy anchor weight.

**Rationale.** The generator should remain visibly task-linked and satisfy profile-floor checks, while still producing novel scenes. Weighting dimensions and palette count independently provides support outside the five exact tuples without importing canonical coordinates.

**Alternatives rejected.** Sampling uniformly over the full rectangular domain failed the practical profile floor too often. Emitting canonical inputs directly would overfit and would not teach the negative cases absent from the public examples.

**Probe and failure mode.** The official 60-draw profile gate got 53 exact hits and 55 envelope hits. The independent 300-draw probe got 82–84 exact hits per band and records the complete profile histogram. A future weight change that eliminates exact support will fail both the shared gate and task-local test.

## D6 — Alternate two scene patterns deterministically

**Choice.** Ordinary `sample_index` parity alternates `canonical` and `comprehensive`; an exact `scene_pattern` override can request either.

**Rationale.** With three demonstrations and one query, every four-pair window under any query rotation must leave at least one comprehensive demonstration. Strict alternation guarantees two comprehensive and two canonical pairs in every consecutive four-pair bundle, so holding out any one still leaves a comprehensive witness.

**Alternatives rejected.** Independent random scene selection was rejected because even a healthy marginal witness rate leaves a nonzero probability of an all-canonical lesson. A longer schedule was unnecessary. Making every draw comprehensive was rejected because canonical-profile ambiguity is useful to demonstrate why the negative example matters and because it would narrow the visual curriculum.

**Probe and failure mode.** The independent probe enumerates 40 consecutive starts per band and all four query rotations. The source-bound census tests 100 starts per band and all rotations. Any schedule regression that leaves a rival alive is reported by `lesson_identifiable()`.

## D7 — Canonical scene contents

**Choice.** A canonical scene contains two or three target rows, one mismatched two-color row, one three-of-a-kind row, and at most one singleton needed to realize the requested palette. Same-color vertical exact pairs are deliberately avoided.

**Rationale.** This owns the five canonical inputs and preserves all three observed canonical-fitting rivals. It provides positive examples and the two public negative row types without prematurely resolving the ambiguity.

**Alternatives rejected.** Adding a pair-plus-singleton to canonical scenes would erase the intended distinction between curriculum branches. Allowing accidental same-color vertical pairs could randomly refute the row-or-column rival and make lesson evidence depend on luck rather than schedule.

**Probe and failure mode.** `self_check()` classifies every row by color multiplicity. Canonical ownership tests accept all five public inputs. Tests prove every declared shortcut fits every public pair and canonical branch scenes.

## D8 — Comprehensive scene contents

**Choice.** A comprehensive scene contains two targets by default plus:

- one row with a repeated color pair and an outside singleton;
- a mismatch and triple aligned to create a gapped same-color vertical exact pair;
- enough role colors to realize the requested palette.

**Rationale.** One compact scene independently refutes all three canonical-fitting rivals while remaining lawful under the selected rule. Using two targets also makes the intended rule non-identity and refutes the global “exactly three targets” condition.

**Alternatives rejected.** Separate witness scene types were rejected because a rotated lesson might hide the only witness relevant to one rival. Putting the singleton inside the repeated span was rejected because the wrong per-color fill could overwrite it, complicating interpretation. A vertical witness using a target endpoint was rejected because it was harder to guarantee without accidental extra column structure.

**Probe and failure mode.** The semantic gate verifies each witness and its claimed rival. Each comprehensive draw in the independent probe disagrees with all three rivals. `self_check()` requires the vertical witness whenever a pair-plus-singleton row is present.

## D9 — Make every target transformation nontrivial

**Choice.** Matching endpoints must have at least one zero cell between them; targets with adjacent endpoints are rejected.

**Rationale.** Adjacent equal cells technically satisfy the predicate but produce no pixel change. A curriculum dominated by identity targets weakens evidence and can conceal broken or identity rules.

**Alternatives rejected.** Allowing adjacent endpoints as low-probability texture was rejected because they add no new rule information and complicate non-identity guarantees.

**Probe and failure mode.** Pair constructors require a gap. `self_check()` rejects adjacent two-cell rows. The independent probe observed zero identity transformations in 300 ordinary draws.

## D10 — Declare rivals as executable code

**Choice.** Expose the same three pure deterministic functions through `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; map each witness through `WITNESS_RIVALS`.

**Rationale.** The shared semantic gate and lesson census should execute the actual hypotheses rather than rely on prose. A shared dictionary avoids rival-name drift between curriculum claims and lesson scoring.

**Alternatives rejected.** A handwritten witness checklist without predictions was rejected because it cannot establish that the witness actually changes a rival’s output. Duplicating separate rival implementations for each hook was rejected because they could diverge.

**Probe and failure mode.** Task tests independently reimplement every rival and compare the declared name set. The reusable probe iterates the declarations. The official semantic gate verifies canonical fit and witness disagreement.

## D11 — Keep degenerates outside ordinary generation

**Choice.** Do not advertise blank, mismatched-only, single-endpoint-only, or malformed “texture” modes as ordinary exact controls.

**Rationale.** The assignment requires useful training lessons, not a mixed ordinary/negative domain. The selected comprehensive branch already provides lawful negative evidence while guaranteeing a non-identity target.

**Alternatives rejected.** Retaining the baseline degenerate aliases was rejected because the defect lint correctly identified domain overlap and because some modes would remove all positive evidence.

**Probe and failure mode.** `strict_canonical_like()` is identical to `self_check()` and the final semantic gate measured 600/600 strict-lawful draws. Malformed near misses are covered in task tests.

## D12 — Limits and future extension

The generator deliberately covers a task-linked teaching manifold, not every grid on which the Racket rule is defined. It does not vary to one target, more than three targets, palettes outside six/seven total colors, or arbitrary combinations of distractor rows. Extending those domains should be done only with constructive boundary tests and another all-rotations lesson check. The finite three-rival set is strong evidence against the observed shortcuts, not a proof against every describable alternative program.
