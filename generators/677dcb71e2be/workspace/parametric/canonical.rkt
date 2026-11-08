(rule!
  ;; Sort nonzero components by occupied-cell count, largest first.  The color
  ;; tie-break is deterministic but unreachable in the generator curriculum.
  (let* ((objs (sort (objects g 0)
                     (lambda (a b)
                       (cond [(not (= (obj-size a) (obj-size b))) (> (obj-size a) (obj-size b))]
                             [else (< (obj-color a) (obj-color b))]))))
         (total (+ (apply + (map obj-size objs)) (max 0 (- (length objs) 1)))))
    ;; Pack one same-color bar per component, separated by a single zero cell.
    (let pack ([remaining objs] [left 0] [out (empty-grid 1 total 0)])
      (if (empty? remaining)
          out
          (let* ((obj (first remaining))
                 (next (for/fold ([acc out]) ([c (in-range left (+ left (obj-size obj)))])
                         (set-cell acc 0 c (obj-color obj)))))
            (pack (rest remaining) (+ left (obj-size obj) 1) next))))))