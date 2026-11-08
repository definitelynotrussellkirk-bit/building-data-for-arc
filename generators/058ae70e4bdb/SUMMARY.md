# 058ae70e4bdb

**Selected version:** `3.0.0`  
**Canonical rule pin:** `f3ddcec3d159`

Color `8` walls partition each input into 4-connected non-wall regions. A region is flooded with its sole nonzero color exactly when its distinct nonzero palette has size one. Empty regions and regions containing two colors remain unchanged.

The generator now uses canonical shape/palette profiles and an observable semantic scene grammar. Its ordinary three-example cycle is:

1. `same_color_pair` — an equal-color pair still fills, a two-color room stays, and a color repeats across regions;
2. `merged_two_color` — a punched wall creates a non-rectangular two-color region that stays;
3. `merged_single_color` — a punched wall creates a non-rectangular one-color region that fills.

Every consecutive three-example window contains the full cycle. The declared rivals are `exactly_one_marker`, `fill_every_nonempty_region`, `globally_unique_color_only`, and `rectangular_singleton_only`; the teaching hook rejects a lesson when any declared rival fits every demonstration.

## Public exact control

`scene_profile` accepts exactly:

- `canonical_mix`
- `all_fill`
- `same_color_pair`
- `two_color_stay`
- `merged_single_color`
- `merged_two_color`

The requested profile is recoverable from the generated grid, and unknown override axes are rejected.

## Verified support

The independent workspace audit checked 900 exact-profile draws (50 per profile in each of three difficulty bands), all unique and non-identity, plus 1,200 hold-one-out lesson rotations over 100 cyclic starts per band. It found zero failures against the independent flood oracle or the generator's actual rival declarations. See `workspace/deep_audit.py` and `checks/deep-audit.json` in the review packet.

Finite rival checks do not prove universal identifiability. The generated domain is deliberately limited to the five canonical height/width/palette profiles, a 2×3 wall lattice, at most one punched wall, and at most two marker cells per region.
