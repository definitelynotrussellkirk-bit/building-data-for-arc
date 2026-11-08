(rule!
  (for/fold ([out g]) ([p (in-list (find-color g 2))])
    (for/fold ([acc out]) ([d (in-list cardinal-deltas)])
      (let ((rr (+ (first p) (first d)))
            (cc (+ (second p) (second d))))
        (if (and (in-bounds? rr cc (rows g) (cols g)) (= (at acc rr cc) 0))
            (set-cell acc rr cc 6)
            acc)))))