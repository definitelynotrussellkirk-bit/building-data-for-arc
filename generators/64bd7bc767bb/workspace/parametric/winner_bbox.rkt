(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (counts (make-hash))
         (dummy
          (for* ((r (in-range h)) (c (in-range w)))
            (let ((v (at g r c)))
              (when (and (>= v 1) (<= v 4))
                (hash-set! counts v (+ 1 (hash-ref counts v 0))))))))
    (let* ((winner
            (for/fold ((best 1)) ((color (in-range 2 5)))
              (if (> (hash-ref counts color 0) (hash-ref counts best 0))
                  color
                  best)))
           (min-r
            (for*/fold ((best h)) ((r (in-range h)) (c (in-range w)))
              (if (= (at g r c) winner) (min best r) best)))
           (max-r
            (for*/fold ((best -1)) ((r (in-range h)) (c (in-range w)))
              (if (= (at g r c) winner) (max best r) best)))
           (min-c
            (for*/fold ((best w)) ((r (in-range h)) (c (in-range w)))
              (if (= (at g r c) winner) (min best c) best)))
           (max-c
            (for*/fold ((best -1)) ((r (in-range h)) (c (in-range w)))
              (if (= (at g r c) winner) (max best c) best)))
           (top? (> (- max-c min-c) (- max-r min-r))))
      (cellmap g (r c v)
        (let ((color (+ c 1))
              (cnt (hash-ref counts (+ c 1) 0)))
          (if (and (<= color 4)
                   (if top? (< r cnt) (>= r (- h cnt))))
              color
              0)))))))