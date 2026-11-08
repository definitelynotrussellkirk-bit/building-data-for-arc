# Bounding-box relay parametric family

**Reviewer status:** proposed native adapter; owner acceptance and training admission remain pending.

The `outer_fill` default returns the exact canonical Racket program byte-for-byte. Its matched-input alternative, `short_side_relay`, retains the outer nonzero bounding-box discovery but composes it with a second operation:

1. derive the outer box and its shorter side length;
2. select the unique non-blue same-color component whose cell count equals that length;
3. crop that component and render its exact normalized shape in color 8.

Thus the input-dependent side length is a real intermediate needed to choose the final object. Every scene also contains a long-side component and other plausible distractors. Two demonstrations alternate landscape/portrait geometry, short-side values, selected colors and object positions so height-only, width-only, long-side, fixed-size, fixed-color, first/last, smallest/largest and solid-bbox shortcuts are refuted within the authored finite set.

Demonstration counts are independently supported from 2 through 6. Every episode has exactly four distinct private queries; query 4 is a substantive 30×30 scene. Inputs are matched across settings for the same seed/counts. `public_turn()` exposes the demonstrations and one query input only, without settings, programs, answers, future inputs or total-turn hints.

The task-local CLI executes retained labels through protected Racket and writes a public/private projection:

```bash
python3 review.py run python3 generators/ebe355c22d70/workspace/parametric/prototype.py \
  --all-settings --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/ebe355c22d70/self-audit
```

This evidence is bounded to the two declared programs and authored finite rivals; it is not a universal uniqueness proof.

For a broader Python-side structural sweep across every supported demonstration
count, run:

```bash
python3 review.py run python3 generators/ebe355c22d70/workspace/parametric/audit.py \
  --seeds 50 --out ../checks/ebe355c22d70/sampler-stress.json
```

The sampler keeps the preferred distractor geometry for stable existing seeds.
When a crowded scene has no legal translation for that one aspect ratio, it
tries the remaining connected snake aspect ratios deterministically. This
avoids seed-dependent placement dead ends without weakening component-size
uniqueness or changing the target operation.
