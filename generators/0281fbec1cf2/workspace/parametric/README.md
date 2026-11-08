# 0281fbec1cf2 native parametric family

`finish=rays_only` is the exact canonical blocker-aware red-ray program.
`finish=largest_pocket` applies that program as Stage A, recomputes
4-connected zero regions on the expanded grid, and fills the unique largest
newly enclosed pocket with the color of the adjacent blocker that caps it.

Inputs are matched across settings.  The first two demonstrations deliberately
contain multiple pocket sizes, locations, and marker colors so that canonical,
smallest-pocket, first-pocket, fixed-color, and fill-all shortcuts do not fit the
visible lesson.  Query 0 is a substantive 30x30 case.  Public export remains the
standard train input/output plus one revealed test input at a time; settings,
programs, future queries, and test labels remain private.
