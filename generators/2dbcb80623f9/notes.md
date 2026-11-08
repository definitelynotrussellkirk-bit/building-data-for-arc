# Working notes: 2dbcb80623f9

## Root cause

Version 2.0.2 generated only positive clear-diagonal examples while advertising eight controls, several of which were ignored, aliases, fixed singletons, or invalid/no-op textures. Difficulty silently narrowed declared override domains, scalar overrides were coercive, unknown keys were accepted, and `self_check` rejected the canonical oblique distractor. The canonical labels therefore admitted the plausible shortcut “connect every clear straight pair,” while generated lessons supplied no counterexample.

## Repair choices

- Kept the unchanged Racket rule as label authority and pinned `RULE_HASH = 1c2557609ca3`.
- Reduced the public contract to four exact, pixel-observable axes: `grid_h`, `grid_w`, `n_pairs`, and `n_distractors`.
- Replaced rejection sampling with a finite constructive search over cached segment geometry. Every declared cross-product combination is realizable, including `8x8`, four diagonal pairs, and two distractors.
- Default samples use exactly three foreground colors on the four canonical shape profiles. Samples with index modulo three equal to 1 or 2 contain a clear horizontal/vertical distractor; any consecutive four samples therefore contain at least two shortcut-refuting witnesses, including under held-out-query rotation.
- Validator accepts the canonical non-diagonal distractor, enforces exact color multiplicity, clear separated diagonals, and disjoint connectable paths.
- Added an independent Python geometry oracle, an explicit axis-or-diagonal rival, source-bound regression tests, and a reusable probe under `workspace/`.

## Authority and limits

The Python oracle and rival are supplementary diagnostics, not labels. Semantic declarations establish counterexamples only for the named finite rival; they do not prove uniqueness against arbitrary hypotheses.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `81ce79fdd5ce12922a82dd30e093edadf7f1082ef8d949605ad591e57bc08dd4`.

# Decisions for 2dbcb80623f9

## D1 — Preserve the Racket authority

**Prior state.** The canonical Racket program already produced the intended
labels and passed rule smoke, Racket lint, and authority synchronization in the
baseline battery.

**Decision.** Leave the Racket rule and canonical data untouched and pin
`RULE_HASH = "1c2557609ca3"` in the Python generator.

**Reason.** The failures were in input support, declared controls, validation,
and lesson identifiability—not in the label authority. Changing a correct rule
would have enlarged the review surface without addressing the root cause.

**Evidence.** Before and after authority-set SHA-256 are both
`8eda1d877cde35d1edd6ab791fa18fc980921dfd3c84e90c9a59ae4b6661ea4f`;
final rule smoke, Racket lint, and authority sync are green in
`checks/after/checks/2dbcb80623f9_after_battery_summary.json`.

**Rejected alternative.** Modify the Racket rule to reject or erase the canonical
non-diagonal pair. That would change the task rather than repair the generator.

## D2 — Replace eight misleading controls with four exact observable axes

**Prior state.** Version 2.0.2 advertised grid size, pair count, palette aliases,
fixed singleton categories, and texture variants. Some were duplicates, some
were dead, some were invalid negative fixtures inside the ordinary domain, and
difficulty silently narrowed legal values.

**Decision.** Expose only `grid_h`, `grid_w`, `n_pairs`, and `n_distractors`, with
fixed global domains 8–14, 8–14, 1–4, and 0–2. Make every override exact and
recoverable from pixels through `observe_overrides`.

**Reason.** A smaller truthful control surface is more useful than nominal
variety that cannot be observed or composed. These four axes describe actual
independent properties of the generated input.

**Evidence.** The strict override gate is green; the focused test realizes
`8×8`, four connectable pairs, and two distractors in all four band settings and
independently recovers the requested values.

**Rejected alternatives.** Keep `palette_size` and `n_distinct_colors` as
aliases; keep singleton `density`/`position_bias`; or label dead controls
“diagnostic.” Each preserves misleading API surface without producing distinct
training examples.

## D3 — Use strict input validation instead of coercion

**Decision.** Reject booleans, strings, floats, negative sample indices, unknown
bands, unknown axes, and out-of-range values before creating a generation
context.

**Reason.** Silent coercion and swallowed typos make an exact override contract
unfalsifiable and can corrupt experiment metadata.

**Evidence.** Eleven malformed-call regressions fail before the repair and pass
after it; final lint, defect lint, and override stages are green.

**Rejected alternative.** Preserve permissive Python integer coercion for
backward compatibility. The baseline showed that this accepted invalid scalar
values and obscured caller errors.

## D4 — Construct support deterministically rather than reject-sample it

**Decision.** Enumerate finite candidate diagonal and axis segments, shuffle each
pool with keyed RNG, prefer a band-specific length, and use bounded backtracking
to choose disjoint footprints.

