(rule!
 ;; Protected counterfactual: skip square-to-center reduction, choose the raw
 ;; pixel-majority color, and frame its original-pixel bounding box.
 (let ((dummy 0))
   (define colors
     (filter (lambda (color) (not (= color 0))) (grid-colors g)))
   (define (frequency-desc< a b)
     (let ([ca (length (find-color g a))]
           [cb (length (find-color g b))])
       (if (= ca cb) (< a b) (> ca cb))))
   (define target-color (first (sort colors frequency-desc<)))
   (define bb (bbox-of-cells (find-color g target-color)))
   (define r1 (first bb))
   (define c1 (second bb))
   (define r2 (third bb))
   (define c2 (fourth bb))
   (for*/fold ([out g])
              ([r (in-range r1 (+ r2 1))]
               [c (in-range c1 (+ c2 1))])
     (if (and (or (= r r1) (= r r2) (= c c1) (= c c2))
              (= (at out r c) 0))
         (set-cell out r c 9)
         out))))
