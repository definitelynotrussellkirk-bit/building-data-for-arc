# Workspace tools for 4e79c276ce9d

`probe_smallest_object.py` is a source-bound authoring probe. It loads the selected generator from its actual file, reads canonical pairs through `reviewer_support`, and iterates the generator's live `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` declarations.

It checks:

- every declared canonical shortcut against every canonical pair;
- default profile coverage and rich-witness behavior in all three bands;
- every legal joint `grid_h`/`grid_w` combination in all three bands;
- all six declared schedule starts and all four held-out query positions.

Run from the repository root in the packet runtime:

```bash
python3 generators/4e79c276ce9d/workspace/probe_smallest_object.py \
  --seed 441 --samples-per-band 100 --out ../checks/probe-final.json
```

The output includes the generator SHA-256 and rule hash. It is finite evidence against the declared rivals, not a proof of universal identifiability.
