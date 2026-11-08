# Largest objects after joining color-8 bridges

This is a separate native parametric proposal for `6afe10b621e4`. The production
generator and canonical authority are unchanged. `bridge_mode=ignore` returns
the exact 485-byte canonical program. `bridge_mode=merge` first recolors every
8 to red (2), then runs the canonical largest-red/largest-green selection on
that intermediate grid. Red winners become yellow (4), green winners become
blue (1), and all other cells are cleared.

The parameter changes topology and selection, rather than merely the output
palette: two smaller red fragments joined through color 8 can overtake a larger
isolated red component. A standalone 8 component may also become the red winner.
Four-connected, same-color components are used in both stages. The sampled
grammar has both required colors and unique maxima before and after merging;
ties and missing colors are outside the admitted grammar.

## API and grammar

`program(settings)` and `generate(seed, settings, demos=3, queries=4)` are exposed
by the thin adjacent-file adapter. Settings are exactly
`{"bridge_mode":"ignore"}` or `{"bridge_mode":"merge"}`. Seeds are exact
integers `0..2**63-1`; counts are independent exact integers, 2–6 demonstrations
and 1–4 queries. Qualification and the intended controller use four queries.
All labels returned by Python are claims until the native worker executes them
through protected Racket. The independent audit uses a separate flood fill and
executable rival rules.

The sampler constructively places connected red fragments, an 8 bridge,
independent red candidates, two green candidates, a standalone 8 region, and
other-color distractors in separated regions. Extra small red/green candidates,
polyomino shapes, translations, positions and all eight whole-grid symmetries
vary. It has no rejection loop or global RNG side effect. Same-seed inputs and
query order match across settings. Counts preserve both input prefixes and
fresh return values.

The first two demonstrations are 19×19 and 13×13. The first has an actual
merge-induced winner reversal, with an eight-cell near-square green winner and
a seven-cell L decoy. The L has greater bbox area, either side, bbox perimeter
and exposed perimeter, teaching occupied-cell count. The second teaches that
standalone 8s also become eligible; a diagonal-only 8 stays separate, distinguishing
four- from eight-connectivity even after preprocessing. Winners occupy opposite corners across the
two demonstrations under a shared sampled symmetry, defeating fixed-location
selection without adding demonstrations. Further demonstrations vary geometry
and scale through 28×26.

Four independently shuffled query roles are 11×13, 19×23, 30×30 and 25×29,
up to transposition. The large scene scales the real component sizes and
contains hundreds of occupied cells, substantial distractors and contacts on
every canvas boundary. The optional family extends the production sampler's
7–18 dimension range; canonical selection itself is lawful on these larger
grids. Region separation, fixed source/output colors, unique maxima and the
two teaching motifs remain explicit grammar limits.

## Evidence and reproduction

Run commands from the outer review packet with its ready Python interpreter:

```bash
WORK/.venv/bin/python review.py run python3 generators/6afe10b621e4/workspace/parametric/audit.py --out ../checks/6afe10b621e4/self-review.json
WORK/.venv/bin/python review.py task-tests 6afe10b621e4 --phase after --out ../checks/6afe10b621e4/task-tests
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 6afe10b621e4 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/6afe10b621e4/qualification --summary
WORK/.venv/bin/python review.py preview-public export --qualification ../checks/6afe10b621e4/qualification/qualification.json --out ../checks/6afe10b621e4/preview
WORK/.venv/bin/python review.py preview-public verify --bundle ../checks/6afe10b621e4/preview
```

Use new output paths when reproducing retained runs. Before qualification, create
the current source inventory with `parametric manifest`, including the focused
tests and the small `evidence/current` receipts. The native witness helper binds
an exact qualified bridge case, records the recolored intermediate, and compares
against selecting the original winner before merging.

Self-review found and repaired location, geometric-score and connectivity teaching
gaps. It also caught a regression where optional red noise accidentally joined
the standalone-8 control. That control now excludes red noise and has an explicit
diagonal-only 8. Protected before-repair examples and failing/passing regressions
are retained in the returned checks. Finite rival checks do not
prove unrestricted rule uniqueness, model learning, or universal seed coverage.

## Sequential public views and authority

Reuse the bundled `preview-public` exporter. A public file has the same visible
demonstrations plus exactly one query input, named by the hash of its exact
serialized visible bytes. Give a solver only one selected public JSON per turn;
the full directory and its private map stay with the controller. They reveal
future queries and original order. There is no total-count or last-turn hint,
and the first view is identical to single-query use. Neither previous answers
nor future inputs are used to establish any query's teaching support.

Native qualification, witness replay and public serialization verification have
different scopes. This return proposes reviewer-ready sources; only the owner's
fresh native acceptance of the integrated exact source makes this a usable
accepted family. Training admission remains false.
