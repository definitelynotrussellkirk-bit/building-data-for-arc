(rule!
  (let* ((marker (first (find-color g 2)))
         (mr (fst marker))
         (mc (snd marker))
         (candidates
           (filter
             (lambda (obj)
               (let* ((bb (obj-bbox obj))
                      (r0 (first bb))
                      (c0 (second bb))
                      (r1 (third bb))
                      (c1 (fourth bb))
                      (color (obj-color obj)))
                 (and (not (= color 2))
                      (> mr r0) (< mr r1)
                      (> mc c0) (< mc c1)
                      (all?
                        (lambda (p)
                          (let ((r (fst p)) (c (snd p)))
                            (= (cell-at g r c) color)))
                        (filter
                          (lambda (p)
                            (let ((r (fst p)) (c (snd p)))
                              (or (= r r0) (= r r1) (= c c0) (= c c1))))
                          (positions-in-rect r0 c0 r1 c1))))))
             (objects g 0)))
         (chosen
           (first
             (sort candidates
               (lambda (a b)
                 (let* ((ba (obj-bbox a))
                        (bb (obj-bbox b))
                        (area-a (* (+ 1 (- (third ba) (first ba)))
                                   (+ 1 (- (fourth ba) (second ba)))))
                        (area-b (* (+ 1 (- (third bb) (first bb)))
                                   (+ 1 (- (fourth bb) (second bb))))))
                   (< area-a area-b))))))
         (bb (obj-bbox chosen))
         (out-w (+ 1 (- (fourth bb) (second bb))))
         (selector (quotient (- out-w 1) 2))
         (payloads
           (sort
             (filter (lambda (obj) (= (obj-color obj) 9)) (objects g 0))
             (lambda (a b)
               (if (= (obj-r1 a) (obj-r1 b))
                   (< (obj-c1 a) (obj-c1 b))
                   (< (obj-r1 a) (obj-r1 b))))))
         (target (list-ref payloads (- selector 1))))
    (paint-cells (empty-grid (rows g) (cols g) 0)
                 (obj-cells target)
                 8)))
