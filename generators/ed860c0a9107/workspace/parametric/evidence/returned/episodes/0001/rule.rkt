(rule!
  (let* ([bg (at g 0 0)]
         [boxes (objects-multicolor g bg)]
         [bb (obj-bbox (first boxes))]
         [out-h (+ 1 (- (third bb) (first bb)))]
         [out-w (+ 1 (- (fourth bb) (second bb)))])
    ;; alt: normalize every box to its bbox, then left-fold a transparent overlay.
    (define (local-at obj r c)
      (let* ([obb (obj-bbox obj)]
             [gr (+ (first obb) r)]
             [gc (+ (second obb) c)])
        (and (in-bounds? gr gc h w) (at g gr gc))))
    (define (visible? v)
      (and v (!= v 0) (!= v bg)))
    (build-grid out-h out-w (r c)
      (let ([hit (find-first (lambda (obj) (visible? (local-at obj r c))) boxes)])
        (if hit (local-at hit r c) 0)))))