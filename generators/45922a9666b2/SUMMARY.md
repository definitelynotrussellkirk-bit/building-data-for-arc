# 45922a9666b2

Every red cell on the bottom row starts an independent walker. A walker moves upward while the cell above is not gray. When gray blocks the cell above, it moves one cell right if that cell is in bounds and not gray, then again prefers upward. It stops at the top or when both options are blocked, and every visited cell becomes red.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
