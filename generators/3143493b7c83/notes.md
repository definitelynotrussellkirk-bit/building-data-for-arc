# Working notes: 3143493b7c83

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/3143493b7c83/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-24 native parametric MAIN

Built a source-qualified `match_mode` family under `workspace/parametric/`.
The exact canonical default, `contains`, preserves the selected authority bytes;
`exact_bbox` instead requires the extracted key bitmap to match exactly inside
its input-derived bounding box. Inputs are matched across settings, support 2–6
demonstrations and stable 1–4 query prefixes, and include a substantive 30×30
fourth query.

Demonstrations constructively distinguish the two settings and five finite
plausible rivals. Protected verification covered 18 jobs, 138 pair labels and
207 Racket evaluations; the 64-seed min/max sampler check covered 256 episodes
and 2,048 pairs. Native qualification passed for both settings on seeds 0 and
17. The source-bound owner-form witness replays two cases in protected Racket:
a horizontally corrupted extracted key and skipped extraction both change the
final output.

Reviewer status is `ready`; owner admission and training admission were not
performed. The pre-existing production override-contract audit remains open:
this return intentionally leaves the approved production generator and
canonical authority unchanged.
