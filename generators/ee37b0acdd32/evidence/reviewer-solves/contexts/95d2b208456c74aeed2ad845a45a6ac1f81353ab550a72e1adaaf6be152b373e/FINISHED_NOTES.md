# Visible-only solve notes

The three demonstrations consistently treat each monochrome 4-connected region as one object. Blue 1 and red 2 mark endpoints in the graph formed by edge-touching objects. The output is same-size, zero elsewhere, and recolors exactly the unique chain of objects connecting those endpoints to 8; touching leaf objects are omitted even when their color also appears on the route.

Implementation plan: extract monochrome components, build the 4-contact graph, BFS from the unique blue component to the unique red component, reconstruct the parent path, and paint every cell in those path components 8 on a zero grid. This is derived from the visible examples. I had earlier rule exposure during generator review, but did not reopen or consult any reference while writing this solve revision.
