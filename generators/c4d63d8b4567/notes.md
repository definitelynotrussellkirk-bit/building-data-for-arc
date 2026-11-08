# Working notes: c4d63d8b4567

Imported associated notes retain original evidence and timestamps in
`evidence/associated_notes.jsonl`.

## 2026-10-02 review

### Finding

The v3.0.0 generator and all five canonical examples used every nonzero color
exactly twice in the whole grid. That distribution supported a plausible but
wrong shortcut: reject a color unless its global multiplicity is exactly two,
then apply the otherwise-correct row/column span rule. The shortcut matched all
five canonical pairs and 600 sampled v3.0.0 generations.

The authoritative rule is line-local, not grid-global. A color may occur three
or more times overall while still occurring exactly twice on a particular row
or column. The concrete review witness places a clear horizontal pair and one
extra off-axis occurrence of the same color; the bundled Racket authority fills
the horizontal span, while the global-count shortcut leaves it unchanged.

### Selected change

Version 3.1.0 turns schedule profile 3 into a repeated-color witness. One active
horizontal color receives exactly one extra cell that is off-axis from both
endpoints. The structural checker accepts this narrowly defined three-cell
case only when it exposes exactly one clear aligned pair. A named
`global_exactly_two` rival and `repeated_color` witness make the semantic gate
retain the distinction.

### Alternatives considered

- Relax every color to arbitrary multiplicity. Rejected because it would make
  the teaching grammar much harder to validate and could introduce several
  simultaneous row/column segments with ambiguous interactions.
- Add a fifth schedule profile. Rejected because four examples are the declared
  lesson size; extending the schedule would weaken sliding-window guarantees.
- Change the canonical Racket program. Rejected because direct execution of the
  counterexample matched the Python mirror; the authority was already correct.

### Remaining limits

The generated grammar is intentionally narrower than the full legal Racket
input domain. It permits at most one repeated color, exactly three occurrences
for that color, and exactly one clear aligned pair for it. It still does not
teach multiple independent segments of the same color, multiple repeated
colors, or denser scenes with several line-local counts. Those are possible
future curriculum expansions, not authority defects.
## Current reviewer considerations

Source SHA-256: `87a0aa06a16dc6fde1d432f0229154986038ef61c534f13ef18bf38c9c09d0f1`.

# Decisions: c4d63d8b4567

## Authority and scope

**Choice:** Keep the canonical Racket program unchanged.

**Original rationale:** The existing generator already declared the canonical
rule hash and its Python mirror matched all public pairs. The exact review
counterexample was executed through the bundled protected Racket runtime and
matched that mirror.

**Alternatives considered:** Patch the Racket rule to require global
multiplicity two; rewrite it for style warnings; broaden it to consume a
precomputed component representation.

**Decision:** Reject all three. A global count would encode the identified wrong
shortcut. The style findings are advisory and unrelated. The current authority
already implements the written row/column rule correctly.

**Failure mode retained:** The authority supports denser legal inputs than this
generator currently teaches.

## Canonical canvas and palette profiles

**Choice:** Preserve the five public dimension/color-count profiles:
`7x8/2`, `8x9/2`, `7x10/2`, `9x9/3`, and `8x10/2`.

**Original rationale:** Inferred from the code and canonical-profile gate: exact
public shape and nonzero-color support prevents morphology drift while endpoint
placement, colors, orientations, and spans provide variation.

**Alternatives considered:** Add novel canvas sizes; collapse to one size; vary
the number of colors independently.

**Decision:** Preserve them during this bounded repair. The profile floor was
already clean, and changing unrelated morphology would make the semantic delta
harder to attribute.

**Probe:** Exact-profile support remained 60/60 after the change.

**Limit:** Canvas and color-count support remains tied to the public examples.

## Four-example schedule

**Choice:** Retain a four-profile cyclic schedule, indexed by
`sample_index % 4`.

**Original rationale:** Every four consecutive demonstrations should expose all
main preconditions, regardless of starting index.

**Alternatives considered:** Add a fifth profile solely for repeated colors;
make profile selection random; replace one existing lesson.

**Decision:** Fold the new witness into profile 3. A fifth profile would violate
the declared `EXAMPLES_NEEDED = 4`; random selection would lose the sliding
window guarantee; removing blocked or off-axis examples would resurrect known
rivals.

**Probe:** Eight rolling starts for each of 50 seeds and all three bands yielded
zero unrefuted four-example windows.

**Limit:** A fixed cycle is pedagogically explicit but makes lesson category
predictable from sample index.

## Profile 0: mixed clear orientations

**Choice:** Keep non-overlapping clear horizontal and vertical spans, plus a
third clear span for the three-color profile.

**Original rationale:** Refutes horizontal-only and vertical-only rules and
makes the transformation fire more than once.

**Alternatives considered:** Cross active spans or allow shared endpoints.

**Decision:** Keep spans disjoint. Crossing clear spans can make output order
matter and would entangle curriculum semantics with conflict resolution.

