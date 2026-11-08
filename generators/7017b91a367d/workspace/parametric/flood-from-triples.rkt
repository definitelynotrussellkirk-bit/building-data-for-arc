(rule!
  (let ((dummy 0))
    (define (t13c-panel grid idx top-rows)
      (subgrid grid 0 (* idx 6) (- top-rows 1) (+ (* idx 6) 4)))
    (define panels (map (lambda (i) (t13c-panel g i (rows g))) (range 3)))
    (define counts
      (grid-from-fn 5 5
        (lambda (r c)
          (let ((cnt (count-where (lambda (panel) (not (= (at panel r c) 0))) panels)))
            (cond [(= cnt 0) 0] [(= cnt 1) 2] [(= cnt 2) 4] [else 8])))))
    (define dirs (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))
    (define (neighbors p)
      (filter (lambda (q) (in-bounds? (first q) (second q) 5 5))
              (map (lambda (d) (list (+ (first p) (first d))
                                     (+ (second p) (second d)))) dirs)))
    (define (eligible? p)
      (let ((v (at counts (first p) (second p))))
        (or (= v 4) (= v 8))))
    (define seeds
      (filter (lambda (p) (= (at counts (first p) (second p)) 8))
              (grid-positions counts)))
    (define (flood pending seen)
      (if (empty? pending)
          seen
          (let ((p (first pending)))
            (if (member? p seen)
                (flood (rest pending) seen)
                (flood (append (rest pending)
                               (filter eligible? (neighbors p)))
                       (cons p seen))))))
    (define reached (flood seeds (list)))
    (grid-from-fn 5 5
      (lambda (r c)
        (if (member? (list r c) reached) 8 (at counts r c))))))
