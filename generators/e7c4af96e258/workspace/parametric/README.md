# `e7c4af96e258` parametric proposal

Parameter: `target_policy`.

- `all_matches` is the byte-exact canonical program. Stage A enumerates every D4 marker match; Stage B stamps all candidate red footprints.
- `farthest_match` uses the same Stage A, removes the source footprint, scores each remaining candidate from the source bbox origin, and stamps only the largest-score candidate.
- `nearest.rkt` is not a declared setting. It is a source-bound counterfactual that keeps Stage A but changes only Stage B to select the nearest non-source candidate.

The sampler is independent of the hidden setting, constructs exactly two non-source candidates, makes their scores unequal, supports 2–6 demonstrations independently of 1–4 queries, and fixes query four at 30×30. The proposal is authoring evidence only; it does not claim owner acceptance or training admission.


## Demonstration certificate

The first two demonstrations are selected jointly. `prototype.py` fits a finite
named rival family using demonstrations only: all/nearest/farthest, fixed
lexicographic and edge-position selectors, plus three alternate distance
functionals. Every generated episode carries a certificate whose sole survivor
is the selected `target_policy`. This is a bounded teaching guarantee, not proof
of uniqueness against arbitrary programs. The candidate-footprint memo is capped
at 256 entries so repeated multi-seed audits do not retain an unbounded grid set.
