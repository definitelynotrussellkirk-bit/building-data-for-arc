(rule!
  (let ((dummy 0))
    (define (turn v dr dc)
      (cond [(= v 6)
             (cond [(and (= dr 0) (= dc 1)) (list -1 0)]
                   [(and (= dr 0) (= dc -1)) (list 1 0)]
                   [(and (= dr -1) (= dc 0)) (list 0 1)]
                   [else (list 0 -1)])]
            [(= v 7)
             (cond [(and (= dr 0) (= dc 1)) (list 1 0)]
                   [(and (= dr 0) (= dc -1)) (list -1 0)]
                   [(and (= dr -1) (= dc 0)) (list 0 -1)]
                   [else (list 0 1)])]
            [else (list dr dc)]))
    (define (trace r c mirrors?)
      (let loop ([rr r] [cc c] [dr 0] [dc 1] [fuel (* (rows g) (cols g) 8)] [path (list)])
        (let ((nr (+ rr dr)) (nc (+ cc dc)))
          (cond [(or (= fuel 0) (not (in-bounds? nr nc (rows g) (cols g)))) (reverse path)]
                [(= (at g nr nc) 5) (reverse path)]
                [(and (not (= (at g nr nc) 0))
                      (not (and mirrors? (or (= (at g nr nc) 6) (= (at g nr nc) 7)))))
                 (reverse path)]
                [else
                 (let* ((v (at g nr nc))
                        (nd (turn v dr dc)))
                   (loop nr nc (first nd) (second nd) (- fuel 1) (cons (list nr nc) path)))]))))
    (for/fold ([out g]) ([seed (in-list (find-color g 2))])
      (for/fold ([acc out]) ([p (in-list (trace (first seed) (second seed) #f))])
        (if (= (at acc (first p) (second p)) 0)
            (set-cell acc (first p) (second p) 7)
            acc)))))