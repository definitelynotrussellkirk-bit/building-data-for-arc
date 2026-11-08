# Proposed prototype: episode-level border color

**Status: proposed prototype.** This extension has no production API, approval,
or canonical-rule authority change. Its tests are separate from canonical
repair coverage. It imports no task generator and depends on no layout helper.

## Rule and bounded parameter

`border_color` is an integer from 1 through 9, default **8**. Choose it exactly
once per episode; the same exact Racket program labels all three demonstrations
and the final query. Without an explicit setting, `make_episode` chooses the
color deterministically from the episode seed. The retained experiment uses
explicit settings **8, 3, 6**, each at seed **104729**.

Find the global bounding box of **all nonzero input cells**. On its perimeter,
fill only zero cells with the selected color. Preserve every nonzero input
cell (including multicolor perimeter and interior sources); preserve all other
cells. Empty inputs stay unchanged. One-row and one-column boxes follow the
same perimeter semantics. The materializer reads only this task's canonical
ledger record, located with `canonical_path(find_root(__file__))`, and checks
that exactly one known fill literal is replaced. At setting 8, the complete
program text is exactly canonical. A changed canonical source causes a clear
failure rather than a silent replacement elsewhere.

Input source colors exclude the chosen color and all retained colors 8/3/6.
This prototype distribution constraint simplifies role identification and gives
identical source inputs across retained settings. It is not a canonical-domain
restriction. Opposite nonzero corners establish each global box, with other
corners zero; every demonstration therefore reveals the selected fill color.
Existing perimeter and interior sources use multiple preserved colors. Shapes
and padding vary deterministically across four examples, independently of the
canonical generator.

## Reproduce from WORK/

```bash
python3 run_with_racket.py ../.venv/bin/python generators/a5bda33d14a0/workspace/parametric/prototype.py --out ../checks/parametric --seed 104729
python3 run_with_racket.py ../.venv/bin/python -m pytest generators/a5bda33d14a0/tests/test_parametric.py -q
```

The wrapper sets the included Racket runtime and runs payloads from `WORK/repo/`.
Any Python interpreter with pytest and packet prerequisites can replace the
shown environment. Helpers use `find_root` rather than a fixed source depth;
focused tests resolve the prototype relative to their task directory.

## Evidence and public/private boundary

`checks/parametric/evidence.json` is **private authoring evidence**, containing
seed, selected colors, exact Racket text/hashes, prototype/canonical hashes,
all labels including queries, executed command, counts, limitations, and rival
refutations. `border-8.rkt`, `border-3.rkt`, and `border-6.rkt` are the exact
executed expressions. The included Racket bridge computes every label and
rival prediction; no Python mirror supplies labels.

`public-8.json`, `public-3.json`, and `public-6.json` are standalone public
challenges containing only three input/output demonstrations and one query
input. They contain no hidden parameter, seed, Racket program, or query answer.
Their filenames are authoring identifiers and are not part of the challenge
content. Do not give learners the private evidence, rule files, or authoring
README alongside those challenge objects.

For each of three retained settings, execute all eight alternate settings on
all three demonstrations: **72 actual rival/demo executions**, with 24 rival
setting/episode pairs refuted. The retained evidence also contains 12 chosen-rule
pair executions: nine demos and three queries. Tests separately check the
canonical setting against every labeled canonical pair; all nine colors on
multicolor, empty, horizontal and vertical edge cases; public projection;
parameter validation; and deterministic input generation. The test-first
collection failure (missing implementation) is retained in `test-first-red.txt`;
it is development evidence, not a failed solver attempt. `test-final.txt` holds
the subsequent focused test result. Intermediate parser-import and 30-second
Racket-startup failures are preserved in `test-iterations.txt`; the final
prototype uses a 120-second startup allowance to tolerate concurrent checks.

## Limits

The complete-episode evidence covers one fixed seed and three colors. All nine
color literals receive focused Racket edge-case tests, but complete episodes
for the other six settings are not claimed. Production here means the proposed
three-demo/final-query assembly; query rotation is **unknown**, with no broader
rotation census. Parameter rivals are only the other eight fill colors; this
is not a proof against unrelated semantic hypotheses. Accepted canonical repair
does not approve this proposed extension.
