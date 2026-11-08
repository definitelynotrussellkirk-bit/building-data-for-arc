## 281f59ba6a02

Supplementary ticket `ticket-5d64ba4b0451dbcb` reproduced the retained witnesses from existing audit `review-f5408f5912ca74b7:v0001` on current generator SHA-256 `1477b25680033e2ddca2135f9d8122aeb85dae7d85c668b9689035a5e92a0bc5` (identical to the audited source), pinned rule identifier `037a32085547`. These are source-bound reviewer findings pending maintainer assessment; the existing audit remains `needs_triage` and is not cleared.

**B1 — Declared generation controls remain ignored.** `generate(0, 0, difficulty="medium", grid_h=10, grid_w=10, n_plus=1, center_color=9, arm_color=1)` returns a 16-by-17 grid identical to both the retained witness and the unoverridden call.

**B2 — Malformed ARC grids remain admitted.** Both `self_check([[10]*3 for _ in range(3)])` and `self_check([[4]*31 for _ in range(31)])` return `[]`, admitting out-of-range colors and oversized dimensions respectively.

**B3 — Retained asymmetric-arm witness reproduces.** For an all-zero 10-by-10 grid with `(4,4)=4, (3,4)=2, (5,4)=3, (4,3)=5, (4,5)=6`, `self_check` returns `[]`. One actual Racket application of the canonical program yields color 2 at `(2,4)`; the retained down-arm rival yields 3. The entire oracle and rival outputs match the retained asset. This confirms the concrete executable-oracle contrast only: heterogeneous arms are not uniquely justified by homogeneous-arm demonstrations alone. The historical 128-generated-case census and all-canonical-pairs claim were not rerun.

Reproduction: `checks/tickets/ticket-5d64ba4b0451dbcb/command.txt` and `replay.py`. Exact source/index/manifest/record/asset hashes and complete replayed witness grids: `checks/tickets/ticket-5d64ba4b0451dbcb/results.json`. One targeted probe completed successfully in 2.862659 measured seconds; authoring elapsed time was not measured. No target source or existing audit record was changed.
