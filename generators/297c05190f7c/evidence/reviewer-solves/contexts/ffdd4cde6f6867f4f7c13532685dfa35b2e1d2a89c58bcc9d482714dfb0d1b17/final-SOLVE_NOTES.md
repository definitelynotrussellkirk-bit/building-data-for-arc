# Solve work log

## Prior exposure

Before this recorded solve I had already reviewed the selected generator and its
rule-related tests while performing the requested adversarial hardening. This is
therefore **not a blind rule-discovery claim**. During the recorded solve phase I
consulted only `solve/challenge.json`, the solve instructions, and my own Python;
I did not reopen the generator, Racket authority, reference solutions, or private
query labels.

## Revision 1

The visible examples support the following transformation:

1. Treat zero as background.
2. Flood-fill each maximal nonzero same-color component using cardinal
   adjacency only.
3. For each component independently, find its minimum and maximum row and
   column.
4. Paint the complete tight rectangle with that component's color; leave all
   other cells zero.

Evidence in the visible pairs:

- The long color-4 L in training example 1 becomes a filled rectangle, while
  the separate color-1 object gets its own rectangle.
- Training example 2 contains a diagonal color-8 arrangement. Cardinal
  connectivity keeps the singleton separate from the three-cell component,
  matching the displayed output rather than merging by color or 8-connectivity.
- Training example 3 contains two disconnected color-5 objects; they are boxed
  separately, ruling out one bounding box per color.

I implemented a direct BFS over cardinal neighbors and construct the output on
a fresh zero grid. The main remaining uncertainty before checking is only the
withheld query label; the visible examples determine the component and fill
operations without an observed exception.
