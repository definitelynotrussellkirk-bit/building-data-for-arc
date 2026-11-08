(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (bg (mode g))
         (objs (objects g bg))
         (bounded (lambda (cells)
                    (filter (lambda (p) (in-bounds? (first p) (second p) h w)) cells)))
         (rects
          (for/list ((o objs)
                     #:when (> (length (obj-cells o)) 1))
            (list (obj-color o) (obj-bbox o))))
         (dots
          (for/list ((o objs)
                     #:when (= (length (obj-cells o)) 1))
            (list (obj-color o) (first (obj-cells o))))))
    (for/fold ((out g)) ((dot dots))
      (let* ((color (first dot))
             (cell (second dot))
             (dr (first cell))
             (dc (second cell))
             (best
              (for/fold ((best #f)) ((entry rects))
                (let* ((rect (second entry))
                       (r1 (first rect)) (c1 (second rect))
                       (r2 (third rect)) (c2 (fourth rect))
                       (candidate
                        (cond
                          ((and (< dc c1) (<= r1 dr) (<= dr r2))
                           (list (- c1 dc 1) 'right (- c1 1)))
                          ((and (> dc c2) (<= r1 dr) (<= dr r2))
                           (list (- dc c2 1) 'left (+ c2 1)))
                          ((and (< dr r1) (<= c1 dc) (<= dc c2))
                           (list (- r1 dr 1) 'down (- r1 1)))
                          ((and (> dr r2) (<= c1 dc) (<= dc c2))
                           (list (- dr r2 1) 'up (+ r2 1)))
                          (else #f))))
                  (cond
                    ((not candidate) best)
                    ((not best) candidate)
                    ((< (first candidate) (first best)) candidate)
                    (else best))))))
        (cond
          ((not best) out)
          (else
           (let* ((direction (second best))
                  (cap-coord (third best))
                  (g5 (paint-cells
                       (erase-cells out (list (list dr dc)) bg)
                       (bounded (map (lambda (delta)
                                       (list (+ dr (first delta)) (+ dc (second delta))))
                                     cardinal-deltas))
                       color)))
             (cond
               ((eq? direction 'right)
                (paint-cells
                 g5
                 (bounded (append (positions-in-rect dr (+ dc 2) dr cap-coord)
                                  (list (list (- dr 1) cap-coord) (list (+ dr 1) cap-coord))))
                 color))
               ((eq? direction 'left)
                (paint-cells
                 g5
                 (bounded (append (positions-in-rect dr cap-coord dr (- dc 2))
                                  (list (list (- dr 1) cap-coord) (list (+ dr 1) cap-coord))))
                 color))
               ((eq? direction 'down)
                (paint-cells
                 g5
                 (bounded (append (positions-in-rect (+ dr 2) dc cap-coord dc)
                                  (list (list cap-coord (- dc 1)) (list cap-coord (+ dc 1)))))
                 color))
               ((eq? direction 'up)
                (paint-cells
                 g5
                 (bounded (append (positions-in-rect cap-coord dc (- dr 2) dc)
                                  (list (list cap-coord (- dc 1)) (list cap-coord (+ dc 1)))))
                 color))
               (else g5))))))))))
