# Generator 83c4d8ce9656

For each maximal horizontal run of one nonzero color, preserve the run's two
endpoints and erase its interior. Singletons remain unchanged.

The generator now uses a four-example scheduled curriculum:

1. `canonical_mix` stays on an exact public shape/palette signature.
2. `multiple_long_runs` disproves “transform only the longest run per row.”
3. `repeated_color_runs` disproves “merge all same-color cells in a row.”
4. `touching_color_runs` disproves “ignore color boundaries in a nonzero block.”

`workspace/profile_audit.py` gives future reviewers a quick profile, observer,
lesson-identifiability, and rival-refutation census.
