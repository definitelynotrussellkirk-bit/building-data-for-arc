# d09fae8197f6

Dense field (h 12..22, w 12..22) of noise colors 0/1/8 with magenta-6 cells at ~6..16% and exactly one 3x3 template (yellow-4 body + magenta-6 markers, 3..5 markers, yellows spanning the bbox; yellow appears nowhere else). Rule: for every dihedral orientation of the template, stamp its yellow cells wherever its magenta pattern matches grid 6s (>=2 hits, no conflicts; bottom/right 1-cell overhang allowed). The generator plants 1..3 guaranteed match windows in the noise so the rule always fires; emergent noise matches add more, matching the canonical 3..18 stamped-cell range.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
