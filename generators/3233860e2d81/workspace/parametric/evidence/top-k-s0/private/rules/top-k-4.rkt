(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define colors (filter (lambda (c) (!= c 0)) (grid-colors g)))
             (define color-counts
               (map (lambda (c) (list c (length (find-color g c)))) colors))
             (define sorted (sort-by color-counts (lambda (cc) (- 0 (second cc)))))
             (build-grid 4 1 (r c) (first (nth sorted r)))))))