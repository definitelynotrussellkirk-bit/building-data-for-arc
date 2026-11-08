# Native triggered-closure family

`closure_policy=markers_only|newly_enclosed` preserves the exact canonical
[2,3,0] -> [2,3,8] completion as its default. The alternative first executes
every original directed match, then colors a zero region 4 only if it is now
enclosed and belonged to boundary-connected zero space before completion.
Preclosed chambers, partially sealed chambers, reversed gates, blocked patterns
and free markers outside chambers distinguish the rule from simple recoloring.

This is a separate constructive grammar, not a claim that the canonical sparse
motif generator already sampled chamber walls. Horizontal wall gaps connect
inside and outside vertically. A vertical-wall gap with its preceding green
cell on the outside would already be blocked and is deliberately not used.
The ordinary scenes contain four rooms, including two newly sealed ones; the
30×30 scene has six substantive rooms and at least three newly enclosed regions.
Freestanding distractors have a clear zero row on each side to avoid accidentally
plugging a gate before execution. Trigger colors 2/3 and response 8 remain fixed;
4 is reserved for the composed filling step.

Inputs are deterministic and independent of the episode setting. Support is
2–6 demonstrations and independently requested 1–4 queries. The full four-query
bank is privately shuffled before taking any prefix. Public turns expose only
demonstrations and a single input; do not expose the private order or directory
listing. The existing preview helper may choose a separate presentation of the
qualified four-query bank; use one presentation consistently when stopping early.

From the outer packet folder:

```sh
python3 review.py run python3 generators/8de3465b4dbd/workspace/parametric/audit.py --seeds 20 --out generators/8de3465b4dbd/workspace/parametric/evidence/new-audit
python3 review.py task-tests 8de3465b4dbd --phase after --out ../checks/8de3465b4dbd-fresh-tests
python3 review.py run python3 -m arcpuzzles parametric qualify 8de3465b4dbd --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/8de3465b4dbd-fresh-qualification --summary
```

The self-contained auditor checks count boundaries, setting-neutral inputs,
prefixes, masked export invariance, finite executable rival teaching and protected
Racket parity. Public files are sorted by their visible-content hashes before
physical emission. Labels stored in its private examples are actual Racket
outputs; adapter labels are claims independently replayed by qualification.

The task-local tests include a hand-derived closure witness and an independent
geometric room-interior oracle over 100 scenes. The observed presealed-gate
construction regression is retained with four protected-Racket labels before/
after the fix. Evidence does not establish universal identifiability or training
benefit. Exact-source owner acceptance and training admission remain separate.
