(rule!
 (let ((dirs4 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1))))
   (define base
     (grid-from-fn
      4 (cols g)
      (lambda (r c)
        (if (!= (zero? (at g r c)) (zero? (at g (+ r 5) c))) 3 0))))
   (define (green-neighbors grid r c)
     (filter (lambda (d)
               (let ((rr (+ r (first d))) (cc (+ c (second d))))
                 (and (in-bounds? rr cc (rows grid) (cols grid))
                      (= (at grid rr cc) 3))))
             dirs4))
   (grid-from-fn
    (rows base) (cols base)
    (lambda (r c)
      (let ((v (at base r c)))
        (if (and (= v 3)
                 (= (length (green-neighbors base r c)) 1)
                 (let* ((d (first (green-neighbors base r c)))
                        (rr (+ r (first d)))
                        (cc (+ c (second d))))
                   (= (length (green-neighbors base rr cc)) 1)))
            8
            v))))))
