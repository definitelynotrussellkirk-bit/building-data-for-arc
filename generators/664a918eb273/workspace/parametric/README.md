# Tail-order parametric family for 664a918eb273

The source task extracts separated orthogonal paths, keeps the first path fixed,
and sequentially translates each later path so its left entry is immediately to
the right of the previous placed exit.

This family varies one private episode-fixed parameter while preserving that
packing operation:

- `left_to_right` — exact canonical Racket source, byte for byte.
- `shortest_first` — keep the first path fixed; order the tail by cell count,
  shortest first, breaking ties by original left-to-right position.
- `longest_first` — the same, longest first.

Step A extracts each path, its endpoints, and its input-dependent cell count,
then chooses the ordered tail. Step B consumes that ordering and the previous
placed exit to position the next path. Inputs are identical across settings for
a fixed seed/count request. The first demonstration distinguishes all three declared settings and rejects
the bounded shortcut family; a second small canonical-scale example
is retained. Episodes support 2–6 demonstrations and exactly four queries. The
last query is a 30×30 lifted scene with colored content touching both horizontal
boundaries; it extends only this parametric family, not the production generator's
published `grid_h` axis.

`audit.py` checks the declared settings plus anchor-removal, horizontal-only,
color-order, reversed-tail, and identity rivals using demonstrations only. This
is finite evidence, not a uniqueness theorem. Python mirrors are sampler and
claimed-label checks; native qualification executes every selected label through
protected Racket.

From the packet's outer directory, the bounded authoring audit is runnable as:

```bash
python3 review.py run env PYTHONPATH=src:shared/runtime \
  python3 generators/664a918eb273/workspace/parametric/audit.py \
  --seed 0 --seed 17 --demos 2 --demos 3 --demos 6 --queries 4 \
  --out generators/664a918eb273/workspace/parametric/evidence/current/self-audit.json
```

After rebuilding the current source inventory, native protected-Racket
qualification is:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify 664a918eb273 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/664a918eb273/qualification --summary
```

The returned qualification is reviewer evidence only. Exact integrated source
still requires owner replay and acceptance before this family is usable by the
accepted parametric API or any training pipeline.
