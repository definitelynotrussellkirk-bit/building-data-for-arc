# Working notes: 577d2db13443

## Current decision

Built a native, episode-fixed parametric family under `workspace/parametric/` and
left the approved production generator unchanged at SHA-256
`806f53221ad5dca44db6230fcadb9d0b8606f954126206d5adf194008c18a23a`.
The default `finish=caps_only` returns the exact canonical Racket bytes
(SHA-256 `a811558a15fb8476dc33ee271dc391ab53717b42ff625990feffa515ddda14c9`).
The alternative `finish=highlight_largest_cap_component` is a substantive
sequential rule, not a palette or layout cosmetic.

## Rule family

1. Step A applies the canonical operation: every maximal same-color horizontal
   nonzero run has its left and right endpoints recolored to 1.
2. The intermediate is the complete post-cap grid and its 4-connected color-1
   components, with occupied-cell counts.
3. Step B selects the unique largest such component by occupied cells and
   recolors exactly it to 8.

Step B depends on Step A because endpoints from differently colored adjacent
runs merge only after endpoint recoloring. The retained counterfactual consumes
the same post-cap components but uses bounding-box area; on the protected witness
it selects a five-cell component with box area 9 instead of the correct six-cell
component with box area 6, changing the final grid.

## Sampling and visibility

The adapter is deterministic and prefix-stable for 2–6 demonstrations and 1–4
queries. Inputs are identical across settings. Production episodes expose four
distinct queries sequentially, with no settings, program, answer, future input,
or total-query hint in `public_turn()`. The four-query bank independently shuffles
14×17, 18×22, 24×27, and substantive 30×30 scenes. Across bounded seeds, the
30×30 query occurs in every turn position. Every alternative-setting scene has a
unique largest occupied component and a smaller component with a larger bounding
box, so the intended size statistic is observable.

## Evidence

- Focused task-local tests: 40 passed.
- Authoring audit: 18 jobs spanning seeds 0, 17, 97; demonstration counts 2, 3,
  6; both settings; 68 protected-Racket evaluations; all eight declared rivals
  refuted; 2,560 prefix checks; 512 public-projection checks; 23 query orders.
- Native qualification: four jobs (two settings × two fresh seeds), three demos,
  four queries, 40 protected-Racket label evaluations; status `qualified`.
- Sequential witness: two fresh protected-Racket evaluations; status
  `reviewer_replayed`.
- Source inventory: 17 bound files; manifest SHA-256
  `9737b1c3a962a5e4c38ec5b426f37444f9d4db84b4f2c49f5b63fcce850e1358`.
- Alternative program SHA-256:
  `c1fb2e185659079e68b9c80977dea8bf9bce76b9c6ce2933fb9ab922aa3ce0aa`.

## Limits and next action

All identifiability and rival claims are finite to the declared seeds, settings,
and competitors. Reviewer readiness does not perform owner acceptance, canonical
integration, training admission, or measured training-gain validation. The next
step is owner integration followed by fresh qualification and acceptance replay
on the exact live bytes.
