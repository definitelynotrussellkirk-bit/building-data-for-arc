# Native metric family

This prototype preserves the selected Manhattan rule exactly and adds one
finite semantic rival: Chebyshev distance. Inputs are shared across settings.
The bounded banks use 3–5 distinct singleton seeds, include ties under both
metrics, give every seed a nontrivial region, and force the two metrics to
produce different labels. The third private query is a boundary-spanning
30×30 stress case.

The causal decomposition is explicit: Step A computes each cell's selected
metric nearest-seed set; Step B maps a singleton set to its seed color and a
multi-seed set to color 8.
