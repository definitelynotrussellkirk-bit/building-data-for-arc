(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         ;; Find all gray (5) connected components using objects
         (objs (objects (grid-from-fn h w (lambda (r c) (if (= (cell-at g r c) 5) 5 0))) 0))
         (result (make-hash)))
    ;; Copy grid
    (for* ((r (range 0 h)) (c (range 0 w)))
      (hash-set! result (list r c) (cell-at g r c)))
    ;; Process each gray rectangle
    (for ((obj objs))
      (let* ((cells (obj-cells obj))
             (rs (map first cells)) (cs (map second cells))
             (fr1 (apply min rs)) (fc1 (apply min cs))
             (fr2 (apply max rs)) (fc2 (apply max cs))
             (fh (+ 1 (- fr2 fr1)))
             (fw (+ 1 (- fc2 fc1)))
             (tl (cell-at g (- fr1 1) (- fc1 1)))
             (tr (cell-at g (- fr1 1) (+ fc2 1)))
             (bl (cell-at g (+ fr2 1) (- fc1 1)))
             (br (cell-at g (+ fr2 1) (+ fc2 1)))
             (mid-r (+ fr1 (quotient fh 2)))
             (mid-c (+ fc1 (quotient fw 2))))
        ;; Remove corner markers
        (hash-set! result (list (- fr1 1) (- fc1 1)) 0)
        (hash-set! result (list (- fr1 1) (+ fc2 1)) 0)
        (hash-set! result (list (+ fr2 1) (- fc1 1)) 0)
        (hash-set! result (list (+ fr2 1) (+ fc2 1)) 0)
        ;; Fill quadrants
        (for* ((r (range fr1 (+ fr2 1))) (c (range fc1 (+ fc2 1))))
          (hash-set! result (list r c)
            (cond
              ((and (< r mid-r) (< c mid-c)) tl)
              ((and (< r mid-r) (>= c mid-c)) tr)
              ((and (>= r mid-r) (< c mid-c)) bl)
              (else br))))))
    (grid-from-fn h w
      (lambda (r c)
        (hash-ref result (list r c) 0))))))