# Minimal shape-distinction counterexample

`reflection-and-bbox.json` is one exact 12×14 input on background 0. Four
isolated tetrominoes, in bounding-box row/column order, are: an L, its mirror,
a quarter-turn of the L, and a T. Component colors are 5,2,4,3. All have
area four and unordered bounding-box sides {2,3}; only components 0 and 2
match under rotation.

The final generator's validator accepts the input. Selected Racket authority
`f2869336c461` produces:
`[[5,0,8,0],[0,5,0,0],[8,0,5,0],[0,0,0,5]]`.
Reflection adds spurious matches between 0/1 and 1/2; area/bbox adds still
more. Full authoritative input/output/source/cwd/command evidence is in the
return at `checks/canonical-label/final-distinguishing-racket.json`.
The focused contract tests include this geometry independently.

Replay from the original outer packet directory with a new output filename:

```bash
python3 review.py run python3 -m arcpuzzles apply 84aeaf4792a8 --input generators/84aeaf4792a8/counterexamples/reflection-and-bbox.json --out ../checks/reflection-replay.json
```

This hand-built arrangement demonstrates the rule distinction. Actual default
generated counterexamples with seed/index/overrides are separately retained by
`workspace/probe_distribution.py` in `checks/distribution/run-1729/report.json`.
No claim is made that the sampler emits this exact placement under a known seed.
