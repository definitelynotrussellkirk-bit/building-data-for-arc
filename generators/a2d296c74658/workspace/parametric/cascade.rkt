(rule!
  (let ([stage-a (for*/fold ([out g])
             ([r (in-range 1 (- (rows g) 1))]
              [c (in-range (cols g))])
    (if (and (= (at g r c) 0)
             (= (at g (- r 1) c) 7)
             (= (at g (+ r 1) c) 7))
        (set-cell out r c 4)
        out))])
    (for*/fold ([out stage-a])
               ([r (in-range (rows stage-a))]
                [c (in-range 1 (- (cols stage-a) 1))])
      (if (and (= (at stage-a r c) 0)
               (= (at stage-a r (- c 1)) 4)
               (= (at stage-a r (+ c 1)) 4))
          (set-cell out r c 2)
          out))))
