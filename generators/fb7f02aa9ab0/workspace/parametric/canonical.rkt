(rule!
  (let ((dummy 0))
    (define (cell<? a b)
      (or (< (first a) (first b))
          (and (= (first a) (first b)) (< (second a) (second b)))))
    (define (norm color) (sort (normalize-cells (find-color g color)) cell<?))
    (define (has-cell? p cells) (member? p cells))
    (define a (norm 1))
    (define b (norm 2))
    (define op (cond [(not (empty? (find-color g 3))) 'union]
                     [(not (empty? (find-color g 4))) 'inter]
                     [(not (empty? (find-color g 6))) 'xor]
                     [else 'union]))
    (define res0
      (cond
        [(eq? op 'union) (remove-duplicates (append a b))]
        [(eq? op 'inter) (filter (lambda (p) (has-cell? p b)) a)]
        [else (append (filter (lambda (p) (not (has-cell? p b))) a)
                      (filter (lambda (p) (not (has-cell? p a))) b))]))
    (define res (sort (normalize-cells res0) cell<?))
    (if (empty? res)
        (empty-grid 1 1 0)
        (let* ((bb (bbox-of-cells res))
               (out (empty-grid (+ 1 (third bb)) (+ 1 (fourth bb)) 0)))
          (paint-cells out res 8)))))