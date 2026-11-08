(rule!
 ;; Stage A: canonical square-to-center reduction.
 ;; Stage B: on that intermediate, select the unique most frequent center
 ;; color and frame the bounding box of those centers with color 9.
 (let ((dummy 0))
   (define (center-grid grid)
     (for/fold ([out (empty-grid (rows grid) (cols grid) 0)])
               ([obj (in-list (objects grid 0))])
       (let* ([bb (obj-bbox obj)]
              [h (+ 1 (- (third bb) (first bb)))]
              [w (+ 1 (- (fourth bb) (second bb)))])
         (if (and (= h w) (= (modulo h 2) 1))
             (set-cell out
                       (+ (first bb) (quotient h 2))
                       (+ (second bb) (quotient w 2))
                       (obj-color obj))
             out))))
   (define stage-a (center-grid g))
   (define colors
     (filter (lambda (color) (not (= color 0))) (grid-colors stage-a)))
   (define (frequency-desc< a b)
     (let ([ca (length (find-color stage-a a))]
           [cb (length (find-color stage-a b))])
       (if (= ca cb) (< a b) (> ca cb))))
   (define target-color (first (sort colors frequency-desc<)))
   (define bb (bbox-of-cells (find-color stage-a target-color)))
   (define r1 (first bb))
   (define c1 (second bb))
   (define r2 (third bb))
   (define c2 (fourth bb))
   (for*/fold ([out stage-a])
              ([r (in-range r1 (+ r2 1))]
               [c (in-range c1 (+ c2 1))])
     (if (and (or (= r r1) (= r r2) (= c c1) (= c c2))
              (= (at out r c) 0))
         (set-cell out r c 9)
         out))))
