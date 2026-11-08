# Current review notes — a61246736c26 v4.1.0

Review `review-0a75bb185b4fe284`; proposed generator SHA-256 `f6be3b037fc2bd515ed0a12602eaf9d6873f563b0ed26f0b84ac5a51d25f2e45`. Canonical rule pin remains `08238424436c`. Original family: `training:15660dd6`.

## Intended rule and domain

Full color-8 separators define a three-row lattice with three or four tile columns. Each column has two identical 1/2/8 pattern tiles and one solid-fill tile. The solid tile's row selects the frame from the left swatch strip; its interior selects the fill. Recolor pattern border 1 to the frame, stroke 2 to the fill, leave 8 unchanged, and concatenate with 8 separators. Row swatches are a permutation of 5,9,0; distinct solid fills come from 3,4,6,7. Inputs stay within 30×30.

## Current distribution and lesson policy

The three exact public profiles remain available. Top/middle same-row profiles complement the retained zero-frame case. The permuted profile permits same-row or mixed-row solids and three or four columns. Four-column tile sizes are capped at 5/6; three-column hard scenes can use 7/8.

Default episodes require five demonstrations and one query. The six-position cycle is same-row frame 5, mixed rows with swatches 9/0/5, exploration, same-row frame 9, mixed rows with swatches 0/5/9, exploration. Explicit scene_profile controls bypass the cycle and are exact single-input controls, not a promise of lesson identifiability. Scheduled profiles use the public keyed context draw so provenance matches observed inputs.

Three deliberate rivals are declared: force frame 0 for same-row scenes; use fixed row frames 5/9/0; and read the strip only for same-row scenes. Python rivals are diagnostics; canonical Racket remains label authority.

## Decisions and reversals

The baseline's only same-row constructor selected frame 0. Retained audits `review-66a96f3e3fde9097:v0001` and `review-e3fe90a3dfb3e6d7:v0001` led to fresh reproduction of that shortcut and a malformed-separator IndexError. Broadened support repairs the shortcut; early structural returns make self_check diagnostic instead of indexing malformed tiles.

The first repair used three demonstrations and a four-position cycle. It was reversed after source e61fa2… at seed 3, medium, indices 0–3 admitted the conditional third rival: all three demonstrations fit, while 16 query cells differed under actual Racket. The permanent fixture is `counterexamples/conditional_swatch_shortcut.json`; the replacement uses mixed-row witnesses and five demonstrations.

A later 55a battery exposed missing scene-profile provenance on four scheduled branches. The singleton keyed draw repairs that contract without changing the layout stream: 792/792 compared grids are byte-for-byte equal. Literal integer identifiers are now required; sample_index must be nonnegative, but integer seeds have no arbitrary 32-bit cap.

## Evidence and limits

The final strict battery passes all twelve stages; the portable task suite passes 43 tests. Exact canonical-profile support is 29/60 and envelope support 43/60, with every band represented; semantic-manifold strict coverage is 600/600.

The public production census finds no declared-rival ambiguity in 300 lessons/1,800 pairs/1,800 single-query rotations, with 1,766 unique inputs. Fixed seed 0 covers all six cyclic starts in each band: 18 lessons, 108 rotations, 25 unique inputs. These are finite checks against three rivals, not a proof for every seed or every plausible branch-conditioned rule.

The reusable `workspace/probe_joint_swatch_support.py` discovers actual declarations, verifies canonical shortcut fits, and records Python support separately from Racket evidence. Detailed receipts, failures, source snapshots, and decisions are in this review's return under `checks/`, `REVIEW.md`, and `DECISIONS.md`.

## Separate proposed parameterization

`workspace/parametric/` provides a runnable episode prototype with stroke_symbol in {2,8}, chosen once per episode. Default 2 materializes the exact canonical program; 8 recolors the alternate interior symbol. It uses real Racket labels and a three-demo/one-query curriculum that distinguishes the two parameter settings. This is separate from the canonical five-demo generator and is not selected or approved for production. See its README and `checks/parametric/commands.json` in the return.

## Open status

No canonical Racket edit, catalog approval update, or audit closure is included. The retained audit index's explicit statuses remain authoritative: repairing their reproduced symptoms here does not automatically resolve unrelated findings. Untested rivals and downstream model-learning effects remain unknown. The two separately drawn targets are findings-only audits in the return, with unchanged source.
