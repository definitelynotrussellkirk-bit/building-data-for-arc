(rule!
  (cellmap g (r c v)
    (if (zero? v)
        0
        (let* ((start (last (filter (lambda (cc)
                                      (or (zero? cc)
                                          (!= (at g r (- cc 1)) v)))
                                    (range 0 (+ c 1)))))
               (end (find-first (lambda (cc)
                                  (or (= cc (- w 1))
                                      (!= (at g r (+ cc 1)) v)))
                                (range c w)))
               (mid (quotient (+ start end) 2)))
          (if (= c mid) v 0)))))