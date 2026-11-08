# Working notes: 74e83caa0660

## Base repair

The imported generator advertised `n_pairs` but read an undocumented `pairs` key, so the public count axis was inert and permissive coercion/unknown overrides remained possible. Version 2.1.0 now uses the declared `n_pairs` axis exactly over 1..8, validates strict integer and known-axis requests, constructs disjoint 3×3 boxes without retry loss, enlarges only unspecified dimensions when needed, and validates exact opposite-corner geometry. A final self-review also found that `n_pairs=1, texture=mixed` could not visibly realize a mixed orientation; that explicit combination is now rejected instead of silently collapsing.

## Parametric decision

The canonical default remains the exact selected X-completion program. The alternative `completion_rule=orientation_selects_motif` first classifies each color pair as main- or anti-diagonal, carries the per-color orientation map as the intermediate state, then paints main pairs as X motifs and anti pairs as plus motifs. Normal lessons contain both orientations, so two demonstrations distinguish the setting and reject an always-plus shortcut.

## Self-review and evidence

The retained checks cover exact count boundaries at 1 and 8 across all difficulty bands, invalid and impossible requests, both settings at seeds 0 and 17 with 2/3/6 demonstrations, protected-Racket/Python parity, rival and wrong-intermediate rejection, query-prefix invariance, and a distributed 30×30 eight-pair case. Fresh source-bound authoring preflight, causal replay, public projection, and first-turn evidence are under `checks/74e83caa0660/`.

The next action is owner source review followed by native qualification and fresh acceptance of the exact integrated bytes. No training admission is implied.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/74e83caa0660/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
