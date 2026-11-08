(rule! (lambda (g)
         (begin
           (define yellows
             (filter (lambda (cell) (= (third cell) 4)) (grid-cells g)))
           (define (payload-color cell)
             (find-first (lambda (value) (or (= value 7) (= value 9)))
                         (neighbors-8 g (first cell) (second cell) -1)))
           (define hit (find-first (lambda (cell) (payload-color cell)) yellows))
           (define target (if hit (payload-color hit) #f))
           (if target
               (for/fold ((out g))
                 ((cell (grid-cells g)))
                 (if (= (third cell) target)
                     (set-cell out (first cell) (second cell) 8)
                     out))
               g))))
