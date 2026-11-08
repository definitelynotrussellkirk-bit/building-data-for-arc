(rule!
  (let* ([down
          (fold-cells g g
            (lambda (out r c v)
              (if (or (= v 0) (= v 5))
                  out
                  (let smear ([rr (+ r 1)] [acc out])
                    (if (and (< rr (rows g)) (= (at g rr c) 0))
                        (smear (+ rr 1) (set-cell acc rr c v))
                        acc)))))])
    (fold-cells g down
      (lambda (out r c v)
        (if (or (= v 0) (= v 5))
            out
            (let endpoint ([rr (+ r 1)] [last r])
              (if (and (< rr (rows g)) (= (at g rr c) 0))
                  (endpoint (+ rr 1) rr)
                  (if (= last r)
                      out
                      (let turn ([cc (+ c 1)] [acc out])
                        (if (and (< cc (cols g)) (= (at down last cc) 0))
                            (turn (+ cc 1) (set-cell acc last cc v))
                            acc))))))))))
