(rule!
 (lambda (g)
  (define coarse-placement 'transpose)
  (define matching-mode 'color)
  (define n (for/first ([c (in-range (cols g))] #:when (= (at g 0 c) 5)) c))
  (define starts
    (for/list ([left (in-range 0 (+ 1 (- (cols g) n)) (+ n 1))]
               #:when (for*/or ([r (in-range n)] [c (in-range n)])
                        (> (at g r (+ left c)) 0))) left))
  (define slots
    (for/list ([left starts])
      (list
       (for*/first ([r (in-range n)] [c (in-range n)]
                    #:when (> (at g r (+ left c)) 0))
         (at g r (+ left c)))
       left
       (for*/first ([r (in-range (+ (* 2 n) 2) (+ (* 2 n) 4))]
                    [c (in-range n)]
                    #:when (and (> (at g r (+ left c)) 0)
                                (not (= (at g r (+ left c)) 5))))
         (at g r (+ left c))))))
  (grid-from-fn (* n n) (* n n)
    (lambda (r c)
      (define out-r (quotient r n))
      (define out-c (quotient c n))
      (define source-r (if (eq? coarse-placement 'transpose) out-c out-r))
      (define source-c (if (eq? coarse-placement 'transpose) out-r out-c))
      (define hit
        (for/or ([left starts])
          (define v (at g (+ n 1 source-r) (+ left source-c)))
          (and (> v 0) (list v left))))
      (if (not hit) 0
          (let* ([slot (if (eq? matching-mode 'column)
                           (for/first ([s slots] #:when (= (second s) (second hit))) s)
                           (for/first ([s slots] #:when (= (first s) (first hit))) s))]
                 [pixel (at g (remainder r n) (+ (second slot) (remainder c n)))])
            (if (> pixel 0) (third slot) 0)))))))
