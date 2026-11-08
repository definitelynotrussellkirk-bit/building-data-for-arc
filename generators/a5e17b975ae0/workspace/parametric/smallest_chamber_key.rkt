(rule!
  (let ((dummy 0))
    (define dirs4 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))
    (define seeds
      (filter
        (lambda (p)
          (let ((v (at g (first p) (second p))))
            (and (not (= v 0)) (not (member? v (list 5 9))))))
        (grid-positions g)))
    (define (seed-region seed)
      (let ((color (at g (first seed) (second seed))))
        (let bfs ((queue (list seed)) (seen (list seed)))
          (if (empty? queue)
              seen
              (let* ((cur (first queue))
                     (nbrs
                       (filter
                         (lambda (p)
                           (and
                             (in-bounds? (first p) (second p) (rows g) (cols g))
                             (not (member? p seen))
                             (let ((v (at g (first p) (second p))))
                               (and
                                 (not (member? v (list 5 9)))
                                 (or (= v 0) (= v color))))))
                         (map
                           (lambda (d)
                             (list (+ (first cur) (first d))
                                   (+ (second cur) (second d))))
                           dirs4))))
                (bfs (append (rest queue) nbrs) (append seen nbrs)))))))
    (define winner
      (pick-min seeds (lambda (seed) (length (seed-region seed)))))
    (define winner-color (at g (first winner) (second winner)))
    (for/fold ((out g)) ((seed (in-list seeds)))
      (paint-cells out (seed-region seed) winner-color))))
