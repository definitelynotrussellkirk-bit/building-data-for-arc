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
                          (positions-in-rect r0 c0 r1 c1))))))
             (objects g 0)))
         (seeded
           (filter
             (lambda (obj)
               (let* ((bb (obj-bbox obj))
                      (r0 (first bb))
                      (c0 (second bb))
                      (r1 (third bb))
                      (c1 (fourth bb)))
                 (any?
                   (lambda (p) (= (cell-at g (fst p) (snd p)) 2))
                   (positions-in-rect (+ r0 1) (+ c0 1) (- r1 1) (- c1 1)))))
             frames))
         (deepest
           (filter
             (lambda (obj)
               (let* ((bb (obj-bbox obj))
                      (r0 (first bb))
                      (c0 (second bb))
                      (r1 (third bb))
                      (c1 (fourth bb)))
                 (not
                   (any?
                     (lambda (other)
                       (let* ((ob (obj-bbox other))
                              (or0 (first ob))
                              (oc0 (second ob))
                              (or1 (third ob))
                              (oc1 (fourth ob)))
                         (and (not (and (= r0 or0) (= c0 oc0) (= r1 or1) (= c1 oc1)))
                              (> or0 r0) (< or1 r1)
                              (> oc0 c0) (< oc1 c1))))
                     seeded))))
             seeded)))
    (grid-from-fn h w
      (lambda (r c)
        (if (any?
              (lambda (obj)
                (let ((bb (obj-bbox obj)))
                  (and (> r (first bb)) (< r (third bb))
                       (> c (second bb)) (< c (fourth bb)))))
              deepest)
            3
            (cell-at g r c))))))