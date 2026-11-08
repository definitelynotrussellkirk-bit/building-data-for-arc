# 9000d0ea6484

Version `3.0.0`; rule hash `c9256d51e807`.

The input is exactly 4×19: four aligned 4×4 sections begin at columns 0, 5, 10, and 15, separated by full-height color-3 columns. The 4×4 output chooses the first nonzero aligned source in section order `2 → 3 → 0 → 1`, or zero when all four sources are empty.

Every generated input is a complete teaching example. Across its sixteen aligned positions it contains an empty cell, one solo cell for each section, and all six pairwise overlaps. The remaining five positions vary from empty/singleton cases to three-/four-section overlaps through the exact `extra_overlap_count` difficulty axis. Section colors are four exact pairwise-distinct axes drawn from nonzero non-divider ARC colors; defaults break the fixed canonical color-order shortcut while explicit overrides retain the full legal palette.

`strict_canonical_like` accepts the canonical structural family, `self_check` additionally enforces complete teaching support for noncanonical generated palettes, `observe_overrides` recovers every public axis, and the semantic contract executes named rivals and checks lesson identifiability.
