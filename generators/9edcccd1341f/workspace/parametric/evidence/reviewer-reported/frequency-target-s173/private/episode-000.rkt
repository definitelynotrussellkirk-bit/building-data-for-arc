(rule!
 ;; Keep the color key unchanged. Inside the old frame, the unique most-common
 ;; nonzero color other than the frame color selects both the replacement color
 ;; and the cells whose bounding box becomes the inner hollow rectangle.
 (lambda (g)
   (let* ((h (rows g))
          (w (cols g))
          ;; The uniform outer frame begins at row 1; row 0 is the preserved key.
          (bdr (at g 1 0))
          ;; Each entry is (row column color) for a non-background, non-frame
          ;; interior cell.
          (interior
           (for*/list ((r (range 2 (- h 1)))
                       (c (range 1 (- w 1)))
                       #:when (let ((v (at g r c)))
                                (and (!= v 0) (!= v bdr))))
             (list r c (at g r c))))
          (colors (unique (map third interior)))
          (counts
           (map (lambda (clr)
                  (list clr
                        (count-if (lambda (cell) (= (third cell) clr))
                                  interior)))
                colors))
          ;; The task grammar guarantees one strict frequency maximum.
          (winner (first (pick-max counts second)))
          (win-cells (filter (lambda (cell) (= (third cell) winner))
                             interior))
          (r1 (min-of first win-cells))
          (r2 (max-of first win-cells))
          (c1 (min-of second win-cells))
          (c2 (max-of second win-cells)))
     (cellmap g (r c v)
       (cond
         ;; Preserve the key row verbatim.
         ((zero? r) v)
         ;; Recolor the full old outer frame with the winner.
         ((or (= r 1) (= r (- h 1)) (zero? c) (= c (- w 1))) winner)
         ;; Draw the winner bounding box as a hollow rectangle.
         ((or (and (or (= r r1) (= r r2)) (>= c c1) (<= c c2))
              (and (or (= c c1) (= c c2)) (>= r r1) (<= r r2)))
          winner)
         ;; Drop every original interior cell not on that hollow rectangle.
         (else 0))))))