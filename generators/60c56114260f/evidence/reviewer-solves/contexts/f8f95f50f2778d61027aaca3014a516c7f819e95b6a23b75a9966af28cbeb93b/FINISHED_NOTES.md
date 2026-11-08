# Blind solve work log

This is a reviewer-authored experiment summary, not a captured token-level conversation. Earlier rule exposure: no. No generator, reference rule, private labels, or previous explanations were opened. Only challenge.json and local visible-example experiments were used.

Visible observations: each nonzero color marks a small object. Output dimensions equal the number of objects/colors. The output is a symmetric 0/8 matrix with an 8 diagonal. Repeated shapes in the third example form one equivalence block.

Hypothesis tested: color objects are ordered by first row-major occurrence; entry (i,j) is 8 exactly when their shapes agree up to translation, rotation, and reflection. The executable probe compares translation-only, rotation-only, and dihedral invariance on all three visible examples. Its measured results are in probe_shapes.json. Translation and rotation alone fail visible examples; full dihedral equivalence matches all three.

Revision 1 implements the dihedral hypothesis. No intentionally wrong solution was submitted. The rejected alternatives are hypothesis probes, not failed solve attempts. Assumptions not independently settled by these examples include disconnected pieces sharing a color and objects whose row-major order differs from their bounding-box order. Hidden-query correctness is withheld by the checker.
