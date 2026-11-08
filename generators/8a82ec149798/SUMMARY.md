# 8a82ec149798

A 0-background grid has 6-8 rows and 9-11 columns. Exactly one full vertical column is gray (5), centered or offset one column left/right from center. Two to seven non-{0,5} source cells lie on the mirrorable left side and use one or two colors. The right side is either empty or contains exactly two same-color control distractors: unrelated cells to erase, occupied mirror targets to overwrite, or one of each.

Rule: locate the first full gray column and reconstruct a clean output on a blank grid. Preserve all gray cells and every colored source left of the axis. Reflect each source horizontally across the gray column in its own color. Erase unrelated right-side input marks and overwrite occupied mirror targets with the reflected source color.

The five-profile lesson schedule covers centered and off-center axes, single- and two-color sources, clean inputs, erase noise, overwrite noise, and mixed noise. Difficulty changes palette/layout surface form without changing the semantic profile. Labels remain authoritative through the selected Racket program; the Python mirror is diagnostic only.

Kind: `per_puzzle`. Version: `3.0.0`. Rule hash: `40243de2441c`.
Approval remains derived by the catalog from current code and retained review evidence.
