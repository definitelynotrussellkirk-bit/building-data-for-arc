# Frame completion and component selection

Native adapter for `f812a7b32f47`, with the episode-fixed setting
`selection = all | largest`. The `all` program is copied verbatim from the
selected canonical authority. The production generator and its validator are
unchanged.

## Rules and admitted grammar

Both settings use the same sampled inputs: one hollow rectangular nonzero frame,
left-edge color-2 row markers, top-edge color-3 column markers, inert bottom-2 and
right-3 distractors, and zero/orange interior cells. Preexisting orange fragments
are an explicit extension of the separate parametric grammar. The original
production grammar has an empty interior.

1. Complete all marked row/column crossings with orange (7).
2. For `all`, return that completed grid. For `largest`, find its four-neighbor
   orange components, retain **every** component of maximum occupied-cell count,
   and clear all other orange cells to zero. Losing original fragments are cleared
   too. All frame/marker cells remain unchanged.

Completion can join originally separate fragments into a new winning component.
The first teaching example merges four fragments and four new crossings into an
eight-cell ring that outranks the original five-cell chain. The second has two
twelve-cell winners and a losing nine-cell chain. This teaches ties and relative
ranking: a fixed minimum-size threshold cannot both keep eight and discard nine.
A diagonal fragment distinguishes four-neighbor from eight-neighbor connectivity.

## API and supported requests

`adapter.program(settings)` returns exact Racket text.
`adapter.generate(seed, settings, demos, queries)` returns labeled private
`train`, `test`, and `program_solution`. It accepts integer seeds in
`0..2**63-1`, **2–6 demonstrations**, and **1–4 queries** independently. Native
qualification uses three demonstrations and four queries. Booleans, unknown
settings, and out-of-range counts fail explicitly.

Input streams are independent of the setting and requested query count. The
same seed/count request samples identical inputs under both settings. Demos and
queries are distinct; requesting one or four queries yields identical demos and
the same first query. A bounded 32-attempt uniqueness guard fails loudly.

Query roles are a genuine 5×6 boundary case, varied transfer, a fresh tie case,
and a 30×30 stress case. The last spreads at least 144 completed orange cells over
four separated marker bands on each axis, with bridges, multiple components,
and border contacts. Transfer scenes vary marker counts, frame proportions,
fragments, positions and palette. Teaching motifs are constructive and finite;
they do not represent every possible orange topology.

## Reproduce in a reviewer packet

Run these from the outer folder containing `review.py`, with its ready Python
interpreter (the delivered run used `WORK/.venv/bin/python`). Choose fresh output
directories after source edits.

```sh
python3 review.py run python3 -m pytest \
  generators/f812a7b32f47/tests/test_parameters.py \
  generators/f812a7b32f47/tests/test_parametric_scenes.py \
  generators/f812a7b32f47/tests/test_parametric_exports.py -q

python3 review.py run python3 \
  generators/f812a7b32f47/workspace/parametric/audit.py \
  --out ../checks/f812a7b32f47/replay --seeds 0 17 --demos 2 --queries 4
```

The audit executes all labels and declared rival programs through protected
Racket. `prototype.solve` and rival Python functions are claims checked against
that runtime. Failed rival execution fails the audit; it never counts as a
teaching refutation. Fifteen programs cover the two real settings plus identity,
smallest, first/last tied winner, bounding-box area, eight-neighbor connectivity,
select-before-fill, ignored anchors, preserved losing originals, marker-anywhere
rules, exact size eight, and a minimum-size-eight cutoff.

The writer produces `private.json`, `report.json`, and hash-named files under
`public/`. Only the latter contain model-facing challenge payloads: demo
inputs/outputs and query inputs. Private settings, programs, seeds, future-turn
metadata, and query answers do not affect public bytes or IDs. The full four-query
public file is a controller-side bundle. Reveal `audit.first_turn(episode)` for
the first turn, then one query at a time with the existing consumer; no new
controller is introduced here. First-turn content has no total-query hint.

## Native qualification and owner handoff

The source inventory is `evidence/manifest.json`; its evidence root holds compact
source-bound verification receipts. Current native qualification and causal
witness are in `WORK/checks/f812a7b32f47/qualification/` and
`WORK/checks/f812a7b32f47/causal/` in the return package.

After applying the returned patch to the owner repository, qualify and accept
the exact live bytes using the existing native commands:

```sh
python3 -m arcpuzzles parametric qualify f812a7b32f47 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out var/review/qualification-f812a7b32f47 --summary
python3 -m arcpuzzles parametric accept f812a7b32f47 \
  --qualification var/review/qualification-f812a7b32f47/qualification.json \
  --reason 'Reviewed frame completion, merged-component ranking, ties and finite teaching evidence'
```

Reviewer qualification is not owner acceptance or training admission. Evidence
covers bounded settings, seeds and explicit rivals; it does not establish
universal identifiability or measured learning benefit.
