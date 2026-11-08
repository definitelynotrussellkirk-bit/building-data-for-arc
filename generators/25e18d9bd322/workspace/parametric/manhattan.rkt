(rule!
  (let* ((marker (first (find-color g 9)))
         (objs (objects (set-cell g (first marker) (second marker) 0) 0))
         (best (first (sort objs
                            (lambda (a b)
                              (let ((da (apply min (map (lambda (p) (pos-manhattan p marker)) (obj-cells a))))
                                    (db (apply min (map (lambda (p) (pos-manhattan p marker)) (obj-cells b)))))
                                (cond [(not (= da db)) (< da db)]
                                      [(not (= (obj-r1 a) (obj-r1 b))) (< (obj-r1 a) (obj-r1 b))]
                                      [else (< (obj-c1 a) (obj-c1 b))]))))))
         (cells (normalize-cells (obj-cells best)))
         (bb (bbox-of-cells cells)))
    (paint-cells (empty-grid (+ 1 (third bb)) (+ 1 (fourth bb)) 0) cells (obj-color best))))