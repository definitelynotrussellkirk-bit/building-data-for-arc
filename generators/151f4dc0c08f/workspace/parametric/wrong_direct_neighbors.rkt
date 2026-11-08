(rule!
  (let ((dummy 0))
    (define (points-of grid color)
      (sort (find-color grid color) cell<))
    (define (color-groups grid)
      (map (lambda (color) (list color (points-of grid color)))
           (grid-colors grid 0)))
    (define (aligned? p q)
      (or (= (first p) (first q))
          (= (second p) (second q))
          (= (abs (- (first p) (first q)))
             (abs (- (second p) (second q))))))
    (define groups (color-groups g))
    (define points (map (lambda (entry) (first (second entry))) groups))
    (define n (length groups))
    (define anchor-neighbors
      (filter (lambda (j) (aligned? (first points) (list-ref points j)))
              (range 0 n)))
    (grid-from-fn n n
      (lambda (i j)
        (if (and (member? i anchor-neighbors)
                 (member? j anchor-neighbors))
            8
            0)))))
