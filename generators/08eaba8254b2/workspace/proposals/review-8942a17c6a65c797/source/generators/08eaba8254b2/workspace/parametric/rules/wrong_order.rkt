(rule!
 (let ((dirs4 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1))))
   (define (green-neighbors grid r c)
     (filter (lambda (d)
               (let ((rr (+ r (first d))) (cc (+ c (second d))))
                 (and (in-bounds? rr cc (rows grid) (cols grid))
                      (= (at grid rr cc) 3))))
             dirs4))
   (define paired-input
     (grid-from-fn
      (rows g) (cols g)
      (lambda (r c)
        (let ((v (at g r c)))
          (if (and (= v 3)
                   (= (length (green-neighbors g r c)) 1)
                   (let* ((d (first (green-neighbors g r c)))
                          (rr (+ r (first d)))
                          (cc (+ c (second d))))
                     (= (length (green-neighbors g rr cc)) 1)))
              8
              v)))))
   (grid-from-fn
    4 (cols paired-input)
    (lambda (r c)
      (if (!= (zero? (at paired-input r c))
              (zero? (at paired-input (+ r 5) c)))
          3
          0)))))
