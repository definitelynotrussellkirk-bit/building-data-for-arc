(rule!
 ;; A monochrome hollow cross determines a center and common arm length.
 ;; Extend its four arms into clockwise interleaved contours, leaving one
 ;; background cell between paths. Radius one first expands to radius two.
 ;; Each contour group runs 2+4*n, bends inward by k-2, then extends by k.
 ;; Move outside the canvas normally and clip only painting: later segments
 ;; can re-enter. The reflected setting reverses every turn, not the input.
 (lambda (g)
   (let ()
     (define height (rows g))
     (define width (cols g))
     (define cells (filter (lambda (p) (> (at g (first p) (second p)) 0)) (grid-positions g)))
     (define box (bbox-of-cells cells))
     (define center-r (/ (+ (first box) (third box)) 2))
     (define center-c (/ (+ (second box) (fourth box)) 2))
     (define measured-radius (/ (- (third box) (first box)) 2))
     (define radius (max 2 measured-radius))
     (define ink (at g (first (first cells)) (second (first cells))))
     (define handedness -1)
     (define directions (list (list -1 0) (list 0 1) (list 1 0) (list 0 -1)))
     (define (segment state direction distance)
       (let* ((r (second state)) (c (third state))
              (delta (list-ref directions (modulo direction 4)))
              (dr (first delta)) (dc (second delta))
              (points (for/list ((step (range 1 (+ distance 1)))
                         #:when (in-bounds? (+ r (* dr step)) (+ c (* dc step)) height width))
                        (list (+ r (* dr step)) (+ c (* dc step))))))
         (list (recolor-cells (first state) points ink)
               (+ r (* dr distance)) (+ c (* dc distance)))))
     (for/fold ((out (empty-grid height width 0))) ((start (range 0 4)))
       (let loop ((state (segment (list out center-r center-c) start radius))
                  (direction (+ start handedness)) (layer 0))
         (if (>= layer (+ height width))
             (first state)
             (let* ((long (segment state direction (+ 2 (* 4 layer))))
                    (inward (segment long (+ direction handedness) (- radius 2)))
                    (tip (segment inward direction radius)))
               (loop tip (+ direction handedness) (+ layer 1)))))))))
