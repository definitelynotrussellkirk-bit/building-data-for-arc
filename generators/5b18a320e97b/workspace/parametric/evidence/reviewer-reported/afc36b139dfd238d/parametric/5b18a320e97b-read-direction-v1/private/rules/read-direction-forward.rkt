(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((colors (filter (lambda (c) (and (!= c 0) (!= c 5))) (grid-colors g)))
                  (color-first-cell (lambda (col) (first (find-color g col))))
                  (color-all-cells (lambda (col) (find-color g col)))
                  (horizontal (andmap (lambda (col)
                                        (let* ((cells (color-all-cells col))
                                               (rs (map first cells)))
                                          (= 1 (length (unique rs)))))
                                      colors))
                  (sorted-colors (if horizontal
                                     (sort-by colors
                                              (lambda (col)
                                                (first (color-first-cell col))))
                                     (sort-by colors
                                              (lambda (col)
                                                (second (color-first-cell col))))))
                  (n (length sorted-colors)))
             (if horizontal
                 (build-grid n n (r c) (nth sorted-colors r))
                 (build-grid n n (r c) (nth sorted-colors c)))))))