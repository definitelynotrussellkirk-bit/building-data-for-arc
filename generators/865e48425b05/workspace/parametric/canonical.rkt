(rule!
  (let* ((palette (filter (lambda (v) (not (= v 0))) (row g 0)))
         (bb (bbox-of-cells (find-color g 1)))
         (mask (grid-from-fn (+ (- (third bb) (first bb)) 1)
                             (+ (- (fourth bb) (second bb)) 1)
                 (lambda (r c)
                   (if (= (at g (+ (first bb) r) (+ (second bb) c)) 1) 1 0)))))
    (define copies
      (map (lambda (color)
             (grid-from-fn (rows mask) (cols mask)
               (lambda (r c) (if (= (at mask r c) 1) color 0))))
           palette))
    (define out-h (rows mask))
    (define out-w (+ (apply + (map cols copies)) (max 0 (- (length copies) 1))))
    (let pack ([remaining copies] [left 0] [out (empty-grid out-h out-w 0)])
      (if (empty? remaining)
          out
          (let* ((p (first remaining))
                 (next (for*/fold ([acc out])
                                   ([r (in-range (rows p))]
                                    [c (in-range (cols p))])
                         (let ((v (at p r c)))
                           (if (not (= v 0)) (set-cell acc r (+ left c) v) acc)))))
            (pack (rest remaining) (+ left (cols p) 1) next))))))