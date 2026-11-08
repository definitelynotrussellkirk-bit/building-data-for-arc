(rule!
  (let ()
    (define stage g)
    (define (crossing? r c)
      (let ([v (at stage r c)])
        (and (= (at g r c) 0)
             (not (= v 0))
             (not (= v 9))
             (= (at stage (- r 1) (- c 1)) v)
             (= (at stage (- r 1) (+ c 1)) v)
             (= (at stage (+ r 1) (- c 1)) v)
             (= (at stage (+ r 1) (+ c 1)) v))))
    (for*/fold ([out stage])
               ([r (in-range 1 (- (rows g) 1))]
                [c (in-range 1 (- (cols g) 1))])
      (if (crossing? r c)
          (let* ([o1 (set-cell out r c 9)]
                 [o2 (set-cell o1 (- r 1) c 9)]
                 [o3 (set-cell o2 (+ r 1) c 9)]
                 [o4 (set-cell o3 r (- c 1) 9)])
            (set-cell o4 r (+ c 1) 9))
          out))))
