(rule!
 ;; Find every yellow five-cell orthogonal plus, even inside larger shapes.
 ;; Diagonal cells and extensions beyond the four arms do not disqualify it.
 ;; All detections use the original grid, so overlapping crosses are simultaneous.
 ;; Recolor the union of their center/arm cells cyan; leave all other cells alone.
 (lambda (g)
  (let ()
   (define selection-mode 0)
   (define detection-mode 0)
   (define painting-mode 0)
   (define use-eight #f)
   (define plus '((0 0) (-1 0) (1 0) (0 -1) (0 1)))
   (define diagonals '((0 0) (-1 -1) (-1 1) (1 -1) (1 1)))
   (define stencil (if (= detection-mode 3) diagonals plus))
   (define comps (filter (lambda (o) (= (obj-color o) 4)) (if use-eight (objects-8 g 2) (objects g 2))))
   (define centers
     (for*/list ((r (range 1 (- h 1))) (c (range 1 (- w 1)))
       #:when (and
          (for/and ((d stencil)) (= (at g (+ r (first d)) (+ c (second d))) 4))
          (or (not (= detection-mode 1))
              (for/and ((d (rest diagonals))) (not (= (at g (+ r (first d)) (+ c (second d))) 4))))
          (or (not (= detection-mode 2))
              (for/or ((o comps)) (and (= (obj-size o) 5) (member (list r c) (obj-cells o)))))))
       (list r c)))
   (define bearing (filter (lambda (o) (for/or ((p centers)) (member p (obj-cells o)))) comps))
   (define (cross-count o) (length (filter (lambda (p) (member p (obj-cells o))) centers)))
   (define chosen
     (cond ((and (= selection-mode 7) (not (null? comps))) (list (pick-max comps obj-size)))
           ((null? bearing) '())
           ((= selection-mode 0) bearing)
           ((= selection-mode 1) (list (pick-max bearing obj-size)))
           ((= selection-mode 2) (list (pick-min bearing obj-size)))
           ((= selection-mode 3) (list (first bearing)))
           ((= selection-mode 4) (list (last bearing)))
           ((= selection-mode 5) (list (pick-max bearing (lambda (o) (* (obj-h o) (obj-w o))))))
           ((= selection-mode 6) (list (pick-max bearing cross-count)))
           ((= selection-mode 8) (list (pick-max bearing obj-w)))
           ((= selection-mode 9) (list (pick-max bearing obj-h)))
           (else '())))
   (define active (filter (lambda (p) (for/or ((o chosen)) (member p (obj-cells o)))) centers))
   (define paint-offsets (cond ((= painting-mode 1) '((0 0)))
                               ((= painting-mode 2) '((0 0) (0 -1) (0 1)))
                               ((= painting-mode 3) '((0 0) (-1 0) (1 0)))
                               (else stencil)))
   (for/fold ((out g)) ((p active))
     (if (and (= painting-mode 4)
              (not (for/and ((d plus)) (= (at out (+ (first p) (first d)) (+ (second p) (second d))) 4))))
       out
       (recolor-cells out (map (lambda (d) (list (+ (first p) (first d)) (+ (second p) (second d)))) paint-offsets) 8))))))
