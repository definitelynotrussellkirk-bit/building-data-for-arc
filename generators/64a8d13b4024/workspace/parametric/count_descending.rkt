(rule!
  (let* ((colors (list 1 2 3))
         (totals (map (lambda (color) (length (find-color g color))) colors))
         (bars (map (lambda (color hgt) (list color hgt)) colors totals))
         (ordered
           (sort bars
             (lambda (a b)
               (if (= (second a) (second b))
                   (< (first a) (first b))
                   (> (second a) (second b)))))))
    (grid-from-fn 6 3
      (lambda (r c)
        (let* ((bar (list-ref ordered c))
               (color (first bar))
               (hgt (second bar)))
          (if (>= r (- 6 hgt)) color 0))))))
