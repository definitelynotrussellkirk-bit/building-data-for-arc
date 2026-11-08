# Working notes: b86607f34b8b

## Review provenance

Assignment `review-535f1f762a14ec62` repaired imported v2.1.0 to v3.0.0.
Baseline SHA-256: `b8a16c7f1a55a2b04fc789c2751b306fa654d563cf6a3d36db8f01094221847f`.
Final generator SHA-256: `be164d9a707bba60eb2bea2e2d4e5d6477a90f5601afd4eaeacb881bdebdbe34`.
The selected canonical rule remains `6fa3fd6234a8`; no authority, shared code,
frozen test, audit target, or catalog approval was edited. Associated notes
were empty and no previous selected-task return was used as measured evidence.

## Why the input distribution changed

The old mode-specific row/column/L motifs exposed which operation to use without
reading the legend. The single L also failed to distinguish row-then-column
closure from reversed order or repeated closure. Mode 4 was never sampled,
the canonical shape/palette profile had 0/60 support in the before check, and
several advertised controls were ignored or rejected within their declared
ranges. The old docstring described an unrelated panel-sorting task.

All modes now start from the same motif family. Compact draws use three seeds
per color, flips, varied gaps, and no extra seeds. Broad draws use two disconnected
three-seed motifs and sometimes one additional original seed per color. Each
accepted board must retain its relevant diagnostic differences after actual
overlap arbitration. The Python reference projection selects informative inputs;
only the unchanged Racket rule supplies labels in authority checks and censuses.

Even indices default to 9x11 with four colors drawn from 1..4. Odd indices default
to 9..14 in both dimensions with five colors drawn from 1..8; easy favors smaller
dimensions and hard larger ones. Exact overrides supersede these preferences.
All difficulties retain both categories. The profile gate measures shape and
total palette size; it does not certify the entire canonical distribution.
Canonical examples have three body colors, available through `n_colors=3`.

## Controls and structural domain

| Exact control | Accepted values | Observable result |
| --- | --- | --- |
| `grid_h` | Integers 9..14 | Number of rows, including the three header rows |
| `grid_w` | Integers 9..14 | Number of columns |
| `n_colors` | Integers 3..5 | Distinct nonzero body colors |

Unknown controls, retired aliases, fractional values, booleans, strings, and
out-of-range integers fail explicitly. `None` requests the default. Retired
axes are `palette_kind`, `n_markers`, `palette_size`, `position_bias`,
`n_distinct_colors`, `density`, and `texture`; hidden `body_h` and `n` are not
supported. The range reduction is intentional: the broad teaching motif needs
six body rows and seven distinct columns, plus space for independent colors.
No incompatible combinations are declared. The 8,100-call final advertised
control matrix passed; that finite sample does not prove all seeds succeed.

`self_check` validates the structural task domain, not the teaching distribution:
rectangular integer grids, exactly one full 9 divider at row 2, unique colors
1..8 paired with modes 1..4, and equality of legend/body color sets. It accepts
the three canonical inputs and the sparse one/two-color authority witnesses.
Other executable Racket cases, such as moved separators or fallback mode codes,
remain outside the declared domain. Per-input teaching conditions belong in
sampling and lesson checks, not in this broader structural validator.

## Lesson schedule and finite rivals

Default four-pair windows contain two compact mode-4 examples and two broad
examples with three equal-mode colors. The broad examples each refute the
13 non-bridge rivals, while compact examples refute the three bridge rivals;
holding out any one input leaves a demonstration of both groups. The default
mode schedule has period six. This reasoning is for consecutive successful
draws; the public census separately checks the actual production materializer.

Explicit four-color requests use alternating mode sets `[1,3,3,4]` and
`[2,3,3,4]`. The larger tied color appears left,left,right,right across indices
modulo four. This separates mode presence from tie direction: both unconditional
and both conditional legend-order rivals are wrong twice per four-input window,
so every single query holdout retains a counterexample. Three-color requests
cannot expose equal-mode tie rules; the probe reports such rivals as surviving
all pairs, not as established knowledge. Broader tie support comes from the
four/five-color curriculum.

