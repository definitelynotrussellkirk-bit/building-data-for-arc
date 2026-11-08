(rule!
  (let* ((seed (first (find-color g 2)))
         (source-region
          (connected-region g (first seed) (second seed)
                            (lambda (r c v) (or (= v 0) (= v 2))) 4))
         (source-zeros
          (filter (lambda (p) (= (at g (first p) (second p)) 0))
                  source-region))
         (port-count (length (find-color g 1)))
         (anchors (sort (find-color g 3) cell<))
         (selected-anchor (nth anchors (- port-count 1)))
         (target-region
          (connected-region g (first selected-anchor) (second selected-anchor)
                            (lambda (r c v) (or (= v 0) (= v 3))) 4))
         (target-zeros
          (filter (lambda (p) (= (at g (first p) (second p)) 0))
                  target-region)))
    (paint-cells (paint-cells g source-zeros 8) target-zeros 8)))