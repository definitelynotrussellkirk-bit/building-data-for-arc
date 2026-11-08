(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define bg (mode g -1))
             (define colors (grid-colors g bg))
             (define source-color
               (argmax (lambda (c) (length (find-color g c))) colors))
             (define paint-color (find-first (lambda (c) (!= c source-color)) colors))
             (define paint-markers (find-color g paint-color))
             (define source-cells (find-color g source-color))
             (define same-row?
               (all? (lambda (p) (= (first p) (first (first paint-markers))))
                     paint-markers))
             (define (cell-sign x) (cond ((< x 0) -1) ((> x 0) 1) (else 0)))
             (define (same-list? a b) (equal? (sort a <) (sort b <)))
             (if same-row?
                 (let* ((marker-row (first (first paint-markers)))
                        (marker-cols (map second paint-markers))
                        (target-row (for/first ((r (range 0 h)) #:when
                                                 (and
                                                   (!= r marker-row)
                                                   (same-list? marker-cols
                                                               (map second
                                                                    (filter (lambda (p)
                                                                              (= (first p)
                                                                                 r))
                                                                            source-cells)))))
                                               r))
                        (dir (if (> target-row marker-row) -1 1)))
                   (foldl (lambda (p acc)
                            (let ((r (first p))
                                  (c (second p)))
                              (if (= (cell-sign (- r marker-row)) dir)
                                  (let ((nr (+ target-row (- marker-row r))))
                                    (if (and (>= nr 0) (< nr h))
                                        (set-cell acc nr c source-color)
                                        acc))
                                  acc)))
                          g
                          source-cells))
                 (let* ((marker-col (second (first paint-markers)))
                        (marker-rows (map first paint-markers))
                        (target-col (for/first ((c (range 0 w)) #:when
                                                 (and
                                                   (!= c marker-col)
                                                   (same-list? marker-rows
                                                               (map first
                                                                    (filter (lambda (p)
                                                                              (= (second p)
                                                                                 c))
                                                                            source-cells)))))
                                               c))
                        (dir (if (> target-col marker-col) -1 1)))
                   (foldl (lambda (p acc)
                            (let ((r (first p))
                                  (c (second p)))
                              (if (= (cell-sign (- c marker-col)) dir)
                                  (let ((nc (+ target-col (- marker-col c))))
                                    (if (and (>= nc 0) (< nc w))
                                        (set-cell acc r nc source-color)
                                        acc))
                                  acc)))
                          g
                          source-cells)))))))