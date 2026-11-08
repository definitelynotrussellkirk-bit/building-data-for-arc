(rule! (letrec ([dedup-consecutive
            (lambda (lst)
              (cond [(empty? lst) '()]
                    [(empty? (rest lst)) lst]
                    [(equal? (first lst) (second lst))
                     (dedup-consecutive (rest lst))]
                    [else (cons (first lst)
                                (dedup-consecutive (rest lst)))]))])
    (dedup-consecutive g)))
