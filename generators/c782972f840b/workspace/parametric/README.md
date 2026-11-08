# Native parametric family: rotation versus dihedral equivalence

`equivalence_policy=rotation` is the exact selected canonical Racket source.
`dihedral` additionally treats reflected shapes as equivalent. Inputs are shared
between settings and contain a chiral mirror pair plus independent shape/color
relations. The first two demonstrations identify the setting. Four prefix-stable
queries end in a dense boundary-touching 30x30 case.

Sequential dependency: step A extracts objects and assigns transformation-orbit
class IDs; step B consumes those IDs and object colors to render the relation
matrix. `audit.py` checks the bounded setting/rival curriculum.
