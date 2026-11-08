# Mirror placement — proposed parametric prototype

This task supports one small semantic parameter, `mirror_side`, with values
`right` and `left`. The original/default setting is `right`: append the
left-right reflection after the input. The proposed `left` setting prepends the
same reflection. Both settings preserve the original reasoning structure:
reflect the complete grid, concatenate the two grids horizontally, and infer
from demonstrations which side contains the reflected copy.

This is a task-local **prototype**, separate from the selected canonical
`generator.py`. It does not alter the canonical rule, approval, or production
API. `right` reads the byte-exact canonical `program_solution`; `left` uses:

```racket
(rule! (lambda (g) (hconcat (flip-lr g) g)))
```

## Reproduce

From `WORK/`:

```bash
python3 run_with_racket.py python3 generators/19158f03ecb2/workspace/parametric/prototype.py \
  --out ../checks/parametric/mirror-side-seeds-0-7 --seeds 8
python3 run_with_racket.py python3 -m pytest \
  generators/19158f03ecb2/tests/test_parametric.py -q
```

The evidence directory must not already exist. Each episode has three
 demonstrations and one query. `choose_mirror_side(seed)` selects one setting
once from a dedicated deterministic stream; all four inputs come from independent
named streams that do not depend on the setting. Every pair in an episode uses
one exact Racket program.

## Input and teaching contract

The independent prototype sampler emits 3–9 by 3–9 grids containing 2–6 ARC
colors. Every input is filtered to be left-right asymmetric. That constraint is
shared by both settings and is deliberately semantic: on any such grid, the two
placement programs produce different outputs. Therefore each demonstration
refutes the other declared parameter setting, and every single-query rotation
of a four-pair episode remains identifiable against that bounded rival set.

Symmetric inputs are the honest limit: both programs then coincide. An
unfiltered episode containing only symmetric demonstrations cannot identify
`mirror_side`; this prototype avoids that ambiguity rather than claiming it away.
The census establishes only distinction between these two declared settings on
the retained seeds, not uniqueness against arbitrary programs or all inputs.

## Evidence and confidentiality

`racket-executions.private.json` retains every evaluated input, exact program
text and hash, and the actual isolated-verifier receipts. Python samples inputs
and compares labels but never synthesizes output labels. `episodes.private.json`
contains complete episodes. Public challenge files contain only demonstration
inputs/outputs and query inputs; they omit seed, parameter, program text, and
query answer. `report.json` binds source/program hashes, canonical agreement,
parameter draws, lesson and rotation results, and limitations.
