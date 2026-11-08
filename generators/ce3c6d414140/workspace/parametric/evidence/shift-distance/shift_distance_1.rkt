(rule!
  (let* ((objs (objects-8 g 0))
         (stays
          (apply append
                 (map (lambda (o)
                        (let* ((cells (obj-cells o))
                               (rs (map first cells))
                               (cs (map second cells))
                               (maxr (max-list rs))
                               (maxc (max-list cs)))
                          (filter (lambda (p)
                                    (or (= (first p) maxr)
                                        (= (second p) maxc)))
                                  cells)))
                      objs))))
    (cellmap g
      (r c v)
      (cond
        ((member? (list r c) stays) v)
        ((and (>= c 1)
              (not (= (at g r (- c 1)) 0))
              (not (member? (list r (- c 1)) stays)))
         (at g r (- c 1)))
        (else 0)))))
