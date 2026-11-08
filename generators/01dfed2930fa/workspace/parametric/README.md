# Room-fill policy family — proposed parametric extension

The exact canonical default, `unique_color`, partitions the scene at color-8
walls and fills a room only when all of its nonzero seeds have one distinct
color. The alternative, `strict_majority`, preserves the same segmentation but
changes the gate: Step A counts every seed color within each room; Step B fills
zeros only when one count is strictly greater than half of all seeds.

Every constructive scene now contains eight semantic room roles: mixed 3:1 and
3:2 majorities whose first row-major seed is the minority, monochrome rooms with
two and five seeds, a 1:1 tie, a 2:2:1 no-majority room, a one-seed room, and an
empty room. Equal seed totals deliberately require different actions: at total
five, `unique_color`/`strict_majority` produce all three outcomes (fill neither,
fill only the majority setting, fill both). This rejects the retained
`seed_count_lookup.rkt` and `three_of_four_only.rkt` shortcuts, in addition to
first-seed, plurality, identity, and exactly-one-seed-cell rules.

The settings share identical inputs. The six-demo bank spans 13×15 through
24×28. The complete four-query bank is independently seed-shuffled before any
prefix is selected and covers 14×18, 19×23, 25×27, and a substantive 30×30
stress scene. The first visible query is therefore count-independent without a
fixed size-to-turn cue.

Run the focused checks and bounded protected-Racket probe from the packet root:

```bash
python3 review.py run python3 -m pytest -q generators/01dfed2930fa/tests/test_parameters.py
python3 review.py run python3 generators/01dfed2930fa/workspace/parametric/probe.py \
  --out generators/01dfed2930fa/workspace/parametric/evidence/current/probe.json
```

The default Racket file is byte-for-byte the canonical program. These variants
remain proposed and unaccepted; authoring preflight, owner source review, native
qualification, and exact-source acceptance are separate gates.
