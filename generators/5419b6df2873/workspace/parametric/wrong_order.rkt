(rule!
  (let ([base
         (for*/fold ([out (empty-grid (rows g) (cols g) 0)])
                    ([c (in-range (cols g))]
                     [r (in-range (rows g))])
           (let ([v (at g 0 c)])
             (if (not (= v 0)) (set-cell out r c v) out)))])
    (let ([selected
           (for*/fold ([picked 0])
                      ([r (in-range 1 (rows g))]
                       [c (in-range (cols g))])
             (if (and (= picked 0) (= (at g r c) 9))
                 (let ([left (if (> c 0) (at g r (- c 1)) 0)]
                       [right (if (< c (- (cols g) 1)) (at g r (+ c 1)) 0)])
                   (if (not (= left 0))
                       left
                       (if (not (= right 0)) right picked)))
                 picked))])
      (for*/fold ([out base])
                 ([r (in-range 1 (rows g))]
                  [c (in-range (cols g))]
                  [target-c (in-range (cols g))])
        (if (and (not (= selected 0)) (= (at g r c) selected))
            (set-cell out r target-c selected)
            out)))))