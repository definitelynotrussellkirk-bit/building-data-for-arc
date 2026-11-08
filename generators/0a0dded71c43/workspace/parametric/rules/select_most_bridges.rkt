(rule!
  (let* ((filled
          (grid-from-fn h w
            (lambda (r c)
              (let ((v (cell-at g r c)))
                (if (and (= v 0)
                         (or (and (> c 0) (< c (- w 1))
                                  (= (cell-at g r (- c 1)) 6)
                                  (= (cell-at g r (+ c 1)) 6))
                             (and (> r 0) (< r (- h 1))
                                  (= (cell-at g (- r 1) c) 6)
                                  (= (cell-at g (+ r 1) c) 6))))
                    7
                    v))))))
    (define (active? v) (or (= v 6) (= v 7)))
    (define (components67 grid)
      (define visited (make-hash))
      (define comps (list))
      (for* ((r (in-range (rows grid)))
             (c (in-range (cols grid))))
        (when (and (active? (at grid r c))
                   (not (hash-has-key? visited (cons r c))))
          (let ((cells
                 (connected-region grid r c
                   (lambda (rr cc v) (active? v))
                   4)))
            (for ((p (in-list cells)))
              (hash-set! visited (cons (first p) (second p)) #t))
            (set! comps (cons cells comps)))))
      (reverse comps))
    (define (new-bridge? p)
      (let ((r (first p)) (c (second p)))
        (and (= (at g r c) 0) (= (at filled r c) 7))))
    (define (bridge-count cells)
      (length (filter new-bridge? cells)))
    (define candidates
      (filter (lambda (cells) (> (bridge-count cells) 0))
              (components67 filled)))
    (if (empty? candidates)
        filled
        (let ((winner
               (argmax (lambda (cells)
                         (+ (* 1000 (bridge-count cells)) (length cells)))
                       candidates)))
          (paint-cells filled winner 8)))))