Declared rival families cover ignoring the legend, bounding boxes, reversed or
iterated double closure, row/column union, bridge erasure and orientation,
mode/color/legend priority, and unconditional or mode-dependent tie direction.
All 13 declared canonical-compatible shortcuts were checked against 3/3 usable
canonical pairs. Independent authority fixtures retain 11 small full outputs
and 26 explicit cell assertions, plus a separate three-color tie witness.

## Retained failures and limitations

An initial dense repair passed a 300-lesson census but failed the canonical
object-count gate and 42 legal override calls. Restoring sparse compact scenes
fixed density; a later four-color configuration still exhausted 512 candidates
and allowed Racket-confirmed ambiguous lesson rotations. A first tie schedule
repaired those cases but correlated tie direction with mode presence; a new
regression caught this and the period-four orientation schedule removed it.
Root `DECISIONS.md` and `checks/` in the return retain every failed stage and
the concrete counterexamples, with source hashes separating each iteration.

The final source passed all 12 battery stages, all 48 focused and portable task
tests, 300 production lessons / 1,200 query rotations, and 54 override windows /
216 rotations against 16 distinct rivals. These are finite measurements, not
proof of unique induction, universal seed success, or improved model accuracy.
Motif families, the compact/broad mix, and fixed header location remain deliberate
restrictions. Training approval remains with the maintainer.
## Current reviewer considerations

Source SHA-256: `be164d9a707bba60eb2bea2e2d4e5d6477a90f5601afd4eaeacb881bdebdbe34`.

# Decisions and failed alternatives

## Scope and authority

The immutable draw selected `b86607f34b8b`, assignment
`review-535f1f762a14ec62`. I repaired its input generator, descriptions, tests,
and authoring tools only. I found no reason to change the canonical Racket rule:
the important behavior already exists there, including one-pass operation order,
mode-4 seed removal, mode priority, and numeric-color ties. The final source is
`be164d9a707bba60eb2bea2e2d4e5d6477a90f5601afd4eaeacb881bdebdbe34`, v3.0.0.
The authority remains `6fa3fd6234a8`. No previous selected-task return or associated
notes supplied an earlier measurement; the original author's broader rationale
is unknown beyond comments in v2.1.0.

## D1: Make the legend necessary

The baseline deliberately aligned each body's geometry with its mode to avoid
identity examples. That solved a real local problem but supplied a shortcut:
row pairs, column pairs, and fixed Ls disclose the operation. I replaced these
with a common motif family across all modes and require the important rival
outputs to differ after conflicts are resolved. Pure random scatter was rejected
because it often creates no informative closure. A single L per color was also
rejected as the entire distribution because it cannot reveal reversed versus
one-pass double closure. The generator uses Python only as an input-selection
diagnostic; all measured labels come from Racket.

## D2: Preserve sparse support while teaching stronger witnesses

The first repair used six/seven seeds for every color on every board. It passed
an intermediate 300-lesson census, but `checks/after/` found its object counts
outside the canonical envelope: canonical median 15 versus generated 29..44,
tolerance 7. The failing density regression retained a minimum of 30 components.
That candidate was rejected despite its semantic-census success.

The final sampler alternates compact three-seed scenes with broad composite
motifs. Core scenes default to 9x11 and palette 1..4; broad scenes use larger
varied supports and three tied mode-3 colors. The shared final profile gate
records 29/60 exact shape/palette-size hits (easy 13/20, medium 8/20, hard 8/20),
versus 0/60 before. Canonical body-color count is three while defaults use four
or five; `n_colors=3` supplies that count. The profile check is a limited support
measure, not equivalence to the full canonical input distribution.

## D3: Replace inert controls with an observable contract

The old interface advertised nine axes, but height and count aliases were inert,
width support depended on difficulty, and palette/texture controls included
irrelevant or invalid constructions. I retained exact dimensions as integers
9..14 and introduced one exact body-color count, `n_colors=3..5`, with an
independent observer. Unknown/retired names and noninteger values fail explicitly.
All 90 advertised-control cases across seeds 0..29 and three bands passed the
final 8,100-call matrix; no incompatibility exemption was added.

This is an intentional major-version interface change. I rejected pretending
the old aliases worked or preserving invalid degenerates as normal training
inputs. I also rejected claiming support for tiny teaching canvases: the broad
motif needs six distinct body rows and seven columns before independent colors
are placed. The structural validator still accepts lawful sparse one/two-color
and canonical examples. The sampler's smaller domain is separate from the
validator and from the full executable Racket domain.

