# Working notes: 39ad03f74acb

## Current decision

The canonical rule remains byte-for-byte unchanged: recolor the interior cells of every straight blue segment red. The ordinary generator moved from version `1.1.1` to `1.2.0` because the old sampler chose one orientation per grid. Retained review evidence contained a concrete lesson with vertical-only demonstrations and a horizontal query, so a vertical-only shortcut fit every visible example.

The repair alternates horizontal and vertical segments within every ordinary generated scene. A one-cell cardinal moat prevents independently placed segments from merging, branching, or forming corners. This changes the sampler only; it does not change the canonical program.

## Parametric family

`selection_mode` has two episode-fixed values:

- `all` — exact canonical/default program; recolor every segment interior.
- `longest` — first compute the maximum straight-segment length in the input, then recolor only interiors of segments attaining that maximum.

Input generation is independent of the setting. Demo and query streams are independently seeded and prefix-stable for 2–6 demonstrations and 1–4 queries. Every scene contains both orientations and multiple lengths. Every four-query bank contains one substantive 30×30 scene.

The causal chain is: enumerate segments and compute the input-dependent maximum length → retain that maximum as the intermediate → use it to select which segment interiors to recolor. The protected-Racket `skip_a` witness replaces the selector with “paint all” and changes 47 cells on the retained 30×30 case.

## Checks and limits

- 17/17 staged task tests passed, including protected-Racket parity for both settings.
- Both Racket programs passed complete-expression checks.
- A 16-seed audit checked 160 generated pairs, all count prefixes, finite-setting identification, mixed orientations, shortcut rejection, and a 30×30 stress scene in every full query bank.
- Authoring preflight passed 4 jobs and 32 protected-Racket evaluations; it is not owner qualification or acceptance.
- Public projection produced 16 single-query views; 24 first-turn private-field invariance mutations passed.

Finite demonstrations rule out the tested rivals, not every conceivable hypothesis. Next owner action: review the repaired base source, integrate the exact files, then run native qualification and fresh acceptance.

## Current retained-rule union

Preserve exact canonical all-interiors and accepted longest-only programs; add the incoming perpendicular-to-longest program as a third episode rule. Both reviewed segment banks remain available. Two demonstrations include controller orientation contrast; queries privately choose and shuffle one bank. The incoming ordinary generator is older and would remove mixed-orientation lessons, so it remains unselected.

Source-bound bounded checks live in `workspace/parametric/evidence/union-current/`. They establish finite Python contracts and protected Racket replay, not universal correctness or training admission. Owner qualification and fresh acceptance passed on these exact source bytes; `parametric/accepted.json` and `evidence/owner-merge-current/admission.json` are current. Existing canonical audits and training admission remain separate.
