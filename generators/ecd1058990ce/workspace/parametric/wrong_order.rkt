(rule! (lambda (g)
  (let* ((target (at g 0 0))
         (original-column-counts
          (for/list ((c (in-range (cols g))))
            (for/sum ((r (in-range (rows g))))
              (if (= (at g r c) target) 1 0))))
         (best-count (apply max original-column-counts))
         (selected-column
          (for/first ((c (in-range (length original-column-counts)))
                      #:when (= (list-ref original-column-counts c) best-count))
            c))
         (row-scales
          (for/list ((r (in-range (rows g))))
            (if (>= (for/sum ((c (in-range (cols g))))
                      (if (= (at g r c) target) 1 0))
                    2)
                10
                1)))
         (intermediate (scale-map g row-scales (make-list (cols g) 1)))
         (column-scales
          (for/list ((c (in-range (cols intermediate))))
            (if (= c selected-column) 28 1))))
    (scale-map intermediate (make-list (rows intermediate) 1) column-scales))))