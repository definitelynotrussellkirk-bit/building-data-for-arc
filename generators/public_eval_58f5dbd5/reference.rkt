(rule!
 ;; Find the large solid monochrome plates on the modal background.
 ;; For each plate, recover the small same-color stencil outside the plate.
 ;; Normalize that stencil and punch its occupied cells out of the plate's
 ;; one-cell-bordered interior. Keep the plate arrangement; crop with one
 ;; background cell of margin. Unmatched small colored stencils are distractors.
 (lambda (g)
  (let ()
   (define bg (mode g -1))
   (define plates (filter (lambda (o) (and (>= (obj-h o) 4) (>= (obj-w o) 4) (solid-rect? o))) (objects g bg)))
   (define painted
    (for/fold ((out g)) ((plate plates))
     (let ()
      (define color (obj-color plate))
      (define raw (filter (lambda (p) (not (member p (obj-cells plate)))) (find-color g color)))
      (define mask (normalize-cells raw))
      (for*/fold ((acc out)) ((rr (range 0 (- (obj-h plate) 2))) (cc (range 0 (- (obj-w plate) 2))))
       (set-cell acc (+ (obj-r1 plate) 1 rr) (+ (obj-c1 plate) 1 cc)
        (if (member (list rr cc) mask) bg color))))))
   (define bounds (bbox-of-cells (apply append (map obj-cells plates))))
   (subgrid painted (- (first bounds) 1) (- (second bounds) 1)
                    (+ (third bounds) 1) (+ (fourth bounds) 1)))))
