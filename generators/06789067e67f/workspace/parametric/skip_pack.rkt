(rule!
  (let ((ordered
         (sort (objects g 0)
               (lambda (a b)
                 (cond [(not (= (obj-c1 a) (obj-c1 b)))
                        (< (obj-c1 a) (obj-c1 b))]
                       [else (< (obj-r1 a) (obj-r1 b))])))))
    (define (paint-rank acc cells rank)
      (reduce (lambda (a p) (set-cell a (first p) (second p) rank))
              acc cells))
    (let loop ([remaining ordered] [rank 1] [acc g])
      (if (empty? remaining)
          acc
          (loop (rest remaining)
                (+ rank 1)
                (paint-rank acc (obj-cells (first remaining)) rank))))))
