# Authoring probes for 538503abef57

These tools expose canonical answers; keep them closed during visible-only solves.
From an extracted packet root, run:

```sh
python3 review.py run python3 generators/538503abef57/workspace/probe_rivals.py --seed 41 --per-band 4 --out ../checks/new-rival-probe
```

Use a fresh output directory. The probe loads the selected source through
`reviewer_support`, uses the current declared rivals, obtains native Racket
outputs, and saves source hashes, canonical fits, generated refutations and
exact counterexamples. The documented command runs from a full packet/library
checkout. A staged runtime also needs the public catalog/API snapshot. The probe
does not write dataset labels or modify approval.

Run focused tests separately with the public task-tests stage. They check all
legal object/color pairs, malformed inputs, deterministic draws, all query
rotations in a finite seed sample, and 15 real Racket/independent-oracle matches.
A normal Python 3.12+ environment needs numpy, Pillow and pytest, with pytest
visible to that interpreter under PYTHONNOUSERSITE=1; Racket uses the packet
setup/wrapper. Consult the root return RESULTS.json for executed commands.
