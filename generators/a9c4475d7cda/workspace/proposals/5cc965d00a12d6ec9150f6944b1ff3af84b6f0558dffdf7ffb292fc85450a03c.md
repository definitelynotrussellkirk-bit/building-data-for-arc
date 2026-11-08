# Review — a9c4475d7cda parametric threshold family
Task/source: `a9c4475d7cda`; approved generator SHA-256 `1e242e04c710107969f6da280291342ae2fe6f0dc4da2a7eb7652e17c85bbe51`.
Defect → repair: the fixed generator had no parametric authoring surface; this adds a source-bound episode-fixed `panel_threshold ∈ {1,2,3}` prototype, adapter, promotion contract, tests, and current evidence inventory.
Canonical behavior: threshold `2` remains the default and exact canonical Racket source SHA-256 `4e6231455ecb950b5c408077976da1f2ee06d3b29707dbbd2717e6cdbbeb6668`; production generator and canonical data are unchanged.
Focused verification: 60/60 canonical, prototype, adapter, and inventory tests pass (`checks/parametric-final-suite.log`).
Finite Racket evidence: 3 settings, 9 demonstrations, 12 queries, 21 distinct inputs, 5 canonical replays, and 0 surviving declared rivals (`checks/parametric/a9c4475d7cda-panel-threshold-v1/report.json`).
Protected qualification: 6 jobs (each threshold × seeds 0 and 17), 3 demonstrations plus 4 queries per job, 78 Racket evaluations, all with the selected setting as the sole survivor (`checks/parametric/a9c4475d7cda-qualification-v1/qualification.json`).
Adversarial pass: count boundaries 1/16, deterministic replay, exact integer cells, source/setting rejection, and visible-only public identity all pass (`checks/parametric/a9c4475d7cda-adversarial-v1.json`).
Status: routine reviewer completion, but the family is `proposed_unapproved`; owner acceptance is still required and training remains unadmitted.
Remaining limits: only thresholds 1–3 and retained finite seeds/count combinations were exercised; no universal identifiability proof or measured learning gain is claimed.
Supplementary result needing attention: peer task `7358813cf026` advertises `grid_h=4..20` but rejects `4` on its default path; see `AUDIT.md` and the source-bound ticket evidence.

## Built artifacts

- `repo/generators/a9c4475d7cda/workspace/parametric/prototype.py` pins the approved generator and canonical Racket source, chooses one threshold per episode, samples distinct legal inputs containing panel counts 1/2/3, executes selected and rival programs through Racket, and writes split public/private evidence with visible-content IDs.
- `workspace/parametric/adapter.py` is the thin promotion boundary; it delegates program materialization and episode generation to the reviewed prototype rather than forking rule logic.
- `workspace/parametric/promotion.json` exposes exactly thresholds 1–3 and independent demo/query limits 1–16.
- `tests/test_parametric_threshold.py` covers source binding, exact program materialization, canonical replay, fixed-setting episodes, rival rejection, deterministic sampling, independent counts, public/private projection, evidence writing, adapter behavior, and contract bounds.
- `tests/test_parametric_inventory.py` guards the repository integration discovered during real qualification: the source-bound evidence inventory must be current and the promotion adapter must be reachable through `_ready`.
- `workspace/parametric/evidence/manifest.json` and its reviewer receipt retain current hashes, exact Racket programs, finite evidence summaries, and the qualification result without asserting approval.

## Evidence and checks

The primary evidence command produced one episode for each threshold with three labeled demonstrations and four distinct unlabeled-query inputs. Every input comes from the unchanged approved generator with a declared count profile that visibly includes counts 1, 2, and 3, so each nonselected threshold changes demonstration outputs. Public challenge filenames are hashes of the exact visible bytes; hidden settings, seeds, programs, and query answers do not affect them.

The protected repository worker initially rejected the adapter as unreachable because no current prototype inventory existed. A regression test first reproduced that `missing` state; the added source-bound inventory made the same worker qualify all six requested jobs. `checks/parametric-qualification-verify.py` independently rechecks retained receipt hashes, job coverage, single-survivor certificates, canonical program identity, and the 78-evaluation total.

A same-author final review found no remaining Critical or Important defect after the inventory integration fix. Its scope and limitations are recorded in `checks/parametric-self-review.md`; the author review is weaker than an independent fresh-context review.

## Supplementary tickets

- `ticket-22fa45fbe13808da` (`api_boundary`): **finding**. One advertised-valid boundary (`grid_h=4`) is rejected while `grid_h=8` succeeds for the same source-bound call coordinates. Peer source was not edited.
- `ticket-45cfd7795e5052d8` (`adversarial_witness`): **completed**. The `upper_wins_overlap` shortcut matches all four labeled canonical pairs but a lawful hard generated witness refutes it in two output cells; `self_check` is empty. Peer source was not edited.

## Stopping point

The selected task now has a bounded authoring implementation, test coverage, source-bound evidence, an adapter/contract, and successful reviewer qualification. Work stops before owner acceptance, production API activation, training admission, broad seed census, or peer repair because those are separate authority decisions or outside the selected edit scope.
