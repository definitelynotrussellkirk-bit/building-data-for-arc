(rule!
  (let ((dummy 0))
    (define (has? p cells) (member? p cells))
    (define (component-before? a b)
      (or (> (obj-size a) (obj-size b))
          (and (= (obj-size a) (obj-size b))
               (or (< (obj-r1 a) (obj-r1 b))
                   (and (= (obj-r1 a) (obj-r1 b))
                        (< (obj-c1 a) (obj-c1 b)))))))
    ;; Stage A: normalize both source shapes and retain their exact overlap.
    (define s2 (normalize-cells (find-color g 2)))
    (define s3 (normalize-cells (find-color g 3)))
    (define inter (filter (lambda (p) (has? p s3)) s2))
    (define intermediate
      (paint-cells (empty-grid (rows g) (cols g) 0) inter 8))
    ;; Stage B: select the largest overlap component; row-major breaks ties.
    (define parts (objects intermediate 0))
    (if (empty? parts)
        intermediate
        (paint-cells (empty-grid (rows g) (cols g) 0)
                     (obj-cells (first (sort parts component-before?)))
                     8))))
