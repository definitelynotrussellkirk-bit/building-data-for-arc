(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         ;; The first full row of 5s separates the encoded icon from markers.
         (sep-row
          (let loop ((r 0))
            (cond
              ((>= r h) -1)
              ((for/and ((c (range 0 w)))
                 (= (at g r c) 5))
               r)
              (else (loop (+ r 1))))))
         (bot-start (+ sep-row 1))
         (bot-h (- h bot-start))
         (bot-w w)
         ;; Each marker-field cell expands to one 3x3 output tile.
         (base (build-grid (* bot-h 3) (* bot-w 3) (r c) 0)))
    ;; A red(2) marker stamps the stride-2 3x3 icon rotated clockwise.
    (for*/fold ((out base))
               ((br (range 0 bot-h))
                (bc (range 0 bot-w))
                #:when (= (at g (+ bot-start br) bc) 2))
      (let ((ro (* br 3))
            (co (* bc 3)))
        (for*/fold ((o out))
                   ((dr (range 0 3))
                    (dc (range 0 3)))
          (let ((v (at g (* (- 2 dc) 2) (* dr 2))))
            (if (zero? v)
                o
                (set-cell o (+ ro dr) (+ co dc) v)))))))))