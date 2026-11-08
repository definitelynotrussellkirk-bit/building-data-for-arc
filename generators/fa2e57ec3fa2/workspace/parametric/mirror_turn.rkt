(rule!
  (let ((dummy 0))
    (define (trace-vertical r c dr)
      (let loop ([rr (+ r dr)] [path (list)])
        (cond [(not (in-bounds? rr c (rows g) (cols g))) (reverse path)]
              [(= (at g rr c) 0)
               (loop (+ rr dr) (cons (list rr c) path))]
              [else (reverse path)])))
    (define (trace r c)
      (let loop ([cc (+ c 1)] [path (list)])
        (cond [(not (in-bounds? r cc (rows g) (cols g))) (reverse path)]
              [(= (at g r cc) 0)
               (loop (+ cc 1) (cons (list r cc) path))]
              [(= (at g r cc) 6)
               (append (reverse path) (trace-vertical r cc -1))]
              [(= (at g r cc) 8)
               (append (reverse path) (trace-vertical r cc 1))]
              [else (reverse path)])))
    (for/fold ([out g]) ([seed (in-list (find-color g 2))])
      (for/fold ([acc out]) ([p (in-list (trace (first seed) (second seed)))])
        (if (= (at acc (first p) (second p)) 0)
            (set-cell acc (first p) (second p) 7)
            acc)))))
