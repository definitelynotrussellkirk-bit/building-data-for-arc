(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         ;; Scan the four 2x2 corner slots in reading order.  The first slot
         ;; whose top edge is neither background 0 nor separator 8 is the key.
         (key-r #f)
         (key-c #f)
         (key-scan
          (for ((pos (list (list 0 0)
                           (list 0 (- w 2))
                           (list (- h 2) 0)
                           (list (- h 2) (- w 2)))))
            (let ((kr (first pos)) (kc (second pos)))
              (when (and (not key-r)
                         (!= (at g kr kc) 0)
                         (!= (at g kr kc) 8)
                         (!= (at g kr (+ kc 1)) 0)
                         (!= (at g kr (+ kc 1)) 8))
                (set! key-r kr)
                (set! key-c kc)))))
         ;; The four key cells are the output colors for TL/TR/BL/BR.
         (k00 (at g key-r key-c))
         (k01 (at g key-r (+ key-c 1)))
         (k10 (at g (+ key-r 1) key-c))
         (k11 (at g (+ key-r 1) (+ key-c 1)))
         (key-set (make-hash))
         (key-set-init
          (begin
            (hash-set! key-set (list key-r key-c) #t)
            (hash-set! key-set (list key-r (+ key-c 1)) #t)
            (hash-set! key-set (list (+ key-r 1) key-c) #t)
            (hash-set! key-set (list (+ key-r 1) (+ key-c 1)) #t)))
         ;; The last non-key, non-0/8 cell in reading order names the marker
         ;; color. Earlier body colors are distractors and must stay unchanged.
         (marker #f)
         (marker-scan
          (for* ((r (range 0 h)) (c (range 0 w)))
            (when (and
                       (!= (at g r c) 0)
                       (!= (at g r c) 8)
                       (not (hash-has-key? key-set (list r c))))
              (set! marker (at g r c)))))
         ;; Zeros count toward the body bbox; only separator 8 and the key are
         ;; excluded.  Exact midpoint cells therefore belong bottom/right.
         (body-cells
          (for*/list ((r (range 0 h)) (c (range 0 w))
                      #:when (and (!= (at g r c) 8)
                                  (not (hash-has-key? key-set (list r c)))))
            (list r c)))
         (r1 (min-of first body-cells))
         (r2 (max-of first body-cells))
         (c1 (min-of second body-cells))
         (c2 (max-of second body-cells))
         (mid-r2 (+ r1 r2))
         (mid-c2 (+ c1 c2)))
    (build-grid h w (r c)
      (let ((v (at g r c)))
        (if (and (= v marker)
                 (not (hash-has-key? key-set (list r c))))
            (let ((qr (if (< (* 2 r) mid-r2) 0 1))
                  (qc (if (< (* 2 c) mid-c2) 0 1)))
              (cond ((and (zero? qr) (zero? qc)) k00)
                    ((and (zero? qr) (= qc 1)) k01)
                    ((and (= qr 1) (zero? qc)) k10)
                    (else k11)))
            v))))))