## D4: Keep teaching evidence in complete lessons

The 16 executable rivals include 13 fitting every canonical pair. They cover
legend omission, boxes, order/fixed-point errors, bridge semantics, and conflict
priority. Default four-input windows contain two broad and two core boards, so
holding out one retains both kinds of evidence. A witness on an individual board
does not establish lesson sufficiency; the production census records actual
accepted indices and checks all four holdouts. No skip/rejection occurred in the
final 300 materialized lessons, but the finite schedule argument alone would not
justify arbitrary reassembly or skipped indices.

For exact three-color lessons, tie rivals may survive every example because
there is no equal-mode tie. The tool labels this separately from contradictory
held-out predictions. It does not certify full tie knowledge for that restricted
case. Requiring all features on every input was rejected: it would distort
canonical support, and the separate `d7068a5d39a2` audit reproduces that failure.

## D5: Repair observed override failures and a new correlation

The dense candidate had 42 generation failures among 8,100 legal override calls.
After sparse support was restored, source `cc9d467...` still exhausted its
512-candidate bound for `(seed=0,index=5,easy,n_colors=4)`. It also exposed
leftmost/rightmost tie rivals that fit every demonstration but contradicted
Racket on held-out queries in indices 0..3. These are concrete teaching defects;
see `checks/code-review/override_rotation_authority_verification.json`, which
preserves the full source/rule identity, four labeled inputs, and differing cells.

Restricting repeated modes to mode 3 and balancing opposed tie witnesses removed
the known exhaustion/rotation failures. However, the first balanced source
`52171ef...` put the larger tied color on the left exactly when mode 1 was present.
An independent regression then found zero counterexamples to the conditional
shortcut. The final left,left,right,right orientation schedule is independent
of alternating mode sets; both conditional rivals are refuted twice in every
four-input window. That failed regression and both failed source snapshots remain
under `checks/`. Raising the retry limit or removing the rival was rejected as
an unsupported way to hide the defect.

The cap remains 512 whole candidates, with 128 placement attempts per color.
The final matrix and exact regression cases pass; universal success over all
seeds has not been proved. The mode plans, motif templates, default body counts,
and parity schedule remain explicit distribution restrictions. The finite-rival
review is not a claim to have eliminated every learnable shortcut.

## D6: Verification, tools, and runtime

New task-local tests run explicitly both in the working tree and through the
supported portable task-test stage. The first portable attempt failed because
pytest was only in the host user site, which that runtime correctly suppresses.
I preserved the failure, created an isolated same-machine environment from
already installed distributions, and retained a reusable offline helper rather
than changing shared runtime policy. Final tests execute 48 test cases;
missing dependencies or test discovery are not counted as passes.

The public census already supports rotations, so I used it directly. Its CLI
does not accept overrides; `workspace/verify_override_lessons.py` supplements it
through public `Catalog.apply` with raw consecutive override windows. It records
Racket labels, source hashes, actual inputs, and live rival declarations. Its
81 calls yield 51 unique inputs and 54 overlapping windows, not 216 unique
lessons. The separate control probe, independent oracle, fixed Racket fixtures,
and audit helpers are retained for future reviewers.

## D7: Honest solve and audit records

The separate blind solve was completed before reading any generator/rule; its
first revision passed 3/3 visible examples. The selected-task solve was prepared
only after the final generator bytes were frozen, and was explicitly marked as
previously exposed. During that attempt the reference sources and hidden labels
stayed closed; one genuine revision passed 3/3 visible examples. Both hidden-query
scores remain unknown, and no manufactured failure or model-training claim is
included. Notes are human-readable work logs, not token-level model traces.

Both immutable audit targets were inspected without modification. Findings in
`AUDIT.md` distinguish rejected lawful canonical inputs, broken advertised
controls, and an accepted-domain mutation outside the sampled template family.
No audit finding is presented as a wrong production Racket label without evidence.

## Stopping criterion

All required selected-task gates, explicit tests, 100 lessons per band with
rotations, both audits, and the final exposed solve are complete. The handoff
also replays the exact patch on a fresh original extraction and reruns the task
tests. I stopped adding speculative rivals after the final bounded code review;
shared admission-policy changes and any measured Qwen benefit remain decisions
for the maintainer, not unverified claims in this return.
