# Visible-only solve log

## Scope and exposure

This solve was performed by a fresh, isolated solver agent. I read only this
lane's `README.md` and `challenge.json`, then wrote my own solution and this log.
I have not inspected any generator, rule, canonical dataset, private label,
reference solution, prior solution explanation, shared source helper, or
unrelated repository content. The parent reported that a broad README discovery
had occurred in its own context; none of that discovery's contents were supplied
to this solver. I have no earlier exposure to this task or its reference rule.

## Initial hypothesis

The nonzero connected components are green rectangles with one red cell on a
boundary. The red cell indicates an outward direction. Extend it as a straight
red line to the grid boundary, surrounded on both sides by a green band. The
number of green cells on each side equals the rectangle's depth in the outward
direction minus one. Keep the input pixels and clip the extension at the grid.

The visible examples support the depth relationship directly:

- Training 0: rectangle depths 4, 3, and 3 give band radii 3, 2, and 2.
- Training 1: depths 3 and 5 give radii 2 and 4.
- Training 2: depths 5, 4, and 4 give radii 4, 3, and 3.
- Training 3: depths 2 and 3 give radii 1 and 2.

The bands can be wider than the marked side or extend beyond its ends, so merely
copying the rectangle edge would not explain the examples. The perpendicular
depth determines their width. All supplied markers occupy a unique rectangle
side; the supplied queries have the same unambiguous geometry.

## Revision 1

Implemented connected-component bounding boxes, outward direction from the red
marker, and the depth-minus-one band rule. This is the first implementation.
There were no earlier implementations, failed probes, or revisions. The first
public check will compare this rule with the four visible training examples and
check execution on the two unlabeled queries; private query correctness remains
unknown.

Public check run from the packet root:

```sh
python3 review.py blind check --intent solve --note 'First implementation: extend each red boundary marker outward to the grid edge with green flank radius equal to rectangle depth minus one; this explains the band widths in all four visible examples.'
```

The command exited 0. Public feedback reported revision 1, execution completed,
4/4 visible examples passed, and query label `unknown`. No failure prompted a
revision, and the solution code was left unchanged. This post-check entry only
records the observed feedback.

## Stopping decision

The single geometric rule explains all four visible examples, and the first
public check passed all four. Both supplied query inputs use the same clear
boundary-marker geometry. I am stopping after one implementation and one public
check. Private query correctness is unknown; no hidden-answer check was sought.
