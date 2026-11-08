# 5f5b990b28ab

A zero-background grid contains two to four disconnected color-8 objects.  Each
object is normally a hollow rectangular perimeter; the canonical data also has a
lawful tiny solid center.  The output keeps the same shape and recolors complete
objects by **descending bounding-box area** with the fixed palette
`[2, 4, 6, 7, 3, 5, 9]`.

The canonical examples use nested rectangles, so nesting depth, scan order,
perimeter/cell count, and width can imitate the intended rule.  Generator v3.0.0
keeps canonical nested scenes but adds two disconnected area-stress profiles in
a deterministic five-role schedule.  In every five consecutive generated pairs,
two stress examples make all three declared ranking shortcuts disagree with the
Racket-authoritative bbox-area answer.  Any one held-out query therefore leaves a
stress witness among the four demonstrations.

The only advertised exact axis is `scene_profile`, with values
`canonical_nested3`, `nested2`, `nested4`, `area_stress3`, and `area_stress4`.
`RULE_HASH = d23e43212061` pins the selected canonical rule.
