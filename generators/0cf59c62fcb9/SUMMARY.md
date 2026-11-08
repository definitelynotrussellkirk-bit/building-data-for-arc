# 0cf59c62fcb9

8-wall-bounded grid split into chambers by straight dividers, PLUS scattered interior 8-wall obstacles inside chambers (so the rule's geodesic BFS must DETOUR around them, not just Manhattan-fill). Each chamber holds 1..4 colored seeds. Rule: within each chamber every open cell takes the color of the geodesically-nearest seed (ties → smaller color value). Grid size, divider layout, obstacle count and seed count/positions all vary.

Kind: `per_puzzle`. Imported version: `1.2.1`.
Approval is derived by the catalog from current code and retained evidence.
