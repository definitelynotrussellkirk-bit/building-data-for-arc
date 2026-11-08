# c831492f416e — Bridge Matching Endpoints

For each nonzero color that appears exactly twice, connect its two cells when
they share a row or column. Paint only the inclusive segment between the two
endpoints. Colors are processed in ascending numeric order, so the higher
numeric color wins at an interior crossing. A diagonal pair or a color that
appears any number other than two is preserved but not connected.

Version `3.0.0` exposes one exact axis, `scene_profile`. Every five consecutive
examples cover:

1. two disjoint canonical endpoint pairs;
2. a minimum one-cell interior gap;
3. a crossing where the horizontal segment has the higher color;
4. a crossing where the vertical segment has the higher color;
5. an aligned valid pair beside a diagonal pair and an aligned triple.

The generator includes an input-pure Python rule mirror, canonical-manifold
check, observable profile classifier, named rival rules, semantic witnesses,
whole-lesson identifiability check, and a standalone task-local census at
`workspace/profile_audit.py`.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Canonical rule hash:
`91f9e86ee830`.
