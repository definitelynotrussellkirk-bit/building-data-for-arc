# Blind visible-only solve

No generator, reference rule, task notes, audit, or private labels were consulted.
I read only the presented challenge and its visible demonstration outputs.

Demonstration 0 is 14x15 in and out: the 5-cell staircase moves down to the bottom;
the 2-cell bar and already-bottom 4-cell square stay in place. Demonstration 1
is 12x12: the 6-cell bar moves from the top to the bottom, while the 2-cell bar
stays. Demonstration 2 is 17x12: the lower 6-cell bar moves to the bottom and
the upper 2-cell bar stays. Counts, shapes, and horizontal positions are preserved.

My first hypothesis is that the largest connected object is translated vertically
until its bottommost cell reaches the bottom border. I use monochromatic four-way
connectivity and infer the background by majority. These connectivity conventions
are assumptions: the demonstrations do not distinguish multicolor connected
objects from touching monochromatic objects. The first query contains touching
colors 6 and 2, so this distinction could matter.

Other unresolved rivals include lowering every object larger than two cells,
or lowering only the widest object. The already-bottom square in demonstration 0
does not distinguish those alternatives. The observed movement selects the largest
object in all three demonstrations, so I choose that compact generalization.
The demonstrations also do not establish collision handling or tied largest sizes.
No masked-query output was viewed, and no synthetic failure revision was created.

Revision 1 implements this hypothesis; its visible-example checker outcome is
recorded by the packet tool. Hidden correctness remains unscored here.
