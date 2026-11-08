# Reusable contact-graph review tools

`probe_curriculum.py` measures returned grids with an independent pixel
flood-fill/BFS oracle. It records source identity, exact seed/index ranges,
unique inputs, canonical-size/palette hits, target multiplicity, graph cycles,
color reuse, all currently declared witness/rival results, and the actual rival
name list. With `--seeds >=20`, it also enumerates 240 overlapping four-pair
windows and all 960 single-query holdouts.

From a packet root:

```sh
python3 run_with_racket.py python3 generators/28ba67946524/workspace/probe_curriculum.py \
  --seeds 100 --samples 10 --out ../checks/new-probe.json
```

`--source PATH` can analyze retained source bytes with the same independent
observations; paths resolve from the runtime repository. The output path must be
new. The probe reads canonical answers and must never be used during a
visible-only solve. Authoritative labels still come from Racket; this tool is a
source-bound distribution and lesson diagnostic.

## Teaching guarantee and limitations

Even indices are varied paths; odd indices are branched four-cycles with a
seed-adjacent triangle. Every odd input refutes all eight declared rivals:
single-target, fixed color 4, merging equal-colored components, diagonal contact,
ignoring input 8, two pixel hops, retaining the whole reachable graph, and
selecting every endpoint of a two-edge walk without checking shortest distance.
The triangle supplies the last witness: a node with a two-edge walk and graph
distance one. The two true target colors differ; one is reused by an unreachable
component; the bridge is two columns wide before rotation; input 8 rotates
between bridge and target roles.

`LESSON_SCHEDULE_PERIOD=2`. Three consecutive demonstrations always include an
odd witness. A four-pair consecutive pool contains two odd inputs, so every
single holdout leaves one. Rejections, arbitrary distant-index subsets, or
removing more demonstrations can break that premise; run `lesson_identifiable`
on the actual assembly. No claim is made for arbitrary planar graphs or
undeclared rivals.
