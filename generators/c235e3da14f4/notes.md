# Working notes: c235e3da14f4

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/c235e3da14f4/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Current parametric build: cell-count extremum

The reviewer-ready family keeps the exact canonical `size_rule=smallest` program
and adds `size_rule=largest` on identical visible inputs. Stage A segments every
same-color four-connected object except color 2, ranks by cell count, and retains
the selected object identity, size, and bounding box. Stage B crops the original
grid to that box. The first two demonstrations separate cell-count rank from
bounding-box rank and explicitly allow color 0 to be selected.

Current evidence is under `workspace/parametric/evidence/`, with native
qualification and the source-bound counterfactual under
`checks/c235e3da14f4/` in the return. The bounded audit covered seeds 0/17/211,
both settings, demo prefixes 2/3/6, four queries, nine named rivals, 30x30
stress, and public masking. Fresh task-local regression: 128/128 passed.
Production `generator.py` and canonical authority are unchanged. Next useful
action is owner integration followed by fresh exact-source qualification,
witness replay, and explicit acceptance; training remains unadmitted.
