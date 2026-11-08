(rule! (lambda (g)
  (let* (;; Each red object is one hollow square frame.
         (red-objs (filter (lambda (o) (= 2 (obj-color o))) (objects g 0)))
         ;; Recover every frame center and its one non-0/1/2 icon color.
         (box-data (map (lambda (o)
           (let* ((r1 (obj-r1 o)) (r2 (obj-r2 o))
                  (c1 (obj-c1 o)) (c2 (obj-c2 o))
                  (cr (/ (+ 0.0 r1 r2) 2))
                  (cc2 (/ (+ 0.0 c1 c2) 2))
                  (ic (find-first
                        (lambda (v) (and (!= 0 v) (!= 1 v) (!= 2 v)))
                        (apply append (subgrid g r1 c1 r2 c2)))))
             (list cr cc2 ic)))
           red-objs))
         (centroid-r (/ (+ 0.0 (reduce + 0 (map first box-data)))
                        (length box-data)))
         (centroid-c (/ (+ 0.0 (reduce + 0 (map (lambda (b) (nth b 1)) box-data)))
                        (length box-data)))
         ;; Sort clockwise by quadrant, then slope, around the shared centroid.
         (sorted-data (sort-by box-data (lambda (b)
           (let* ((dr (- (first b) centroid-r))
                  (dc (- (nth b 1) centroid-c))
                  (quadrant
                    (cond ((and (< dr 0) (>= dc 0)) 0)
                          ((and (>= dr 0) (> dc 0)) 1)
                          ((and (> dr 0) (<= dc 0)) 2)
                          (else 3)))
                  (slope (if (zero? dc) -99999 (/ (+ 0.0 dr) dc))))
             (+ (* quadrant 100000) slope)))))
         (icon-colors (map (lambda (b) (nth b 2)) sorted-data))
         (n (length icon-colors))
         ;; Frame i receives the icon color from the next clockwise frame.
         (recolor-pairs
           (map (lambda (i)
                  (cons (nth icon-colors i)
                        (nth icon-colors (mod (+ i 1) n))))
                (range 0 n))))
    ;; Only icon colors change; all geometry and structural colors are fixed.
    (cellmap g (r c v)
      (let* ((entry (find (lambda (p) (= v (fst p))) recolor-pairs)))
        (if entry (snd entry) v))))))