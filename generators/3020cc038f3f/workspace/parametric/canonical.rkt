(rule!
  (let ((dummy 0))
    (define (has? p cells) (member? p cells))
    (define a (normalize-cells (find-color g 1)))
    (define b (normalize-cells (find-color g 2)))
    (define ba (bbox-of-cells a))
    (define bb (bbox-of-cells b))
    (define out-h (max (if ba (+ 1 (third ba)) 0) (if bb (+ 1 (third bb)) 0)))
    (define out-w (max (if ba (+ 1 (fourth ba)) 0) (if bb (+ 1 (fourth bb)) 0)))
    (define ctrl (at g 0 0))
    (define res
      (cond [(= ctrl 3) (remove-duplicates (append a b))]
            [(= ctrl 4) (append (filter (lambda (p) (not (has? p b))) a)
                                (filter (lambda (p) (not (has? p a))) b))]
            [(= ctrl 5) (filter (lambda (p) (has? p b)) a)]
            [else (list)]))
    (if (empty? res)
        (empty-grid 1 1 0)
        (paint-cells (empty-grid out-h out-w 0) res 8))))