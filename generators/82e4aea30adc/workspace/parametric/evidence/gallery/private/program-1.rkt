(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g)))
    ;; Treat each non-background component as a hollow rectangular frame.
    (let* ((objs (objects g 0)))
      (reduce
        (lambda (grid obj)
          (let* ((bb (obj-bbox obj))
                 ;; Move each bounding-box edge inward to address the interior.
                 (r1 (+ 1 (nth bb 0)))
                 (c1 (+ 1 (nth bb 1)))
                 (r2 (- (nth bb 2) 1))
                 (c2 (- (nth bb 3) 1))
                 (ih (+ 1 (- r2 r1)))
                 (iw (+ 1 (- c2 c1)))
                 ;; Interiors of area at most two are gray; larger interiors are orange.
                 (fc (if (<= (* ih iw) 2) 5 7)))
            ;; Preserve frame borders and exterior cells; fill only zero interiors.
            (reduce
              (lambda (g2 rc)
                (if (zero? (at g2 (fst rc) (snd rc)))
                    (set-cell g2 (fst rc) (snd rc) fc)
                    g2))
              grid
              (flatmap
                (lambda (kr)
                  (map (lambda (kc) (cons kr kc))
                       (range c1 (+ c2 1))))
                (range r1 (+ r2 1))))))
        g
        objs)))))