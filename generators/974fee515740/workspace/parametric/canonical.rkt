(rule!
  (let ((dummy 0))
    (define (same-pos? a b)
      (and (= (fst a) (fst b)) (= (snd a) (snd b))))
    (define (has-cell? p cells)
      (any? (lambda (q) (same-pos? p q)) cells))
    (define (rotate-by cells code)
      (cond
        [(= code 2) (normalize-cells (rotate-cells-cw cells))]
        [(= code 3) (normalize-cells (rotate-cells-cw (rotate-cells-cw cells)))]
        [(= code 4) (normalize-cells (rotate-cells-cw (rotate-cells-cw (rotate-cells-cw cells))))]
        [else (normalize-cells cells)]))
    (define (render cells)
      (if (empty? cells)
          (list (list 0))
          (let* ((norm (normalize-cells cells))
                 (bb (bbox-of-cells norm))
                 (out-h (+ 1 (third bb)))
                 (out-w (+ 1 (fourth bb))))
            (grid-from-fn out-h out-w
              (lambda (r c) (if (has-cell? (list r c) norm) 8 0))))))
    (let* ((nz (filter (lambda (v) (not (= v 0))) (row-at g 0)))
           (op-raw (if (empty? nz) 6 (first nz)))
           (rot-raw (if (> (length nz) 1) (second nz) 1))
           (op (if (member? op-raw (list 3 4 6 7)) op-raw 6))
           (rot-code (if (member? rot-raw (list 1 2 3 4)) rot-raw 1))
           (red-obj (first (filter (lambda (obj) (= (obj-color obj) 2)) (objects g 0))))
           (blue-obj (first (filter (lambda (obj) (= (obj-color obj) 1)) (objects g 0))))
           (red (normalize-cells (obj-cells red-obj)))
           (blue (rotate-by (normalize-cells (obj-cells blue-obj)) rot-code))
           (result
             (cond
               [(= op 3) (append red (filter (lambda (p) (not (has-cell? p red))) blue))]
               [(= op 4) (filter (lambda (p) (has-cell? p blue)) red)]
               [(= op 6)
                (append
                  (filter (lambda (p) (not (has-cell? p blue))) red)
                  (filter (lambda (p) (not (has-cell? p red))) blue))]
               [else (filter (lambda (p) (not (has-cell? p blue))) red)])))
      (render result))))