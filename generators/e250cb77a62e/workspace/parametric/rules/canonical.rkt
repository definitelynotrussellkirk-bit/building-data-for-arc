(rule!
  (let* ((frames
           (filter
             (lambda (obj)
               (let* ((bb (obj-bbox obj))
                      (r0 (first bb))
                      (c0 (second bb))
                      (r1 (third bb))
                      (c1 (fourth bb)))
                 (and (= (obj-color obj) 1)
                      (all?
                        (lambda (p)
                          (let ((r (fst p)) (c (snd p)))
                            (= (cell-at g r c) 1)))
                        (filter
                          (lambda (p)
                            (let ((r (fst p)) (c (snd p)))
                              (or (= r r0) (= r r1) (= c c0) (= c c1))))
                          (positions-in-rect r0 c0 r1 c1)))
                      (any?
                        (lambda (p) (= (cell-at g (fst p) (snd p)) 4))
                        (positions-in-rect (+ r0 1) (+ c0 1) (- r1 1) (- c1 1))))))
             (objects g 0)))
         (frame (first frames))
         (bb (obj-bbox frame))
         (r0 (first bb))
         (c0 (second bb))
         (r1 (third bb))
         (c1 (fourth bb))
         (pattern
           (map
             (lambda (p) (list (- (fst p) (+ r0 1)) (- (snd p) (+ c0 1))))
             (filter
               (lambda (p) (= (cell-at g (fst p) (snd p)) 4))
               (positions-in-rect (+ r0 1) (+ c0 1) (- r1 1) (- c1 1)))))
         (targets
           (flatmap
             (lambda (seed)
               (map
                 (lambda (p) (list (+ (fst seed) (fst p)) (+ (snd seed) (snd p))))
                 pattern))
             (find-color g 7))))
    (paint-cells g targets 8)))