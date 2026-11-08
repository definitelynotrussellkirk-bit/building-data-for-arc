# d5af7195f6da

Version `4.2.0` is a canonical-scale curriculum for wall-aware nearest-seed-color filling. Inputs are 7×9–11 framed arenas with 2–4 singleton seed cells. Color 5 is impassable; zeros take the uniquely nearest seed **color** by four-neighbor geodesic distance. Different-color ties and seedless chambers remain zero; same-color seed ties fill.

The period-four schedule constructs `distinct_tie`, `wall_detour`, `seedless_chamber`, and `same_color_tie`. A production lesson uses seven demonstrations plus one query, so every profile occurs twice and every one-pair query rotation retains all witnesses. Occurrence-rotated palettes prevent exact-input de-duplication from deleting the second witness.

Pinned authority: `RULE_HASH = ca2bc3cf692f`. Final generator SHA-256: `897916ea4e2e6b7812581ff0fd621b80e05694a4eda5606b96ed439049c9b34c`.
