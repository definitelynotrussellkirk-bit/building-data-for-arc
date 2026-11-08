(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (all-objs (objects g 0))
         ;; Rectangles: multi-cell components
         (rects
          (for/list ((o all-objs)
                     #:when (> (length (obj-cells o)) 1))
            (let ((bb (obj-bbox o)))
              (list (obj-color o) (first bb) (second bb) (third bb) (fourth bb)))))
         ;; Singles: single-cell components, count by color
         (single-colors
          (for/list ((o all-objs)
                     #:when (= (length (obj-cells o)) 1))
            (obj-color o)))
         (color-counts
          (let loop ((cs single-colors) (acc (hash)))
            (cond
              ((null? cs) acc)
              (else
               (let ((c (car cs)))
                 (loop (cdr cs) (hash-set acc c (+ 1 (hash-ref acc c 0))))))))))
    ;; Start by removing all scattered pixels (but keep rect cells)
    (let* ((out1
            (for*/fold ((out g)) ((r (range 0 h)) (c (range 0 w)))
              (let ((v (cell-at g r c)))
                (cond
                  ((= v 0) out)
                  (else
                   ;; Check if this cell is inside any rect bbox of the same color
                   (let ((is-rect
                          (for/or ((rect rects))
                            (and (= (first rect) v)
                                 (>= r (second rect))
                                 (<= r (fourth rect))
                                 (>= c (third rect))
                                 (<= c (fifth rect))))))
                     (if is-rect out (set-cell out r c 0))))))))
           ;; Fill rectangles with checkerboard based on color counts
           (out2
            (for/fold ((out out1)) ((color (hash-keys color-counts)))
              (let ((count (hash-ref color-counts color)))
                ;; Find matching rect
                (let loop ((rs rects))
                  (cond
                    ((null? rs) out)
                    (else
                     (let* ((rect (car rs))
                            (r1 (second rect)) (c1 (third rect))
                            (r2 (fourth rect)) (c2 (fifth rect))
                            (rh (+ 1 (- r2 r1)))
                            (rw (+ 1 (- c2 c1)))
                            (ih (- rh 2))
                            (iw (- rw 2))
                            (n (* ih iw))
                            (half (quotient n 2)))
                       (cond
                         ((and (> ih 0) (> iw 0) (= half count))
                          (for*/fold ((gg out)) ((i (range 0 ih)) (j (range 0 iw))
                                                  #:when (= (modulo (+ i j) 2) 1))
                            (set-cell gg (+ r1 1 i) (+ c1 1 j) color)))
                         (else (loop (cdr rs))))))))))))
      out2))))
