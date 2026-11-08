# Bounded rival review of e937c5b85cdd

This review made no changes to the selected generator, task tests, shared code,
assignment, or solve material. The baseline source copied for replay is version
4.1.0, SHA-256
`d53cfef28f2b8c5a75dff2b0909a74efba6d85413bd136e24b909e8a2b0c320e`.

## Findings

The canonical reader returns six labeled occurrences of **three distinct pairs**.
Two simple alternatives fit all six occurrences:

1. **Nearer axis border.** Infer the horizontal/vertical axis from the elongated
   cross, paint the nearer endpoint of that axis with its color, and clear the
   farther endpoint. All 12 crosses in the three distinct canonical scenes put
   the short-arm/paint side strictly nearer its frame edge.
2. **Six-cell template.** Apply the observed operation only to six-cell crosses,
   ignoring seven-cell objects. The canonical scenes contain only the six-cell
   shape. The existing generator introduces seven-cell crosses in hard draws.

The intended Python implementation also fits 6/6 canonical occurrences. The
bounded generated census is explicitly **Python-labelled diagnostic evidence**;
it is not represented as a Racket census. For 200 draws per band, seeds 0..199
with `sample_index = 17*seed+1`, the nearer-border rival is refuted on
154/164/167 easy/medium/hard inputs. The six-cell rival is refuted on 0/0/132.

Across 128 four-pair lessons per band (seed 0..127, consecutive indices beginning
at `11*seed`), the nearer-border rival is consistent with all first-three demos
but changes the last query on 1/1/0 lessons. Holding out each pair in turn exposes
4/2/0 such rotated queries. The six-cell rival causes 0/0/5 original-query and
0/0/18 rotated-query ambiguities. A rival agreeing on all pairs is separately
counted as survived-all, never as query ambiguity.

The existing linked signature covers dimensions/count/palette/arm shape but
misses the observed proximity relation. Its 200-draw counts are 108/124/68; adding
the requirement that every short-arm side is strictly nearer gives only 5/6/3.
The latter input-only measurement is retained separately and should not be
confused with a general requirement for lawful generated counterexamples.

## Independent reference evidence

One successful public `Catalog.apply` call ran canonical Racket rule
`538497122a9d` on 52 inputs, with 52 outputs and no execution errors. Both the
generator's Python implementation and the independent parser/projection in this
probe agree on all 52 outputs. The receipt retains inputs, outputs, hashes, and
runtime authority metadata.

Examples of actual Racket-labelled ambiguous lessons:

| Rival | Band and seed | Demo indices | Query index |
|---|---|---|---|
| Nearer axis border | medium, 58 | 638, 639, 640 | 641 |
| Nearer axis border | easy, 19 | 209, 211, 212 | 210 |
| Six-cell template | hard, 3 | 33, 34, 36 | 35 |

For every row the rival fits all three reference-labelled demonstrations and
differs on the reference-labelled query. The easy and hard rows use query
rotation.

A compact combined counterexample is an 11x11 chamber with a single color-2 cross
centered at (5,6), with its right arm of length three and its other arms length
one (zero-based coordinates). The right edge is nearer, at distance four versus
six. Racket paints (5,0) with 2 and clears (5,10) to 0. The nearer-border rival
reverses those edits; the six-cell rival leaves both cells at 6. The corresponding
length-two cross refutes only the nearer-border rival. Both inputs pass baseline
`self_check`.

D4 transforms commute with the Racket output on 40/40 checked transformations:
all eight transforms of each of the three distinct canonical scenes and both
counterexample bases. This directly contradicts the historical associated-note
claim that D4 does not commute. Unique longest arms and collision-free projection
lanes are the relevant domain restrictions.

A second public call verifies the complementary length-three control: center
(5,4), right arm length three, so the painted left edge is nearer. All eight
D4 transforms execute without errors, fit the nearer-border rival, and refute
the six-cell rival. Their outputs agree with the independent Python projection
8/8 and commute 8/8. This brings the two independent public calls to 60 labelled
inputs. The second call still executes rule `538497122a9d`; it records the live
generator hash `bd2eb9bac38c319cdd427422e0a8286ac93215b615f432bdcc68d15ffada6044`
because the root reviewer had begun the repair. This is reference evidence for
the hand-created controls, not a census of that edited sampler.

## Local repair recommendations

Declare the public semantic hooks, the two named canonical shortcuts and lesson
competitors, and witnesses whose claims follow from input geometry. The strict
nearer-edge counterexample predicate should require at least one longest arm to
point toward the strictly nearer endpoint of its own axis; exclude distance ties.
A seven-cell cross is a genuine counterexample to the six-cell template.

Ensure a four-pair ordinary lesson contains at least two counterexamples to each
rival. A four-profile schedule can reserve two profiles for a length-three plus
strict anti-proximity witness, one for the actual canonical linked profile
(11x11, four official colors, arms length two, all short sides nearer), and one
for generalized layouts. Every four consecutive draws then has two refutations,
so each query rotation leaves at least one in the demonstrations. The canonical
profile retains a 25% floor. Keep exact user overrides exact and report schedule
guarantees only for the ordinary draw scope where they hold.

Do not force anti-proximity on every draw: that would suppress the actual
canonical placement relation while the old shape-only signature continued to
report healthy support. Keep its morphology-only measure distinctly named if
the strict canonical hook is extended to the newly observed relation.

## Reproduction and evidence

From the packet repository:

```bash
python ../run_with_racket.py python generators/e937c5b85cdd/workspace/rival-analysis/rival_review_probe.py
```

The probe uses its retained baseline snapshot, so future generator edits do not
change the diagnostic census. Public application still records the actual live
generator identity used by the authority wrapper. The successful run was against
the unchanged baseline hash above.

Evidence is in `checks/rival-analysis/` at packet root:

- `rival_review_report.json`: counts, exact replays, hand witnesses, and Racket results.
- `python_diagnostics.json`: explicitly Python-labelled census and lesson counts.
- `python_proximity_diagnostics.json`: input-only linked-profile measurements.
- `public_apply_receipt.json`: independent authority inputs, outputs, and hashes.
- `public_apply_input_identities.json`: receipt indices mapped to probes.
- `public_apply_farther_arm3_receipt.json` and `farther_arm3_control_report.json`:
  independent complementary length-three controls, eight D4 transforms.
- `run.log`: successful wrapper command output.
- `public_apply_unconfigured_receipt.json` and `run_unconfigured.log`: preserved
  first attempt without the Racket wrapper; every result failed with
  `RacketUnavailableError`. Those are failure evidence, not verified labels.
