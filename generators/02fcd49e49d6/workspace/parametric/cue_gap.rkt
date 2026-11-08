(rule!
  (let ((target-gap
         (for/fold ([gap -1]) ([r (in-range (rows g))])
           (let ((cols-hit
                  (for/list ([c (in-range (cols g))]
                             #:when (= (at g r c) 8))
                    c)))
             (if (= (length cols-hit) 2)
                 (let ((c1 (first cols-hit))
                       (c2 (second cols-hit)))
                   (if (= (modulo (+ c1 c2) 2) 0)
                       (let ((mid (quotient (+ c1 c2) 2)))
                         (if (= (at g r mid) 1)
                             (- c2 c1)
                             gap))
                       gap))
                 gap)))))
    (for/fold ([out g]) ([r (in-range (rows g))])
      (let ((cols-hit
             (for/list ([c (in-range (cols g))]
                        #:when (= (at g r c) 8))
               c)))
        (if (= (length cols-hit) 2)
            (let ((c1 (first cols-hit))
                  (c2 (second cols-hit)))
              (if (= (modulo (+ c1 c2) 2) 0)
                  (let ((mid (quotient (+ c1 c2) 2)))
                    (if (and (= (at g r mid) 0)
                             (= (- c2 c1) target-gap))
                        (set-cell out r mid 2)
                        out))
                  out))
            out)))))
