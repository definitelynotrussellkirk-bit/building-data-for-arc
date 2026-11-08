# Working notes: 677dcb71e2be

## Current reviewer candidate

- Preserved the canonical Racket program and all five stored labels.
- Repaired the two retained ordinary-curriculum shortcuts. Objects now occupy broad legal interior/boundary positions rather than four fixed corner slots, and palette rank is randomized independently of component-size rank. Strict scalar, difficulty, and override validation was added.
- Added the native `order_mode` family. `size_desc` is byte-identical to the canonical program. `border_shift` finds the unique border-touching component, computes `occupied size mod component count`, rotates the canonical size-descending order by that offset, then packs bars.
- The sampler supports 2–6 demonstrations and a stable bank of four distinct queries, including a substantive 30×30 query. Settings use matched inputs. The query bank covers all nonzero offsets 1, 2, and 3.
- A two-demonstration attack initially found a selector-color-rank proxy. The sampler now forbids both zero rank and the true offset rank. A later probe found that the query bank omitted offset 3; one four-component query was changed and a regression test retained. Final self-review found that the first two demonstrations also confounded offset with dimensions, border side, and component count; they are now a same-dimension, same-side, four-component crossed pair with offsets 1 and 2.
- `workspace/parametric/probe.py` is a reusable bounded audit of the two old base shortcuts, fixed/rank/position/area parametric rivals, crossed causal controls, request/grid types, query-prefix stability, and 30×30 support.

## Limits and next gate

The finite rival set and sampled seeds do not prove universal identifiability. Protected-Racket authoring preflight, causal replay, and public projection are reviewer evidence only. Owner source review, native qualification/acceptance, and any training admission remain separate.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
