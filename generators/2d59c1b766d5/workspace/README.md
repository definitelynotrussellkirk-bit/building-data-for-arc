# Workspace tools

The selected implementation is `../generator.py`.

Run the fast source-bound lesson check from the staged repository root:

```bash
python generators/2d59c1b766d5/workspace/probe_curriculum.py
```

Add `--racket` to execute the selected canonical rule on all five canonical
pairs plus the sealed and diagonal witnesses. The report enumerates all three
schedule starts and all six possible query rotations, and names any declared
rival that survives the remaining five demonstrations.

The probe is finite: passing rules out only the declared `fill_all_interior`
and `eight_neighbor_flood` competitors. It is not a proof of universal
identifiability.
