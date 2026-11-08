# Native cross-frame and post-cut fragment family

Proposed, source-bound, owner acceptance pending. Production generator and canonical
ledger are unchanged. `adapter.py` loads the adjacent `native.py`; the three
retained frame settings reuse `prototype.py` rather than fork its rule builder.

## Rule parameter

`rule` is one of `frame_4` (the exact canonical default), `frame_2`, `frame_8`,
or `largest_fragment`. The first three paint the eight neighbors of the crossing.
The fourth first paints the canonical color-4 ring, recomputes same-color
4-connected components excluding 0/4, selects the largest (ties: top-left row-major),
and highlights **only that one remaining fragment** in color 8. Everything else,
including the cut ring, is preserved. The center participates as a size-one fragment.

A = canonical ring cut; intermediate = the selected post-cut component's exact
cells, color and size; B = recolor that component. Choosing a component before
cutting instead selects an uncut line/arm and changes surviving highlighted cells.
The source-bound protected witness uses this wrong-order ablation. This is not
just a changed constant or a remap that commutes with the frame.

## Grammar and lesson

Native inputs are clean full crosses, 4..30 by 4..30, with an interior crossing,
either center owner, two distinct line colors from {1,2,3,5,6,7,9}. Colors 4 and 8
are reserved for the cut and highlight. This is an explicitly narrower palette
than the unchanged canonical generator; all settings share these same inputs.
The original legacy prototype still accepts its broader 1..9 line palette.

`generate(seed, settings, demos, queries)` accepts exact integers: seed 0..2^63-1,
demos 2..6, queries 1..4. It always constructs one setting-neutral six-demo/four-query
bank, then takes prefixes. Changing demo count never changes queries. No global RNG
is consumed. Duplicate banks fail explicitly rather than return duplicate queries.
Four queries are the qualification and training-supervision contract. Only one is
exposed to a solver at a time; source ordering is not presentation ordering.

The first two demonstrations constructively teach tie handling and color/count
independence: one horizontal/vertical area tie chooses the lower-ranked minority
color; one four-way tie chooses the higher-ranked majority color. This repairs
column-first, min/max-color tie and minority-color shortcuts at **two** demos.
The retained pre-repair lesson demonstrates the actual column-first failure.
Extras vary geometry, colors and center owner. Queries cover 4x4, opposing high
aspect ratios and 30x30 with boundary-adjacent crossing. The 30x30 cross has 59
nonzero cells and touches all four edges; its sparse density is inherent to the
clean-cross rule, not padding of a small embedded puzzle. No noisy/multiple-cross
or arbitrary-color grammar is claimed.

## Run from the outer packet

```sh
python3 review.py run python3 generators/95524d104174/workspace/parametric/audit.py --seeds 32 --out ../checks/95524d104174/audit.json
python3 review.py task-tests 95524d104174 --phase after --out ../checks/95524d104174/tests
python3 review.py run python3 -m arcpuzzles parametric qualify 95524d104174 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/95524d104174/qualification --summary
python3 review.py preview-public export --qualification ../checks/95524d104174/qualification/qualification.json --out ../checks/95524d104174/public-preview
python3 review.py preview-public verify --bundle ../checks/95524d104174/public-preview
```

Before qualifying, use the native `parametric manifest` helper after all source
and test edits; retain its task-local `evidence/current` receipts. Native
qualification independently executes all labels and checks setting identification.
`audit.py` separately records its finite Python-policy sweep and the much smaller
protected-Racket subset. Do not count Python checks as executed Racket labels or
repeat occurrences as distinct grids.

The bundled preview helper shuffles the full private query bank before revealing
single-query prefixes; presentation seed, future queries and answers remain private.
Public files contain only visible demos and one query and are hashed from those
bytes. Never expose the private manifest or directory listing as a model turn.
The older `prototype.py materialize` interface remains a 3-demo/1-query provenance
utility, not the native API. Its writer has also been corrected to public-content
hashes and exact canonical public serialization. Historical ordinal-named exports
are obsolete private evidence and must not be distributed as fresh challenges.

No finite rival check establishes universal identifiability. No owner acceptance,
training admission or measured learning benefit is claimed.
