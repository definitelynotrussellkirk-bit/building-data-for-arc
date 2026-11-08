(rule!
 ;; Reflect every red(2) cell across the green(3) shape's bbox-center axes
 ;; (up-down, left-right, and both); empty cells whose mirror-source is red
 ;; are painted red.
 (lambda (g)
  (let* ((bb (bbox-of-cells (find-color g 3)))
         (sr (+ (first bb) (third bb)))
         (sc (+ (second bb) (fourth bb))))
    (cellmap g (r c v)
      (if (!= 0 v) v
        (if (or (= 2 (safe-at g (- sr r) c 0))
                (= 2 (safe-at g r (- sc c) 0))
                (= 2 (safe-at g (- sr r) (- sc c) 0)))
          2 0))))))
