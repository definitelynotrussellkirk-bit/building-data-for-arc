(rule!
  (let* ((cells (filter-cells g (lambda (r c v) (not (= v 0)))))
         (color (at g (first (first cells)) (second (first cells))))
         (bb (bbox-of-cells cells))
         (border (append
                   (for/list ([c (in-range (second bb) (+ (fourth bb) 1))]) (list (first bb) c))
                   (for/list ([c (in-range (second bb) (+ (fourth bb) 1))]) (list (third bb) c))
                   (for/list ([r (in-range (+ (first bb) 1) (third bb))]) (list r (second bb)))
                   (for/list ([r (in-range (+ (first bb) 1) (third bb))]) (list r (fourth bb))))))
    (paint-cells (empty-grid (rows g) (cols g) 0) border color)))