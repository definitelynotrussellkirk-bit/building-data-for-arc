# Current generator account: 3ab9aab86992

Version `2.2.0`; generator SHA-256 `14f3c3a81127c7f65da3bd837ef287021fb5d8cba1c61f65dc76ac8d5c8af384`; canonical normalized rule hash
`bbdf13ba2dfd`. Catalog/training approval is externally derived and was not changed.

## Intended rule and domain

An odd square (5–15) has a nonzero majority background and one to four
4-connected monochrome 2×2-minus-one-cell L components with distinct occupied
elbow orientations. Each occupied elbow selects the corresponding enlarged
border-L output corner in the same color. Colors may repeat across disconnected
components; zero may be an object color but not the Racket-mode background.
Different-colored components may touch; same-colored components remain
4-disconnected so object identity is unambiguous.

## Current production decisions

- Strict calls: `seed` and nonnegative `sample_index` must be literal integers;
  booleans, floats, strings, unknown keys, invalid difficulty, and conflicting
  exact controls fail loudly.
- Exact controls remain observable. Conflicting controls expose
  `ValueError.incompatible_axes`; there are no declared legal-axis combinations
  that the generator cannot support (`INCOMPATIBLE_OVERRIDE_COMBINATIONS=[]`).
- Lessons use three demonstrations and a seed-rotated period-4 cardinality
  schedule: easy `(1,2,4,4)`, medium/None `(2,3,4,4)`, hard `(3,3,4,4)`.
  Explicit `n_corners` overrides the schedule.
- `complete_all_corners` is the declared canonical shortcut and lesson rival.
  Every three-of-four query rotation in the declared schedule contains an
  incomplete example that refutes it; `lesson_identifiable` validates all pairs
  and checks the declared rival.
- The prior one-dense schedule was reversed after the distribution gate showed a
  median one object under correlated `generate(seed, seed)` calls. The final
  two-dense schedule keeps rotation safety and restores median object count ≥3.

## Evidence

Final source-bound evidence: strict battery 12/12 green
(`checks/after-final/`), portable task suite 118/118 passed
(`checks/task-tests-final-source/`), 300 production lessons and 1,200 query
rotations with zero declared-rival ambiguity (`checks/lesson-census-final*`),
and all 12 declared start residues / 48 rotations clear at schedule seed 0
(`checks/schedule-census-final*`). Exact shortcut/Racket witness:
`checks/main-shortcut-final.json` and `counterexamples/current-shortcut.json`.

## Parametric prototype

`workspace/parametric/` proposes episode parameter `corner_basis` with canonical
`elbow` and alternative `missing`. It preserves the tiny-L grammar and has exact
Racket programs and two complete distinguishable episodes in
`checks/parametric-final-source/`. It is intentionally separate from production,
canonical authority, catalog approval, and training admission.

## Known limits and open questions

The lesson evidence is finite and tests declared rivals, not every conceivable
hypothesis. A four-orientation same-color scene can make the two prototype
settings answer-equivalent, so prototype episodes deliberately use incomplete
orientation sets or distinct colors. The sampler does not claim uniform coverage
of every legal packing, and the retained archival raw Racket source remains
pre-existing divergent although selected execution parity passes.

Prior leads used: approved repair `review-248201d73dc2f3a9:v0001`; unresolved
rotation audit `review-38c015cb27208030:v0001`. Current review assignment:
`review-d4bc3df4ac3b5abb`.
