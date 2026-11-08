(rule!
  (let ((seeds (filter (lambda (cell)
                         (let ((v (third cell))) (and (not (= v 0)) (not (= v 9)))))
                       (grid-cells g))))
    (define (clear-row? r c1 c2)
      (for/and ([c (in-range (min c1 c2) (+ (max c1 c2) 1))])
        (not (= (at g r c) 9))))
    (define (clear-col? c r1 r2)
      (for/and ([r (in-range (min r1 r2) (+ (max r1 r2) 1))])
        (not (= (at g r c) 9))))
    (define (visible? seed r c)
      (let ((sr (first seed)) (sc (second seed)))
        (or (and (= sr r) (clear-row? r sc c))
            (and (= sc c) (clear-col? c sr r)))))
    (grid-from-fn (rows g) (cols g)
      (lambda (r c)
        (cond [(= (at g r c) 9) 9]
              [(>= (count-where (lambda (seed) (visible? seed r c)) seeds) 2) 8]
              [else 0])))))