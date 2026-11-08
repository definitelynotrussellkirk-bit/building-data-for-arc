# Working notes: 7b3c2eaee231

## Current decision

The imported base generator and selected canonical rule were retained unchanged. The full task-local native family lives in `workspace/parametric/`: `packing_rule=canonical` preserves the exact selected program bytes, while `packing_rule=tallest_color_axis` selects the tallest object (width then color tie-break), carries its color parity as the intermediate state, and uses that state to choose horizontal width-sorted or vertical height-sorted center-packing.

## Self-review and evidence

Two demonstrations constructively expose both parity branches. Inputs are setting-independent; query prefixes are stable; all labels used in the retained checks were executed through protected Racket. The bounded review rejected the opposite setting and a wrong-intermediate counterfactual, exercised 2/3/6 demonstrations, seeds 0 and 17, four-query projection, and a populated 30×30 case. The authoring preflight, causal replay, public projection verification, and first-turn privacy checks are under `checks/7b3c2eaee231/`.

No base-source defect was found in the scoped review. This is reviewer-authored ready evidence only: the next action is owner source review followed by native qualification and fresh acceptance of the exact integrated bytes. No training admission is implied.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
