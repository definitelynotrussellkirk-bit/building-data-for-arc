(rule!
 ;; Each foreground color is a possibly disconnected silhouette. Background is
 ;; the most frequent color (smallest color on ties). For each silhouette infer
 ;; the vertical axis retaining the most same-color mirror pairs. Count axis
 ;; cells once; take the leftmost doubled axis on ties. Erase unsupported pixels.
 (lambda (g)
  (let ()
   (define colors (grid-colors g))
   (define background
    (for/fold ((best (first colors))) ((color (in-list colors)))
     (if (> (count-color g color) (count-color g best)) color best)))
   (define (axis-for cells)
    (define lo (min-of second cells))
    (define hi (max-of second cells))
    (define scored
     (for/fold ((best (list -1 (* 2 lo)))) ((k (in-range (* 2 lo) (+ 1 (* 2 hi)))))
      (let ((score (count-if (lambda (p) (member (list (first p) (- k (second p))) cells)) cells)))
       (if (> score (first best)) (list score k) best))))
    (second scored))
   (for/fold ((out g)) ((color (in-list (grid-colors g background))))
    (let* ((cells (find-color g color)) (axis (axis-for cells)))
     (for/fold ((acc out)) ((p (in-list cells)))
      (if (member (list (first p) (- axis (second p))) cells)
          acc
          (set-cell acc (first p) (second p) background))))))))
