# 0701a2c36d45

Read three rotation codes from the header, split the remaining input into three equal panels at the full color-9 rows, tight-normalize and rotate each panel occupancy (`1=0°`, `2=90°`, `3=180°`, `4=270°` clockwise), then paint color 8 wherever at least two rotated panels vote for the same cell.

The version 3.0.0 generator exposes four exact recoverable controls: panel height, panel width, shared base size, and vote texture. Its six-step cyclic curriculum includes full agreement, one-panel noise, a two-panel signal, and repeated mixed-vote examples so every five-pair window—and every four-of-five query rotation—contains decisive majority evidence.

Kind: `per_puzzle`. Current version: `3.0.0`. Canonical rule pin: `606946fe96ab`.
Approval and training admission remain catalog decisions; this review changes neither.
