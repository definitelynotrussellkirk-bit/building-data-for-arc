(rule! (lambda (grid)
  (let* ((height (rows grid))
         (width (cols grid))
         (separator-row
           (first
             (first
               (filter (lambda (row-info) (= (second row-info) 9))
                       (full-rows grid)))))
         (template-grid
           (crop-to-content
             (keep-only
               (subgrid grid 0 0 (- separator-row 1) (- width 1))
               1)))
         (template-shape
           (grid-from-fn (rows template-grid) (cols template-grid)
             (lambda (row col)
               (if (= (cell-at template-grid row col) 0) 0 1))))
         (lower-grid
           (subgrid grid (+ separator-row 1) 0 (- height 1) (- width 1)))
         (candidate-objs (objects lower-grid 0)))
    (define (normalize-shape shape-grid)
      (grid-from-fn (rows shape-grid) (cols shape-grid)
        (lambda (row col)
          (if (= (cell-at shape-grid row col) 0) 0 1))))
    (define (same-shape? shape-a shape-b)
      (and (= (rows shape-a) (rows shape-b))
           (= (cols shape-a) (cols shape-b))
           (= (length (grid-colors (grid-xor shape-a shape-b 0))) 1)
           (= (first (grid-colors (grid-xor shape-a shape-b 0))) 0)))
    (define (matches-template? obj)
      (let* ((shape-grid
               (normalize-shape
                 (crop-to-content
                   (subgrid lower-grid
                            (obj-r1 obj) (obj-c1 obj)
                            (obj-r2 obj) (obj-c2 obj))))))
        (or (same-shape? shape-grid template-shape)
            (same-shape? (rotate-cw shape-grid) template-shape)
            (same-shape? (rotate-180 shape-grid) template-shape)
            (same-shape? (rotate-ccw shape-grid) template-shape))))
    (reduce (lambda (acc obj)
      (if (matches-template? obj)
          (recolor-cells acc
            (map (lambda (position)
                   (list (+ separator-row 1 (fst position))
                         (snd position)))
                 (obj-cells obj))
            2)
          acc))
      grid
      candidate-objs))))