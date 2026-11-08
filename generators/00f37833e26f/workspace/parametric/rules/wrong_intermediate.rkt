(rule!
  (let ((dummy 0))
    (define (normalize cells)
      (let ((bb (bbox-of-cells cells)))
        (map (lambda (p)
               (list (- (first p) (first bb))
                     (- (second p) (second bb))))
             cells)))
    (define (crop-green cells)
      (let ((bb (bbox-of-cells cells)))
        (paint-cells
         (empty-grid (+ (- (third bb) (first bb)) 1)
                     (+ (- (fourth bb) (second bb)) 1)
                     0)
         (map (lambda (p)
                (list (- (first p) (first bb))
                      (- (second p) (second bb))))
              cells)
         3)))
    (let* ((src (first (objects (keep-only g 3) 0)))
           (mask (first (objects (keep-only g 5) 0)))
           (src-norm (normalize (obj-cells src)))
           (mask-norm (normalize (obj-cells mask)))
           ;; The correct residual is computed, then deliberately ignored.
           (kept (filter (lambda (p) (not (member p mask-norm))) src-norm))
           ;; Wrong intermediate: Stage B sees the connected source, not residual.
           (source-grid
            (paint-cells
             (empty-grid (+ 1 (apply max (map first src-norm)))
                         (+ 1 (apply max (map second src-norm)))
                         0)
             src-norm
             3))
           (parts (objects source-grid 0))
           (selected (pick-max parts obj-size)))
      (crop-green (obj-cells selected)))))
