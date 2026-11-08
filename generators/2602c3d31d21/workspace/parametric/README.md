# Pairwise-distance metric family

This native adapter keeps the ARC task's complete construction fixed and varies
one episode-level parameter: the distance used inside each shape's pairwise
signature.

- `squared_euclidean` is the exact canonical Racket program, byte for byte.
- `manhattan` replaces only the guarded pairwise-distance expression.

Inputs are sampled independently of the setting.  Each demonstration set
contains a deliberate signature collision that flips between the two metrics,
so the demonstrations alone identify the chosen program.  The fourth query is
a substantive 30×30, seven-shape stress case rather than a padded small scene.
