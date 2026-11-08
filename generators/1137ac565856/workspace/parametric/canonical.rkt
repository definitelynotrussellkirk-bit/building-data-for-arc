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
                        (area-a (* (+ 1 (- (third ba) (first ba))) (+ 1 (- (fourth ba) (second ba)))))
                        (area-b (* (+ 1 (- (third bb) (first bb))) (+ 1 (- (fourth bb) (second bb))))))
                   (< area-a area-b))))))
         (bb (obj-bbox chosen))
         (out-h (+ 1 (- (third bb) (first bb))))
         (out-w (+ 1 (- (fourth bb) (second bb)))))
    (empty-grid out-h out-w (obj-color chosen))))