**Probe:** Both orientation witnesses continue to fire across all bands.

## Profile 1: blocked aligned pair

**Choice:** Keep one clear active span and one aligned pair whose interior
contains a blocker; require the blocked span to have length at least four.

**Original rationale:** Distinguishes “interior must be entirely zero” from
“connect through obstacles.” Length at least four leaves an empty interior cell
that the blocker-ignoring rival would visibly recolor.

**Alternatives considered:** Use only an `A-X-A` length-three pattern or several
blockers.

**Decision:** Preserve the calibrated construction. The shorter pattern can be
answer-equivalent for an overaggressive rival, while multiple blockers add no
new rule distinction.

## Profile 2: off-axis same-color pair

**Choice:** Keep a clear active span plus one diagonal/off-axis same-color pair.

**Original rationale:** Refutes rules that connect any two equal colors without
requiring a shared row or column.

**Alternatives considered:** Use diagonal lines as outputs or remove the active
pair.

**Decision:** Keep an active pair so every normal sample remains
non-identity, and keep the off-axis pair unchanged.

## Profile 3: repeated-color witness

**Choice:** Start from several disjoint horizontal clear spans. Give the first
active color one additional cell outside every active span, on a different row
and in neither endpoint column.

**Original rationale:** The prior profile supplied the multiple-active-pairs
lesson but gave every color global multiplicity two. The new placement keeps
that lesson while falsifying the newly identified global-count shortcut.

**Alternatives considered:** Put the third cell anywhere free; add a repeated
color to every profile; allow four or more occurrences; add another independent
aligned pair of the same color.

**Decision:** Use one carefully off-axis singleton in profile 3 only. Arbitrary
placement can create unintended row/column pairs. Repetition in every profile
would overrepresent the edge case. Four-plus occurrences or multiple segments
would require a larger structural and conflict-policy design.

**Probes:** The retained audit observed exactly 1,200 repeated witnesses in
4,800 cases, one per audited four-example window. The named rival disagreed on
all 1,200. Protected Racket matched the mirror on 150 generated profile-3
cases.

**Limits:** Only one repeated color is allowed and it has exactly one aligned
pair.

## Structural validation of repeated colors

**Choice:** Accept a three-cell color only when exactly one of its three pairs
is aligned and that pair has a zero interior. Reject two repeated colors,
blocked repeated pairs, adjacent endpoints, or repeated layouts exposing zero
or multiple aligned pairs.

**Original rationale:** This is the smallest grammar relaxation that admits the
required witness while maintaining an unambiguous teaching record.

**Alternatives considered:** Accept any three-cell color and let the authority
sort it out; validate only the constructor output; make the checker reproduce
the full unrestricted authority domain.

**Decision:** Keep validation narrow and explicit. Permissive acceptance would
let accidental extra segments pass. Constructor-only checks would make
canonical and mutation validation weak. Full-domain validation is beyond the
bounded repair.

**Mutation decision:** Replace the obsolete “three occurrences is always
invalid” fixture with an ambiguous three-cell layout that exposes two aligned
pairs and must still be rejected.

## Colors and nuisance variation

**Choice:** Continue drawing distinct nonzero ARC colors and varying layout and
span target through task-local deterministic RNG.

**Original rationale:** Color identity is irrelevant to the rule; distinct
colors keep endpoint ownership visible. Difficulty changes nuisance geometry
without claiming a non-observable public axis.

**Alternatives considered:** Tie colors to profile roles, use repeated endpoint
colors across objects, or expose span length as a public override.

**Decision:** Preserve color permutation and private span/layout variation to
avoid introducing role-color shortcuts or expanding the override contract.

**Limit:** Because color swaps are semantically lawful, a generic mutation
probe reports low rejection for color-swap mutations; this is expected rather
than a checker defect.

## Rival registration

**Choice:** Add the explicit `global_exactly_two` rival and map it only to the
`repeated_color` witness.

**Original rationale:** The baseline semantic gate can verify only rivals the
generator declares. Registering the discovered rule makes regression visible
in normal acceptance checks.

**Alternatives considered:** Rely only on the focused test or external review
notes.

**Decision:** Keep all three: declared rival/witness for the standard gate,
focused regression for schedule behavior, and a retained census for broader
review.

## Retained reviewer utility

**Choice:** Add `workspace/shortcut_audit.py` with canonical, generated-window,
and exact witness reporting.

**Original rationale:** The defect was a distribution-level shortcut that
ordinary morphology checks did not reveal. A reproducible rival census is more
useful to future agents than prose alone.

**Alternatives considered:** Keep only an ad-hoc notebook/command or add a
shared corpus-wide tool.

**Decision:** Keep it task-local. The global-count rival is specific to this
rule, and changing shared tooling is outside the assignment’s allowed scope.

**Failure mode:** The tool checks this named rival, not an open-ended synthesis
of all possible shortcuts.
