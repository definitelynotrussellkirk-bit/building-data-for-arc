(rule!
  (let ((dummy 0))
    (let ((legend (filter (lambda (v) (not (= v 0))) (first g))))
      (for/fold ((out g)) ((obj (in-list (objects g 0))))
        (let ((bb (obj-bbox obj)))
          (if (and (= (obj-size obj) 3)
                   (= (- (third bb) (first bb)) 1)
                   (= (- (fourth bb) (second bb)) 1))
              (let* ((missing
                      (first
                       (filter (lambda (p) (not (member? p (obj-cells obj))))
                               (positions-in-rect (first bb) (second bb)
                                                  (third bb) (fourth bb)))))
                     (orientation
                      (+ (* 2 (- (first missing) (first bb)))
                         (- (second missing) (second bb))))
                     (fill-color (list-ref legend orientation)))
                (paint-cells out (list missing) fill-color))
              out))))))
