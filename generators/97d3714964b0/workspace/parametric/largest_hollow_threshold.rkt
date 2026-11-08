(rule!
  (let* ((objs (objects g 0))
         (hollow?
           (lambda (obj)
             (let* ((bb (obj-bbox obj))
                    (r0 (first bb))
                    (c0 (second bb))
                    (r1 (third bb))
                    (c1 (fourth bb))
                    (cells (obj-cells obj))
                    (interior (if (and (< (+ r0 1) r1) (< (+ c0 1) c1))
                                  (positions-in-rect (+ r0 1) (+ c0 1) (- r1 1) (- c1 1))
                                  (list))))
               (any?
                 (lambda (p)
                   (and (= (cell-at g (fst p) (snd p)) 0)
                        (not (member p cells))))
                 interior))))
         (bbox-area
           (lambda (obj)
             (let ((bb (obj-bbox obj)))
               (* (+ 1 (- (third bb) (first bb)))
                  (+ 1 (- (fourth bb) (second bb)))))))
         (hollows
           (filter
             (lambda (obj)
               (and (= (obj-color obj) 7) (hollow? obj)))
             objs))
         (threshold
           (if (empty? hollows)
               0
               (apply max (map bbox-area hollows)))))
    (foldl
      (lambda (obj acc)
        (if (= (obj-color obj) 7)
            (let ((cells (obj-cells obj)))
              (if (hollow? obj)
                  (paint-cells acc cells 4)
                  (if (>= (bbox-area obj) threshold)
                      (paint-cells acc cells 2)
                      acc)))
            acc))
      g
      objs)))
