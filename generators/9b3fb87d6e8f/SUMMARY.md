# 9b3fb87d6e8f

0-bg grid (size varies). A color-1 (blue) SOURCE on the left emits a ray moving RIGHT. 1-3 single-cell DEFLECTORS (color-3 '/' or color-4 '\') sit at the ray's TURN POINTS, and a color-5 (gray) WALL sits where the ray finally stops. Rule: trace the ray from the source — '/' turns right->up / up->right etc., '\' turns right->down / down->right etc., the wall stops it — and paint every traversed 0-cell COLOR 8 (cyan). The whole path is built by tracing forward so every deflector is actually hit and the ray ends at the wall; grid size, source position, deflector count/placement/type and wall position all vary freely (was one fixed ray config + padding).

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
