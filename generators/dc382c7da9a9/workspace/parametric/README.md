# Native wall-distance scope family for `dc382c7da9a9`

This task-local family preserves the selected canonical Racket rule byte-for-byte
at `distance_scope="all_equidistant"` and adds the matched-input alternative
`"shortest_path_midpoints"`.

For every input, stage A runs wall-constrained BFS from the unique red and green
seeds, retains both distance maps, and reads the input-dependent shortest
seed-to-seed distance `L`. Stage B consumes those intermediates. The canonical
setting paints every reachable blank cell whose two distances are equal. The
alternative additionally requires the two distances to sum to `L`, so it paints
only equidistant cells that lie on a shortest path between the seeds.

The native adapter supports 2–6 demonstrations and 1–4 independently truncated
queries. Six demonstrations and four queries come from separate deterministic
pools, so changing either requested count cannot move the other split. Both
settings receive identical visible inputs. The first two demonstrations refute
Manhattan distance, all-shortest-path, first-tie-only, one-step offset, identity,
and the opposite setting. The fourth query is a genuine 30×30 walled room with
hundreds of equidistant cells but exactly one shortest-path midpoint.

Run focused checks and qualification from the packet root:

```bash
python3 review.py task-tests dc382c7da9a9 --phase after \
  --out ../checks/dc382c7da9a9-tests
python3 review.py run python3 \
  generators/dc382c7da9a9/workspace/parametric/audit.py \
  --out ../checks/dc382c7da9a9/audit.json --seeds 16
python3 review.py run python3 -m arcpuzzles parametric qualify dc382c7da9a9 \
  --out ../checks/dc382c7da9a9/qualification --summary
```

The family is reviewer-ready only. Exact-source owner acceptance and any later
training admission remain separate gates.
