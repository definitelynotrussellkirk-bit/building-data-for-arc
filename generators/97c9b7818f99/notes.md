# Working notes: 97c9b7818f99

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current repair: visible Manhattan-vs-Euclidean witness

- Source `5f4ec6eeae2f1efa063911631d05d47de9d9638fce1186b16a2b6e73bca204d2`
  could emit a consecutive four-demo lesson whose outputs were all also explained
  by squared-Euclidean distance. The minimal reproducer is `difficulty="easy"`,
  seed `93`, demonstrations `9..12`, query `13`; the pre-repair lesson checker
  reported `Euclidean-nearest coloring remains consistent with every demonstration`.
- Version `4.1.0` preserves rule hash `af2297af758f`, the four-slot schedule,
  exact axes, gray-seed semantics, tie witnesses and per-seed ownership. Seed
  colors are selected before layout, and candidate placements are retained only
  when the actual visible colors differ under Manhattan and squared-Euclidean
  nearest-seed assignment. Using actual colors matters because gray `5` can mask
  a geometric tie-versus-owner disagreement.
- The reproducer is a task-local regression test. Focused evidence is retained in
  `checks/97c9-euclidean-window-before.json`,
  `checks/97c9-adversarial-sweep.json`,
  `checks/97c9-semantic-gate/`, and `checks/97c9-racket-parity.json`.
- Bounded verification covered 800 scheduled scenes, 192 sliding lessons and 144
  exact boundary overrides; the shared semantic gate additionally checked 600
  draws and 12 lessons. The first intentionally broader census exceeded its
  five-minute budget and was replaced by the bounded targeted sweep. No full
  twelve-stage battery was run. The canonical Racket authority was not changed.

## Current parametric proposal: fill versus smallest-region highlight

- The approved production generator remains byte-identical at
  `1c8a6546e04a3696caad1b85ac48888f0685c840c1c3414c1208fc26820cd6aa`.
- Built a native episode-fixed `finish=fill_only|highlight_smallest_region`
  family under `workspace/parametric/`. `fill_only` returns the exact canonical
  Racket bytes. The alternative first constructs the canonical Manhattan
  unique-owner partition, computes the filled-region size table, selects the
  unique smallest owner region, and recolors that region to 9 while retaining
  gray ties.
- The adapter supports 2–6 demonstrations, four sequentially revealed queries,
  matched inputs across settings, and a substantive 30×30 query. The bounded
  authoring audit covers 108 episodes and eleven declared finite rivals.
- Native qualification passed four jobs (two settings × two fresh seeds) with
  40 protected-Racket evaluations. The source-bound wrong-intermediate witness
  is `reviewer_replayed`: correct region sizes `{2:65, 5:38, 6:49}` select color
  5, while skipping that table selects color 2 and changes 103 final cells.
- This is reviewer-ready only. Exact-source owner acceptance and any subsequent
  catalog/training admission remain pending.