**Reason.** This makes every declared cross-product combination constructive,
including the densest legal request, while retaining seed-driven variation.
Disjoint full footprints prevent endpoint collisions, path crossings, and later
semantic interference.

**Evidence.** The exact-override cross-product passes the native override gate;
the focused worst-case and 320-default-draw probes all satisfy `self_check` and
independent disjointness checks.

**Rejected alternatives.** Rejection sampling with a retry cap could fail
selectively on small grids; copying canonical grids would pass profiles but
collapse diversity; allowing path crossings would create order-dependent labels
or ambiguous object ownership.

## D5 — Match canonical profiles without copying canonical instances

**Decision.** Default grid shapes rotate through `(9,12)`, `(10,10)`, `(10,13)`,
and `(11,11)`. Defaults contain exactly three foreground colors while geometry
and colors remain seed-dependent.

**Reason.** The baseline profile floor showed weak and band-dependent support.
The selected schedule represents every canonical shape while retaining fresh
instances rather than memorizing the ledger.

**Evidence.** Profile floor and diversity are green; focused tests see all four
shapes and both diagonal slopes in each band.

**Rejected alternatives.** Uniformly sample every 8–14 size by default. That
would satisfy range diversity but make canonical-profile support unnecessarily
rare. Exact overrides still provide the full declared size domain.

## D6 — Add a minimal negative witness for the canonical-compatible rival

**Observed rival.** “Connect every clear straight same-color pair” fits all four
labeled canonical pairs because the canonical non-diagonal distractor is
oblique, not horizontal or vertical.

**Decision.** Use clear horizontal/vertical pairs as ordinary distractors and
declare the executable rival `axis_or_diagonal`, witness `axis_distractor`, and
`lesson_identifiable` hook. The default index pattern is `0,1,1` distractors,
paired with `3,2,2` connectable diagonals.

**Reason.** An axis pair is the smallest local intervention on which the intended
rule and rival disagree. Two witness-bearing examples in every consecutive four
make all one-query rotations identifiable from the remaining three examples.

**Evidence.** `test_axis_rival_fits_all_canonical_pairs_but_generated_witness_refutes_it`
proves canonical fit and generated disagreement. The 12-start rotation test and
1,200-rotation census report no surviving declared rival.

**Rejected alternatives.** Randomly include a distractor. Witness frequency does
not ensure every assembled lesson contains one, especially after query rotation.
Making every sample a distractor-bearing sample was unnecessary and would reduce
positive-only structural variation.

## D7 — Keep the validator broader than the default negative distribution

**Decision.** Count every non-diagonal two-cell color pair as a lawful distractor,
not only horizontal/vertical pairs. Generate axis distractors by default because
they refute the selected rival.

**Reason.** The canonical ledger contains an oblique non-diagonal distractor. A
validator restricted to generated axis examples would again reject canonical
support and conflate the teaching intervention with the rule domain.

**Evidence.** All four canonical labeled inputs pass `self_check`, while default
axis witnesses also pass. The independent geometry oracle matches every
canonical label.

**Limitation.** Ordinary generated distractor geometry is narrower than validator
support. Future work may add oblique distractors after preserving guaranteed
axis-witness coverage.

## D8 — Keep Python mirrors diagnostic, never label-authoritative

**Decision.** Put an independent geometry oracle and rival in
`workspace/reference_probe.py`; use them for regressions and semantic comparison.
Continue obtaining production and census labels from the selected canonical
Racket rule.

**Reason.** Independent implementations catch generator and contract mistakes,
but a Python mirror must not silently become a second authority.

**Evidence.** The final battery and lesson census record the Racket rule source,
callable, generator, controller, and runtime hashes. The workspace README states
the authority boundary explicitly.

## D9 — Preserve honest solve provenance

**Decision.** Keep the blind-before-repair solve separate from the exposed
post-repair solve. Declare `earlier_rule_exposure = yes` for the latter and leave
masked query labels unknown.

**Reason.** A successful exposed solve is useful evidence that visible examples
express the rule, but it is not an independent blind evaluation.

**Evidence.** `solve-blind/summary.json` and `solve/summary.json` each bind one
attempt, its exact program/notes, instance, generator, and exposure declaration.

## D10 — Treat passing finite rival checks as bounded evidence

**Decision.** Report “no ambiguity found against declared/searched rivals,” not
“the rule is uniquely identifiable.”

**Reason.** Neither the semantic gate nor a 300-lesson census can quantify over
all programs a model might infer.

**Remaining failure modes.** A new positional, color-rank, or global-statistic
shortcut could survive the current named rival set; exact-grid uniqueness does
not imply semantic diversity; and generated defaults do not cover every legal
joint override in their natural frequency. These are limitations, not blockers
to the repaired contract.
