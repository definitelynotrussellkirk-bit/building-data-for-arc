# Supplementary safety finding

## 260f488cb5a8

Ticket `ticket-26b64f8e03519161` reproduced the pinned audit record `review-027a21eee2143eb8:v0001` against generator SHA-256 `81356bc5319aa8c3381fadbb4fbb2a032464890ae3dc6aec3d227ae04c17682c`.

At seed `1`, sample index `2`, difficulty `medium`, the exact controls accepted `grid_h=4.9`, `grid_w="8"`, and `grid_w=8.7`. All three generated grids passed `self_check`; the replay JSON is byte-identical to the retained asset (`bde6cb82a31ad60487fb521230aabf99b23fe913e41da7b98f8b81c4b4177c59`). This confirms the bounded claim that non-literal integer overrides are silently coerced instead of rejected.

Evidence: `checks/tickets/ticket-26b64f8e03519161/override_coercion.json` and `checks/tickets/ticket-26b64f8e03519161/receipt.json`. No peer source was edited, and this replay does not by itself resolve or clear the existing audit. The previously proposed repair remains to reject booleans, floats, and numeric strings before the integer draw helper.
