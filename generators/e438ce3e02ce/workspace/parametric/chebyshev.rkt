(rule!
  (let ((seeds (filter (lambda (cell) (not (= (third cell) 0))) (grid-cells g))))
    (define (dist cell r c)
      (max (abs (- r (first cell))) (abs (- c (second cell)))))
    (define (fill-value r c)
      (let* ((dmin (apply min (map (lambda (cell) (dist cell r c)) seeds)))
             (colors (remove-duplicates
                       (map third (filter (lambda (cell) (= (dist cell r c) dmin)) seeds)))))
        (if (= (length colors) 1) (first colors) 8)))
    (grid-from-fn (rows g) (cols g)
      (lambda (r c)
        (if (= (at g r c) 0) (fill-value r c) (at g r c))))))
