# Exposed visible-only solve work log

This is an assistant-authored work log and reproducible Python experiment summary, not a token-level model trace. I previously saw this task's rule while repairing its generator, so earlier exposure is **yes**. During this successful solve I used only solve/README.md, challenge.json and my own Python experiments; generator source, canonical rule, previous solution notes and private labels remained closed. The earlier preparation failed before a public challenge existed; its OSError record is retained in prepare-failures/0001.json.

## Observations and hypothesis

Visible example 0: Input: 11 rows × 11 columns. Output: 11 rows × 11 columns.
Visible example 1: Input: 6 rows × 6 columns. Output: 6 rows × 6 columns.
Visible example 2: Input: 11 rows × 11 columns. Output: 11 rows × 11 columns.
Query 0: Input: 7 rows × 7 columns. Output: unknown.
Query 1: Input: 6 rows × 6 columns. Output: unknown.

Each visible output retains every original colored cell. Added cells exchange row and column coordinates, retain their source color, and double each foreground color count. Example 1 has sources below the main diagonal and creates cells above it. Examples 0 and 2 contain sources on both sides. My hypothesis is: copy each nonzero cell at (r,c) to (c,r), keeping the original grid.

## Experiments before the first actual solution check

`python solve/probe_visible.py` reads only the public challenge and records exact cell-mismatch counts in visible_probes.json. Keeping originals and adding their transpose matched all three demonstrations: [0,0,0]. The diagnostic alternatives produced upper-only [8,5,3], lower-only [5,0,4], anti-diagonal echo [23,8,14], transpose-only [13,5,7], and unchanged [13,5,7]. These are deliberate diagnostic alternatives, not failed solution revisions. No private query output was read or scored by these experiments.

## Submitted solution

The first actual attempted solution is solution.py: clone the square input, then add the transposed location of each original nonzero cell. The visible data do not require resolving conflicts between different colors at reflected source positions, so I do not infer a general collision policy from them. I will use the packet checker for visible-example agreement and query execution, with masked-query correctness remaining unknown.

## Checker result and stopping reason

The retained actual revision1 executed successfully and matched all3/3visible demonstrations. The checker reports the masked-query label as unknown. Before this successful revision, one invocation could not retain its output because evidence writing exhausted disk space; its child exit is unknown and the public revision count stayed0. That infrastructure failure is separately recorded in checks/solve-check-evidence-write-failure.md. I did not change the Python hypothesis to manufacture a failed attempt. I stop because all visible cases agree, the alternatives above disagree, and query execution completed; private correctness remains for independent scoring.
