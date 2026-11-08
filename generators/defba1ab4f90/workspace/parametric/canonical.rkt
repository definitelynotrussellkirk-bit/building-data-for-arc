(rule! (lambda (g)
  ;; A red (2) edge marker fires a stream into the grid (down from a top marker, right from a
  ;; left-edge marker). Each bar it lands on STEERS it by color: blue (1) deflects the stream to
  ;; its own LEFT hand, green (3) to its RIGHT; it slides past the bar's end and flows on. A
  ;; left-edge task is solved as its transpose — transposing mirrors chirality, so blue's step
  ;; flips sign.
  (define (flow gg blue-step)
    (let* ((h (rows gg)) (w (cols gg))
           (mk (first (find-color gg 2)))
           (free? (lambda (r c) (and (>= c 0) (< c w) (zero? (at gg r c))))))
      (let fall ((r (first mk)) (c (second mk)) (cells (list mk)))
        (cond ((= r (- h 1)) (recolor-cells gg cells 2))
              ((free? (+ r 1) c) (fall (+ r 1) c (cons (list (+ r 1) c) cells)))
              (else
               (let* ((step (if (= (at gg (+ r 1) c) 1) blue-step (- blue-step))))
                 (let slide ((cc (+ c step)) (acc cells))
                   (if (free? (+ r 1) cc)
                       (fall (+ r 1) cc (cons (list (+ r 1) cc) (cons (list r cc) acc)))
                       (slide (+ cc step) (cons (list r cc) acc))))))))))
  (let* ((mk (first (find-color g 2))))
    (if (and (zero? (second mk)) (!= (first mk) 0))
        (transpose (flow (transpose g) -1))
        (flow g 1)))))