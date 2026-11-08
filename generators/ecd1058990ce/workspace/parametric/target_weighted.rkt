(rule! (lambda (g)
  (let* ((target (at g 0 0))
         (row-scales
          (for/list ((r (in-range (rows g))))
            (if (>= (for/sum ((c (in-range (cols g))))
                      (if (= (at g r c) target) 1 0))
                    2)
                10
                1)))
         (intermediate (scale-map g row-scales (make-list (cols g) 1)))
         (column-counts
          (for/list ((c (in-range (cols intermediate))))
            (for/sum ((r (in-range (rows intermediate))))
              (if (= (at intermediate r c) target) 1 0))))
         (best-count (apply max column-counts))
         (selected-column
          (for/first ((c (in-range (length column-counts)))
                      #:when (= (list-ref column-counts c) best-count))
            c))
         (column-scales
          (for/list ((c (in-range (cols intermediate))))
            (if (= c selected-column) 28 1))))
    (scale-map intermediate (make-list (rows intermediate) 1) column-scales))))