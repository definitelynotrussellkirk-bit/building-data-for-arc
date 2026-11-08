(rule!
  (let ((dummy 0))
    (define (component-before? a b)
      (or (> (obj-size a) (obj-size b))
          (and (= (obj-size a) (obj-size b))
               (or (< (obj-r1 a) (obj-r1 b))
                   (and (= (obj-r1 a) (obj-r1 b))
                        (< (obj-c1 a) (obj-c1 b)))))))
    ;; Counterfactual: skip the intersection and feed normalized color 2 to B.
    (define intermediate
      (paint-cells (empty-grid (rows g) (cols g) 0)
                   (normalize-cells (find-color g 2))
                   8))
    (define parts (objects intermediate 0))
    (if (empty? parts)
        intermediate
        (paint-cells (empty-grid (rows g) (cols g) 0)
                     (obj-cells (first (sort parts component-before?)))
                     8))))
