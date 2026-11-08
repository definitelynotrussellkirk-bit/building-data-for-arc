# Rules

1. Infer the modal background and find every lawful 4×4 frame around a uniform
   2×2 core.
2. Every background gap in the perimeter launches one member in its outward
   row/column/diagonal direction.
3. Search paths geometrically. When projected next segments share a destination,
   swap, or cross diagonally, move each bundle independently to its pre-event
   cells.
4. `vector_sum` merges all members and resets the digital-line phase to the
   primitive sum of the two courses. `stop` terminates both bundles instead.
5. Paint background only; preserve source frames, cores, and earlier trails.
