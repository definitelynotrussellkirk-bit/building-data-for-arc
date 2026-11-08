(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (bg 8)
         ;; The non-cyan cells are one unbranched path. Find its cells and
         ;; choose either degree-one endpoint as the traversal start.
         (cells
          (for*/list ((r (range 0 h))
                      (c (range 0 w))
                      #:when (not (= (cell-at g r c) bg)))
            (list r c)))
         (cell-set (make-hash))
         (seed-cell-set
          (for ((cell cells))
            (hash-set! cell-set cell #t)))
         (start #f)
         (find-endpoint
          (for ((cell cells))
            (let ((degree
                   (count-if
                    (lambda (neighbor) (hash-has-key? cell-set neighbor))
                    (list (list (- (first cell) 1) (second cell))
                          (list (+ (first cell) 1) (second cell))
                          (list (first cell) (- (second cell) 1))
                          (list (first cell) (+ (second cell) 1))))))
              (when (and (not start) (= degree 1))
                (set! start cell)))))
         ;; Trace the unique path and collect its positions in endpoint order.
         (path (list))
         (visited (make-hash))
         (trace-path
          (let trace ((current start))
            (when (and current
                       (hash-has-key? cell-set current)
                       (not (hash-has-key? visited current)))
              (hash-set! visited current #t)
              (set! path (append path (list current)))
              (let ((next
                     (find
                      (lambda (neighbor)
                        (and (hash-has-key? cell-set neighbor)
                             (not (hash-has-key? visited neighbor))))
                      (list (list (- (first current) 1) (second current))
                            (list (+ (first current) 1) (second current))
                            (list (first current) (- (second current) 1))
                            (list (first current) (+ (second current) 1))))))
                (trace next)))))
         ;; Reverse only the color sequence; every path coordinate is retained.
         (path-colors
          (map (lambda (position)
                 (cell-at g (first position) (second position)))
               path))
         (reversed-base (reverse path-colors))
         (reversed-colors
          (append (rest reversed-base) (list (first reversed-base))))
         (result (make-hash)))
    (for* ((r (range 0 h)) (c (range 0 w)))
      (hash-set! result (list r c) bg))
    (for ((i (range 0 (length path))))
      (hash-set! result (list-ref path i) (list-ref reversed-colors i)))
    (grid-from-fn h w
                  (lambda (r c) (hash-ref result (list r c) bg))))))