(rule!
 (let* ((horizontal-centers
         (for*/list ((r (in-range (rows g)))
                     (c (in-range 1 (- (cols g) 1)))
                     #:when (and (= (at g r c) 0)
                                 (not (= (at g r (- c 1)) 0))
                                 (= (at g r (- c 1)) (at g r (+ c 1)))))
           (list r c (at g r (- c 1)))))
        (rank (length horizontal-centers))
        (vertical-centers
         (for*/list ((r (in-range 1 (- (rows g) 1)))
                     (c (in-range (cols g)))
                     #:when (and (= (at g r c) 0)
                                 (not (= (at g (- r 1) c) 0))
                                 (= (at g (- r 1) c) (at g (+ r 1) c))))
           (list r c (at g (- r 1) c))))
        (base
         (for/fold ((out g)) ((item (in-list horizontal-centers)))
           (set-cell out (first item) (second item) (third item))))
        (chosen (list-ref vertical-centers (- rank 1))))
   (set-cell base (first chosen) (second chosen) (third chosen))))
