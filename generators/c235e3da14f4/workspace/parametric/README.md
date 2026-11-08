# c235e3da14f4 parametric family

`size_rule=smallest` is the exact selected canonical Racket program.
`size_rule=largest` selects the first largest non-2 same-color component.
Both settings use identical episode inputs. The selected component and its
bounding box are the input-dependent intermediate; the final step crops the
original grid to that box. Demonstrations separate cell-count rank from bbox
rank and exercise color 0 as an ordinary candidate object.
