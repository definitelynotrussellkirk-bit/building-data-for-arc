(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         ;; Exactly four gray cells are present: three square-bbox corners and
         ;; one interior distractor. The bbox extremes identify the square.
         (marks (find-color g 5))
         (r0 (min-of fst marks))
         (r1 (max-of fst marks))
         (c0 (min-of snd marks))
         (c1 (max-of snd marks))
         (d (- r1 r0))
         (tl? (= (at g r0 c0) 5))
         (tr? (= (at g r0 c1) 5))
         (bl? (= (at g r1 c0) 5))
         ;; The absent bbox corner determines the triangle orientation.
         (missing (cond ((not tl?) 0)
                        ((not tr?) 1)
                        ((not bl?) 2)
                        (else 3))))
    ;; Paint only orange background cells, preserving all four gray clues.
    (define (paint-if-bg acc r c)
      (if (and (in-bounds? r c h w) (= (at acc r c) 7))
          (set-cell acc r c 8)
          acc))
    (define (paint-h acc r ca cb)
      (reduce (lambda (a c) (paint-if-bg a r c))
              acc
              (range ca (+ cb 1))))
    (define (paint-v acc c ra rb)
      (reduce (lambda (a r) (paint-if-bg a r c))
              acc
              (range ra (+ rb 1))))
    (define (paint-diag-down acc)
      (reduce (lambda (a k) (paint-if-bg a (+ r0 k) (+ c0 k)))
              acc
              (range 0 (+ d 1))))
    (define (paint-diag-up acc)
      (reduce (lambda (a k) (paint-if-bg a (+ r0 k) (- c1 k)))
              acc
              (range 0 (+ d 1))))
    ;; Draw the two square sides incident to the missing corner and the
    ;; diagonal joining the other two present corners.
    (cond
      ((zero? missing)
       (paint-diag-up (paint-v (paint-h g r0 c0 c1) c0 r0 r1)))
      ((= missing 1)
       (paint-diag-down (paint-v (paint-h g r0 c0 c1) c1 r0 r1)))
      ((= missing 2)
       (paint-diag-down (paint-v (paint-h g r1 c0 c1) c0 r0 r1)))
      (else
       (paint-diag-up (paint-v (paint-h g r1 c0 c1) c1 r0 r1)))))))