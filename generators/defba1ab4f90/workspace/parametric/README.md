# Paired handedness stream family

The episode-fixed `handedness` is `canonical` or `reversed`. Canonical returns
exactly the selected Racket source bytes. Reversed swaps the signed blue/green
steering in both entry orientations. Both still trace a red stream, discover
which bar it actually reaches, slide just past the chosen end, and continue.
The canonical generator and its selected authority are unchanged.

## Input and teaching contract

- Two through six demonstrations, independently one through four queries.
  Ordinary lessons use three demonstrations and four queries.
- The first two demonstrations include top and left entry. Each of the two
  rules encounters both colors and at least five active turns on every scene.
- A bounded paired-route construction builds the two paths together. Same
  seed/counts give exactly the same inputs under either setting. Input selection
  retries are checked under both settings, not only the chosen setting.
- Bars are length three in normalized top-entry coordinates, separated by at
  least one zero column. Bar rows have at least one blank row between them.
  Both outside columns stay zero. Thus every possible left/right slide has an
  in-bounds exit, including all declared rivals; runtime errors never count as
  distinguishing evidence. Each main setting hits all constructed layers.
- Query profiles have 8, 10, 12 and 12 active layers. The last two are genuine
  30x30 scenes in opposite orientations, with bars distributed across both axes,
  alternative reachable branches and inert distractors, not padded small inputs.
- Demonstration-only certificates reject the other setting, always-blue,
  always-green, no-transposition-chirality, and first-bar-in-row shortcuts.
  These are finite claims, not uniqueness against arbitrary programs.

`trace` supplies independent Python label claims. Native qualification and the
replay tool execute actual protected Racket. The existing scalar-call audit on
the unchanged canonical generator is not resolved by this variant; the new
adapter strictly rejects non-integer seeds/counts and malformed settings.

## Native preparation and reproduction

From the outer packet directory after `python3 review.py setup`:

```sh
python3 review.py task-tests defba1ab4f90 --phase after --out ../checks/defba1ab4f90-new-tests
python3 review.py run python3 -m arcpuzzles parametric qualify defba1ab4f90 \
  --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/defba1ab4f90-new-qualification --summary
python3 review.py run python3 generators/defba1ab4f90/workspace/parametric/verify.py \
  --qualification ../checks/defba1ab4f90-new-qualification/qualification.json \
  --seeds 32 --out ../checks/defba1ab4f90-new-replay
```

Use fresh output directories. `verify.py` refuses overwrite, retains two fully
Racket-labeled episodes, bounded finite-rival counterexamples, and a source-bound
causal ablation. Without `--qualification`, its witness is explicitly unbound
and is diagnostic evidence only. Source changes need a fresh native inventory
and qualification, not recycled receipts.

The tool's `public/` files contain one current query only, without an answer,
parameter, program, future input or total-count hint. Their filenames hash their
exact visible bytes using `reviewer_support`. Query order and answers are in
`private.json` for the controller; do not expose that file or the public directory
listing to an actor. The first turn is byte-identical for one-query and four-query
requests with the same seed/settings/demonstration count.

The causal witness follows the first bar to column 7, then selects the green bar
at row 4, column 7 rather than the separate blue bar earlier in that row. Forcing
a blue intermediate instead moves the final exit from column 7 to column 9
(zero-based coordinates). The owner must replay and accept the exact source;
reviewer qualification is not acceptance or training admission.
