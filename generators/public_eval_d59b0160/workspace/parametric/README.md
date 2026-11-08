# d59b0160: key-directed deletion and area relay

`erase_policy=all_matches` exactly returns the adjacent canonical program,
which is byte-identical to `../../reference.rkt` and reproduces all four supplied
labels, including test gold. Orange (7), green (3), and black (0) retain their
parent roles. The green L bounds the key; all other key colors form a set.
Delete every separate panel containing that entire set, permitting extra colors,
repeats and arbitrary mark locations. Eight-connectivity identifies multicolor
panels; generated panels are rectangles separated by orange moats.

`area_relay` first performs the key-conditioned deletion, then uses the largest
deleted panel's occupied area to identify and delete a unique surviving panel.
The receiver's aspect ratio differs from the deleted panel, so dimension matching
cannot replace area. The 30×30 stress has matched areas 16 and 36, a 4×9 relay,
two unmatched 64-cell plates and a 56-cell plate. Key count, global maximum,
repeated area and survivor rank cannot replace the key-conditioned intermediate.

Generated grammar: eight separate rectangular panels in nine slots (one key),
27–30 rows/columns, 2–4 key colors, random mark locations, duplicate marks,
non-key distractors, randomized role placement and all eight global isometries.
The original 16×16 cases are executed in full but not used as sampler templates.
Two panels match; one is the unique largest. The admitted relay receiver is
unique. The general Racket rule deletes all equal-area survivors in a tie;
that ambiguous relay condition is deliberately not sampled.

The sampler does not claim arbitrary parent coverage. Green is reserved for
the key, orange for background, and no unmarked panel holes/overlaps or diagonal
panel contacts are sampled. The alternative requires a matched panel; on no
matches the general rule is a no-op. The original canonical semantics are not
changed by the alternative setting or authored rival branches.

Two demonstrations identify the setting against the declared bank: smallest
matched area, largest original area, first match, key cardinality, exact palette,
any key overlap, second-largest survivor, largest repeated area and richest
matched palette. This finite bank is not a universal uniqueness proof. A real
initial teaching flaw is retained in `checks/public_eval_d59b0160/shortcut-before.json`:
a second-largest-survivor rule fit both old demos and failed a lawful query.
The repaired second demo includes extra large unmatched plates and reverses the
palette/area correlation; the target's survivor rank varies across 2, 3 and 4.

The self-contained standard-library adapter supports independent 2–6 demos and
1–4 query prefixes. A complete four-query bank is privately shuffled before a
prefix is chosen. `public_turn` deep-copies only demo input/output and one query
input; no setting, seed, count, ordinal, program, answer or future input is exposed.

```
python3 review.py task-tests public_eval_d59b0160 --phase after --timeout 180 --out ../checks/area-tests-new
python3 review.py run python3 generators/public_eval_d59b0160/workspace/parametric/audit.py --out ../checks/area-audit-new --seeds 20
python3 review.py run python3 ../checks/public_eval_d59b0160/replay_shortcut.py --out ../checks/area-shortcut-new.json
```

Audit/test commands additionally need the checkout's protected Racket runtime.
Authoring preflight and these reports grant no owner qualification, acceptance
or training admission. Owner registration/source reconciliation precedes those.
