(rule! (lambda (g)
  ;; alt: crop the left panel, then overlay the right panel only where the left has zero and the panels are zero-complements.
  (let* ((h (rows g))
         (left-w 4)
         (zero-complements?
          (for*/and ((r (in-range h))
                     (c (in-range left-w)))
            (not (equal? (zero? (at g r c))
                         (zero? (at g r (+ c 5))))))))
    (grid-from-fn h left-w
      (lambda (r c)
        (let ((left (at g r c))
              (right (at g r (+ c 5))))
          (if zero-complements?
              (if (zero? left) right left)
              right)))))))