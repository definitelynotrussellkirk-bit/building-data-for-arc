(rule!
 ;; Proposed vertical reflection variant around the green(3) bbox center.
 ;; Preserve nonzero cells; paint an empty cell red when its selected mirror is red.
 (lambda (g)
  (let* ((bb (bbox-of-cells (find-color g 3)))
         (sr (+ (first bb) (third bb)))
         (sc (+ (second bb) (fourth bb))))
    (cellmap g (r c v)
      (if (!= 0 v) v
        (if (= 2 (safe-at g r (- sc c) 0))
          2 0))))))
