;; Compare 4-connected objects by exact translated shape (no rotation/flip).
;; Singleton shape classes become red 2; repeated classes become blue 1.
(rule!
 (lambda (g)
   (let* ((objs (objects g 0)))
     (paint-objects-by
      g objs
      (lambda (o)
        (let* ((n-matches
                (count-if (lambda (other) (same-shape? o other)) objs)))
          (if (= n-matches 1) 2 1)))))))
