(rule! (lambda (g)
	  (let* ((h (rows g))
	         (w (cols g))
	         (bg (mode g))
	         (objs (objects g bg))
	         (bounded (lambda (cells)
	                    (filter (lambda (p) (in-bounds? (first p) (second p) h w)) cells)))
	         ;; Build a hash from color to rect bbox, and list of dots
         (rects
          (let loop ((os objs) (acc (hash)))
            (cond
              ((null? os) acc)
              (else
               (let* ((o (car os))
                      (cells (obj-cells o))
                      (color (obj-color o)))
                 (cond
                   ((> (length cells) 1)
                    (let* ((bb (obj-bbox o))
                           (r1 (first bb)) (c1 (second bb))
                           (r2 (third bb)) (c2 (fourth bb)))
                      (loop (cdr os) (hash-set acc color (list r1 c1 r2 c2)))))
                   (else (loop (cdr os) acc))))))))
         (dots
          (for/list ((o objs)
                     #:when (= (length (obj-cells o)) 1))
            (list (obj-color o) (first (obj-cells o))))))
    (for/fold ((out g)) ((dot dots))
      (let* ((color (first dot))
             (cell (second dot))
             (dr (first cell))
             (dc (second cell)))
        (cond
          ((not (hash-has-key? rects color)) out)
          (else
           (let* ((rect (hash-ref rects color))
                  (r1 (first rect)) (c1 (second rect))
                  (r2 (third rect)) (c2 (fourth rect))
                  ;; Determine direction
                  (dir-info
                   (cond
                     ((and (< dc c1) (<= r1 dr) (<= dr r2))
                      (list 'right (- c1 1)))
                     ((and (> dc c2) (<= r1 dr) (<= dr r2))
                      (list 'left (+ c2 1)))
                     ((and (< dr r1) (<= c1 dc) (<= dc c2))
                      (list 'down (- r1 1)))
                     ((and (> dr r2) (<= c1 dc) (<= dc c2))
                      (list 'up (+ r2 1)))
                     (else #f))))
             (cond
               ((not dir-info) out)
               (else
	                (let* ((direction (first dir-info))
	                       (cap-coord (second dir-info))
	                       ;; Draw flower: erase center, 4 petals
	                       (g5 (paint-cells
	                            (erase-cells out (list (list dr dc)) bg)
	                            (bounded (map (lambda (delta)
	                                            (list (+ dr (first delta)) (+ dc (second delta))))
	                                          cardinal-deltas))
	                            color)))
	                  ;; Draw stem + cap
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
                    (else g5)))))))))))))