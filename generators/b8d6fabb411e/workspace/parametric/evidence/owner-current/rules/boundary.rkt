(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         ;; Find the 3-square
         (threes (find-color g 3))
         ;; Top edge of the threes bbox
         (tr1 (apply min (map first threes)))
         ;; Left edge of the threes bbox
         (tc1 (apply min (map second threes)))
         ;; Bottom edge of the threes bbox
         (tr2 (apply max (map first threes)))
         ;; Right edge of the threes bbox
         (tc2 (apply max (map second threes)))
         ;; Find colored pixels (non-0, non-3)
         (pixels (for*/list ((r (range 0 h)) (c (range 0 w))
                             #:when (let ((v (cell-at g r c)))
                                      (and (not (= v 0)) (not (= v 3)))))
                   (list r c (cell-at g r c))))
         ;; Mutable lookup table for result
         (result (make-hash)))
    ;; Copy grid
    (for* ((r (range 0 h)) (c (range 0 w)))
      (hash-set! result (list r c) (cell-at g r c)))
    ;; For each pixel, check if axis-aligned with 3-square
    (for ((px pixels))
      (let ((pr (first px)) (pc (second px)) (pcolor (third px)))
        ;; Same row as top or bottom of square?
        (cond
          ;; Pixel on same row as square, to the right
          ((and (or (= pr tr1) (= pr tr2)) (> pc tc2))
           (for ((c (range (+ tc2 1) pc)))
             (hash-set! result (list pr c) pcolor)))
          ;; To the left
          ((and (or (= pr tr1) (= pr tr2)) (< pc tc1))
           (for ((c (range (+ pc 1) tc1)))
             (hash-set! result (list pr c) pcolor)))
          ;; Same col as square, below
          ((and (or (= pc tc1) (= pc tc2)) (> pr tr2))
           (for ((r (range (+ tr2 1) pr)))
             (hash-set! result (list r pc) pcolor)))
          ;; Above
          ((and (or (= pc tc1) (= pc tc2)) (< pr tr1))
           (for ((r (range (+ pr 1) tr1)))
             (hash-set! result (list r pc) pcolor))))))
    (grid-from-fn h w
      (lambda (r c)
        (hash-ref result (list r c) 0))))))