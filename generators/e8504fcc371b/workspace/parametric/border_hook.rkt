(rule!
  (let* ((cmd-cell (last (filter (lambda (cell) (member (third cell) (list 1 2 3 4)))
                                 (grid-cells g))))
         (seed-cell (last (filter (lambda (cell)
                                    (and (not (= (third cell) 0))
                                         (not (member (third cell) (list 1 2 3 4)))))
                                  (grid-cells g))))
         (code (third cmd-cell))
         (color (third seed-cell))
         (sr (first seed-cell))
         (sc (second seed-cell))
         (delta (cond [(= code 1) (list -1 0)]
                      [(= code 2) (list 1 0)]
                      [(= code 3) (list 0 -1)]
                      [else (list 0 1)]))
         (dr (first delta))
         (dc (second delta))
         (ray-length (cond [(= code 1) sr]
                           [(= code 2) (- (- (rows g) 1) sr)]
                           [(= code 3) sc]
                           [else (- (- (cols g) 1) sc)]))
         (end-r (+ sr (* dr ray-length)))
         (end-c (+ sc (* dc ray-length)))
         (perimeter
          (append
           (for/list ([c (in-range 0 (cols g))]) (list 0 c))
           (for/list ([r (in-range 1 (rows g))]) (list r (- (cols g) 1)))
           (for/list ([c (in-range (- (cols g) 2) -1 -1)]) (list (- (rows g) 1) c))
           (for/list ([r (in-range (- (rows g) 2) 0 -1)]) (list r 0))))
         (end-index
          (cond [(= end-r 0) end-c]
                [(= end-c (- (cols g) 1)) (+ (- (cols g) 1) end-r)]
                [(= end-r (- (rows g) 1))
                 (+ (- (cols g) 1)
                    (- (rows g) 1)
                    (- (- (cols g) 1) end-c))]
                [else
                 (+ (- (cols g) 1)
                    (- (rows g) 1)
                    (- (cols g) 1)
                    (- (- (rows g) 1) end-r))]))
         (ray-cells
          (for/list ([k (in-range 1 (+ ray-length 1))])
            (list (+ sr (* dr k)) (+ sc (* dc k)))))
         (hook-cells
          (for/list ([k (in-range 1 (+ ray-length 1))])
            (list-ref perimeter (modulo (+ end-index k) (length perimeter)))))
         (paint-cells* (append ray-cells hook-cells)))
    (for/fold ([out g]) ([cell (in-list paint-cells*)])
      (let ((r (first cell))
            (c (second cell)))
        (if (= (at out r c) 0)
            (set-cell out r c color)
            out)))))
