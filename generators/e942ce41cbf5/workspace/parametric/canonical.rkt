(rule!
  (let ((dummy 0))
    (define (cell<? a b)
      (or (< (first a) (first b))
          (and (= (first a) (first b)) (< (second a) (second b)))))
    (define (norm cells) (sort (normalize-cells cells) cell<?))
    (define (rot cells) (norm (rotate-cells-cw cells)))
    (define (flip-v cells)
      (let* ((n (norm cells)) (cmax (apply max (map second n))))
        (norm (map (lambda (p) (list (first p) (- cmax (second p)))) n))))
    (define a (norm (find-color g 1)))
    (define b0 (norm (find-color g 2)))
    (define op (cond [(not (empty? (find-color g 3))) 0]
                     [(not (empty? (find-color g 4))) 1]
                     [(not (empty? (find-color g 6))) 2]
                     [else 0]))
    (define tr (cond [(not (empty? (find-color g 7))) 0]
                     [(not (empty? (find-color g 8))) 1]
                     [(not (empty? (find-color g 9))) 5]
                     [else 0]))
    (define b (cond [(= tr 1) (rot b0)] [(= tr 5) (flip-v b0)] [else b0]))
    (define (has? p cells) (member? p cells))
    (define res0
      (cond [(= op 0) (remove-duplicates (append a b))]
            [(= op 1) (filter (lambda (p) (has? p b)) a)]
            [else (append (filter (lambda (p) (not (has? p b))) a)
                          (filter (lambda (p) (not (has? p a))) b))]))
    (define res (norm res0))
    (if (empty? res)
        (empty-grid 1 1 0)
        (let* ((bb (bbox-of-cells res))
               (out (empty-grid (+ 1 (third bb)) (+ 1 (fourth bb)) 0)))
          (paint-cells out res 8)))))