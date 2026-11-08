(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         ;; Locate the unique red source endpoint.
         (red-pos
          (let loop ((r 0) (c 0))
            (cond
              ((>= r h) #f)
              ((>= c w) (loop (+ r 1) 0))
              ((= (at g r c) 2) (list r c))
              (else (loop r (+ c 1))))))
         ;; Locate the unique blue destination endpoint.
         (blue-pos
          (let loop ((r 0) (c 0))
            (cond
              ((>= r h) #f)
              ((>= c w) (loop (+ r 1) 0))
              ((= (at g r c) 1) (list r c))
              (else (loop r (+ c 1))))))
         (rr (first red-pos))
         (rc (second red-pos))
         (br (first blue-pos))
         (bc (second blue-pos))
         ;; Unit signs point from red toward blue.
         (drow (if (> br rr) 1 -1))
         (dcol (if (> bc rc) 1 -1))
         (dr-abs (abs (- br rr)))
         (dc-abs (abs (- bc rc)))
         (max-d (if (> dr-abs dc-abs) dr-abs dc-abs))
         ;; The gap difference is the dominant-axis middle phase length.
         (straights (- max-d (if (> dr-abs dc-abs) dc-abs dr-abs)))
         (is-vert (> dr-abs dc-abs))
         ;; Build interior cells in order: one diagonal, dominant-axis
         ;; straights, then the remaining diagonals into blue.
         (path-cells
          (let loop ((step 1) (cur-r rr) (cur-c rc) (acc (list)))
            (cond
              ((>= step max-d) (reverse acc))
              (else
               (let* ((new-r-c
                       (cond
                         ;; Proposed variant: take the dominant-axis block first.
                         ((<= step straights)
                          (if is-vert
                              (list (+ cur-r drow) cur-c)
                              (list cur-r (+ cur-c dcol))))
                         ;; Then take all diagonal steps toward blue.
                         (else (list (+ cur-r drow) (+ cur-c dcol)))))
                      (nr (first new-r-c))
                      (nc (second new-r-c)))
                 (loop (+ step 1) nr nc (cons (list nr nc) acc))))))))
    ;; Paint only path interiors green; keep both endpoint colors unchanged.
    (for/fold ((out g)) ((cell path-cells))
      (set-cell out (first cell) (second cell) 3)))))
