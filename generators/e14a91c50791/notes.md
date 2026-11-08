# Working notes: e14a91c50791

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Native parametric review — review-64519201510b2909

Built the task-local `finish` family under `workspace/parametric/` without
changing the production generator or canonical authority. `bbox_only` returns
the byte-exact canonical program (`af5d729bf23b180b26cc7f9b4174002cc0ccf5f7d11842e482031e2111d3b37a`).
`largest_orange_cluster` first performs that odd-rotation-class bounding-box
fill, then recomputes orange four-connected components and recolors the unique
largest one blue. Two complementary target boxes merge only after the canonical
fill, so the stage-B object is not present in the source.

The sampler supports 2–6 demonstrations, 1–4 prefix-stable private queries,
matched inputs across settings, four distinct queries, and a substantive 30×30
case. The reusable `audit.py` checked 320 episodes, 2,560 labeled pairs, 1,280
public turns and 60 protected-Racket evaluations; no declared shortcut survived.
Native qualification covered both settings at seeds 0 and 17 with 40 Racket
labels. The official wrong-intermediate witness replayed and changed four cells.

The inherited canonical test used a checkout-relative data path; it was repaired
to use `reviewer_support` so the staged task suite runs portably. Final staged
result: 38 tests and 12 subtests passed. One pre-existing non-failing deprecation
warning remains for a private `GenCtx` field.

Status is reviewer-ready, not owner-accepted. Exact-source owner integration,
fresh qualification and witness replay, semantic acceptance, and any later
training admission remain pending. The finite rival/seed audit is not a proof of
unique induction or measured learning gain.
