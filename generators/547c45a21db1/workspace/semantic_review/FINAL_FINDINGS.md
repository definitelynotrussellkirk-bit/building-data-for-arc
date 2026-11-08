# Final dynamic semantic evidence: v3.1.0

Generator SHA-256:
`3d898f37975aaf54e4868ac01e67598f564183ab488b59421be26f59e154bc41`.
The unchanged canonical program hash is
`44ec512ed7bb40370dd13ed35408a4c0ece07c3de292f157b51d6a4450ade2ea`;
`RULE_HASH` is `44ec512ed7bb`.

## Measured final result

The reusable `final_probe.py` reads the actual selected module's
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_RIVALS`,
`SEMANTIC_WITNESSES`, and `WITNESS_RIVALS`. It does not copy a rival-name list.
All seven canonical shortcuts fit all three canonical pairs: **21/21 checks**.
All three canonical inputs pass both the selected validator and strict check.

The completed source-bound Racket census contains 100 lessons per band,
300 total lessons, 1,800 labelled pairs, 1,800 query rotations, and 1,727 distinct
input grids. Dynamic extraction re-evaluated all recorded rival statuses against
those existing Racket labels: all **8,700 production statuses** and **52,200
rotation statuses** are `refuted`. These counts include 29 namespace-qualified
declarations representing 11 competitor rules, not 29 independent hypotheses.
There were zero ambiguities, hook warnings, or scoring/materialization errors.

| Band | Labelled pairs | Canonical input shape/palette | Canonical input/output shape/palette |
| --- | ---: | ---: | ---: |
| Easy | 600 | 231 | 99 |
| Medium | 600 | 262 | 136 |
| Hard | 600 | 268 | 138 |

These explicitly defined profile counts describe the retained census and do not
replace the separate profile-floor gate. Every materialized input passed the
selected validator and strict check. Requested lesson starts were 0 through 99
in each band, with the census's retained SHA-derived seed recipe.

## Exact answer to generator-shortcuts

**Strong plausible rival:** use eight-neighbor BFS, allowing diagonal movement
between active cells. It fits both canonical demonstrations and the labelled
canonical query, yet changes the following generated even-length case.

Exact input:

```json
[[0,0,0,0,0,0],
 [1,1,1,1,1,3],
 [1,0,0,0,0,0],
 [1,1,0,0,0,0],
 [0,2,0,0,0,0]]
```

Intended Racket output:

```json
[[0,0,0,0,0,0],
 [2,3,3,3,3,3],
 [2,0,0,0,0,0],
 [2,2,0,0,0,0],
 [0,2,0,0,0,0]]
```

The eight-neighbor rival instead makes row 1, column 1 (zero-based) color 2;
Racket requires color 3. That is its only differing cell on this input.
The proposed generator emits this exact grid with
`generate(3584832175, 7, difficulty="medium")`, no overrides. It was train pair 2
of the retained medium lesson 5, whose requested start was 5. The extractor
replayed those exact arguments and reproduced the census input byte-for-byte.
Its input hash is
`e06a513920fa773b367f5b68ee533aa2245e7838dfcd0883bebc418a3e1c3004`.

The input and expected output first came from the completed Racket census.
The supported public apply command then re-executed both selected odd/even
witnesses with the final generator hash and unchanged Racket authority;
`apply_verification.json` confirms **2/2 exact matches**. Full rival outputs and
changed coordinates are retained in `witnesses.json`.

The companion odd witness is
`generate(3333184203, 15, difficulty="medium")`, a 5 by 6 grid with nine occupied
cells. Its input hash is
`d21dbc2644c0de7eb2671cd13c2bd9b82938bc0de14194eace1b024db12d7557`.
Each selected witness refutes ten of the eleven lesson competitors; together
they refute all eleven. The remaining competitor on each individual input is
the conditional raster-order rule applying only to the opposite parity.

## Requested schedule versus accepted lessons

The raw default schedule cycles odd contrast, even contrast, and varied inputs.
Six consecutive unrejected draws therefore contain two contrasts of each parity.
The accepted census has one precise exception: hard lesson 53, seed 1179814037,
rejects duplicate sample 58 and accepts indices `[53,54,55,56,57,59]`. It contains
two all-base odd witnesses and one all-base even witness. Do not describe every
accepted bundle as containing two full witnesses of each parity.

The exception remains identifiable against every declared rival in all six
rotations. In particular, varied sample 53 is a 20-cell path that also refutes
the even-only raster-order rival, so withholding the full even witness at sample
55 still leaves that distinction visible. Across the entire census, every
rotation retains at least one refuting demonstration for each parity-conditioned
raster-order rival, at least two for Manhattan, and at least three for every
other declared competitor.

`accepted_schedule_exceptions.json` retains that exact accepted sequence,
rejection, input geometry, Racket path colors, and rival results. The separate
`cycle_examples.json` keeps representative exact six-pair geometries for every
requested residue of the three-slot schedule in every band.

## Evidence and limits

Final evidence lives under `checks/semantic-final/final/`: `proof.json`,
`witnesses.json`, `witness_inputs.json`, `racket.json`, `apply_verification.json`,
`cycle_examples.json`, and `accepted_schedule_exceptions.json`. Exact wrapper
commands, working directories, exit statuses, and artifact hashes are indexed
by `checks/semantic-final/commands.json`.

This extraction reused the existing completed census and generated only two
exact witness replays. It made no new broad sample and read no solve episode.
The evidence addresses the current declared competitors and default five-demo,
one-query assembly. It does not establish universal identifiability, test every
seed or cyclic window, or promise the same witness schedule under exact overrides.
The seven canonical-fitting declarations are a finite diagnostic family;
undeclared conditional rivals remain a stated limitation.
