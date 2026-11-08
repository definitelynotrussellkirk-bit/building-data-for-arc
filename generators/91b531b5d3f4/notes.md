# Working notes: 91b531b5d3f4

## 2026-09-28 review

### Finding

Version 2.1.0 separately generated two useful negative branches—markers under
zero headers and non-marker distractors—but never composed them. Its distractor
profile also excluded all header colors from the body. Consequently, a learner
could retain shortcuts such as “recolor every nonzero cell in an active column”
or “treat marker and header-palette colors as column labels,” while the checker
had no executable semantic contract to expose the ambiguity.

### Selected change

Version 3.0.0 replaces the probabilistic three-profile mixture with a
four-position schedule indexed by `sample_index`:

- `canonical`
- `empty_column_witness`
- `distractors`
- `mixed_witnesses`

The canonical position draws one complete official linked morphology rather
than recombining marginals. The mixed position contains both negative branches,
a neutral distractor below a live header, a distractor below an empty header,
and—on default draws with at least two headers—a header-colored body cell below
a different live header. Four consecutive default examples therefore refute all
declared rivals while retaining a 25% strict-profile rate.

### Executable contract

The generator now declares `strict_canonical_like`, `SEMANTIC_WITNESSES`,
`SEMANTIC_RIVALS`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`,
`LESSON_COMPETITORS`, `lesson_identifiable`, `EXAMPLES_NEEDED=4`,
`MIN_STRICT_FRAC=0.20`, and the deterministic schedule metadata expected by the
shared semantic gate.

Focused tests first failed because these hooks and the mixed profile did not
exist, then passed after implementation. The task-local
`workspace/curriculum_probe.py` checks complete windows and writes JSON evidence
for future reviews.

### Limitations

- The complete curriculum guarantee is for consecutive sample indices. A data
  loader that retains only one residue modulo four can collapse the profile mix;
  lesson packaging should preserve or deliberately rebalance schedule slots.
- The mixed scenes are lawful extrapolations of the Racket rule, not claims that
  the official ARC examples visibly contain those distractors.
- The Python mirror exists only to state executable rivals and lesson checks.
  The canonical Racket authority remains unchanged and must still be exercised
  by the repository battery.
- Explicit overrides remain authoritative. In particular, forcing one header in
  a mixed scene cannot create a “different live header” conflict, although the
  scene remains structurally valid and exposes the other negative branches.

Imported associated notes retain original evidence and timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `9e08948b094a2b4955b37aba9fd86652d08875d60fa7b73268a8ea3913f95fd3`.

# Decisions: 91b531b5d3f4

## D1 — Preserve the selected Racket rule

**Original rationale:** The retained rule interprets row 0 as column headers and
recolors only body cells equal to 1 when the header in that column is nonzero.
The exact original design rationale is not recorded, but all three normalized
canonical inputs and outputs support it.

**Alternatives considered:** Change the rule to recolor every marker regardless
of zero headers; recolor all nonzero body cells under live headers; or constrain
the rule to official dimensions/profiles.

**Probe:** Canonical execution, rule smoke, and authority synchronization all
pass. Each alternative is contradicted by a generated witness in version 3.0.0.

**Decision:** Keep the Racket source unchanged.

**Failure modes / limitations:** Generated counterfactuals define lawful
extensions beyond the visible official examples. They should remain tied to the
selected authority and not be treated as independent proof of intended human
semantics.

## D2 — Keep official morphology linked, not marginally recombined

**Original rationale:** Prior evidence correctly observed that dimensions,
header columns, and per-header marker counts occur as complete linked tuples.
Independent marginal draws can make attractive but unsupported
“canonical-like” scenes.

**Alternatives considered:** Draw official dimensions, columns, and marker
counts independently; eliminate official profiles; retain a 30% random prior.

**Probe:** `_canonical_profile_signature` accepts the three canonical profiles,
rejects a lawful marginal recombination, and every band reaches all three linked
profiles in focused tests.

**Decision:** The canonical schedule slot chooses one complete tuple from
`_CANONICAL_PROFILES`.

**Failure modes / limitations:** The profile list must be regenerated if the
canonical source changes.

## D3 — Replace probabilistic profile choice with a four-slot schedule

**Original rationale:** Version 2.1.0 used a 30% canonical prior and randomly
selected one of three mutually exclusive textures. It gave useful aggregate
coverage but no lesson-level guarantee.

**Alternatives considered:** Keep random mixing and increase sample count; use a
three-slot schedule; sample a mixed profile only probabilistically.

**Probe:** For every starting residue tested in every band, four consecutive
default samples contain exactly the declared four profiles and exactly one
strict canonical anchor. The shared semantic gate reports 12/12 identifiable
lessons.

**Decision:** `sample_index % 4` schedules `canonical`,
`empty_column_witness`, `distractors`, and `mixed_witnesses`.

**Failure modes / limitations:** Nonconsecutive or residue-biased data loaders
can destroy this guarantee. This schedule is deterministic by design, so
curriculum packaging must understand the four-slot period.

## D4 — Add a composition profile

**Original rationale:** Unknown in the predecessor because no composition
profile existed. Source inspection showed the two negative branches never
co-occurred.

**Alternatives considered:** Add more isolated examples; allow arbitrary random
mixtures; add only one palette-conflict cell.

**Probe:** Every default mixed draw has at least one unchanged marker below an
empty header, three to five distractors, distractors below live and empty
headers, a non-header distractor color, and—because default mixed draws use at
least two headers—a header-colored body cell under a different live header.

**Decision:** Make the mixed profile a mandatory fourth lesson slot.

**Failure modes / limitations:** It is a lawful extrapolation and deliberately
more adversarial than the canonical examples. Explicit `header_cols=1` cannot
realize the different-live-header subcase.

## D5 — Use one strict anchor per complete lesson

**Original rationale:** Version 2.1.0 targeted roughly 30% strict official
profiles to keep canonical support visible in every band.

**Alternatives considered:** Preserve 30% probabilistically; use 50%; remove the
strict floor in favor of only generalized scenes.

**Probe:** The deterministic lesson rate is 25%, and the shared census measured
26.7% because some generalized draws also happen to match a strict profile.
All canonical signatures remain reachable in every band.

**Decision:** Declare `EXAMPLES_NEEDED=4` and `MIN_STRICT_FRAC=0.20`; schedule
one explicit strict anchor per four examples.

**Failure modes / limitations:** The pooled measured rate can differ slightly
from 25% because strictness is an observed grid property, not merely a schedule
label.

## D6 — Dimension ranges remain difficulty-banded

**Original rationale:** Existing easy/medium/hard ranges scale visual load while
keeping the same semantic rule.

**Alternatives considered:** Use only canonical dimensions; use one full range
for all bands; enlarge beyond the declared 5..12 by 6..13 envelope.

**Probe:** Override boundaries at 5×6 and 12×13 pass for every texture; the
19,260-draw override gate passes.

**Decision:** Preserve the existing band ranges and full-range explicit
overrides.

**Failure modes / limitations:** Difficulty changes size and witness count, not
logical depth. It should not be interpreted as a calibrated model-difficulty
measure.

## D7 — Require two or more headers for default mixed examples

**Original rationale:** A palette-aware shortcut can only be contradicted by a
header-colored cell under a *different* live header when at least two distinct
headers exist.

**Alternatives considered:** Place the conflict below a zero header; allow one
header and omit this witness; reject explicit one-header overrides.

**Probe:** Every default mixed scene fires
`misaligned_header_color_preserved`; the semantic gate observed 149/600 such
witnesses and verified 60/60 rival claims.

**Decision:** Raise only the default mixed lower bound to two headers; continue
to honor explicit one-header overrides.

**Failure modes / limitations:** The override case necessarily weakens this one
witness and therefore should not be used alone as a complete lesson.

## D8 — Retain marker-count bands and reserve live-column space

**Original rationale:** Existing bands provide one to four fired marker examples
per header. Distractor profiles need a free cell under a live header.

**Alternatives considered:** Place markers densely and retry distractors; cap
all bands at one marker; allow distractors to overwrite markers.

**Probe:** Strict defect lint and all explicit size/texture boundary tests pass;
no generated scene fails `self_check`.

**Decision:** Preserve banded marker counts and cap the maximum at `h - 2` in
profiles that need a live-column distractor.

**Failure modes / limitations:** This is a construction constraint, not part of
the semantic rule.

## D9 — Keep isolated distractor profile simple; make mixed profile adversarial

**Original rationale:** Version 2.1.0 used one non-header distractor color to
make the negative branch visually legible.

**Alternatives considered:** Permit arbitrary palettes in every distractor
example; reuse header colors in the isolated profile; remove the isolated
profile after adding mixed examples.

**Probe:** The isolated profile remains easy to classify and always places one
distractor below a live header and one below an empty header. The mixed profile
adds palette reuse and multiple colors, so both simple and adversarial lessons
are present.

**Decision:** Retain the simple isolated profile and concentrate ambiguity-
breaking palette reuse in `mixed_witnesses`.

**Failure modes / limitations:** A learner seeing only isolated distractor slots
can still infer a palette shortcut; complete lesson packing is essential.

## D10 — Declare executable rivals and witnesses

**Original rationale:** No predecessor semantic hooks existed, so the baseline
checker could report only `NO_CONTRACT`.

**Alternatives considered:** Document the rule only in prose; add witnesses
without rivals; rely on aggregate diversity and morphology gates.

**Probe:** The semantic gate verifies five witness predicates, five witness-to-
rival claims, all canonical-compatible shortcut claims, and 12 identifiable
lessons.

**Decision:** Declare four rivals:

- erase markers below empty headers;
- recolor every nonzero cell below a live header;
- recolor markers and header-palette cells;
- apply the rule only to official profiles.

**Failure modes / limitations:** The rival set is intentionally finite. Passing
it does not prove that no other shortcut exists, only that these concrete,
plausible alternatives are excluded.

## D11 — Add a task-local curriculum probe

**Original rationale:** Shared gate output is comprehensive but difficult to
reuse while iterating on one generator.

**Alternatives considered:** Add no tool; modify shared infrastructure; embed a
large ad hoc script in review notes.

**Probe:** The tool's test passes; a 12-window run in each band reports complete
profile counts, all four rivals refuted, and zero failures. Output is JSON-safe.

**Decision:** Add `workspace/curriculum_probe.py` and its focused test without
changing shared tooling.

**Failure modes / limitations:** It uses the Python rule mirror and therefore is
not an authority check. The full Racket battery remains mandatory.
