(rule!
 ;; Color-6 separator rows and columns divide the input into 5x5 panels.
 ;; Ignore blank color-7 panels.  Every occupied panel contains one monochrome
 ;; path whose edge contacts are either north/south or west/east.  Order all
 ;; panels into the unique chain whose outgoing edge coordinate equals the next
 ;; panel's incoming coordinate, then lay that chain vertically or horizontally
 ;; with one color-6 separator between panels.
 (lambda (g)
  (let ()
   (define highlight-center #t)
   (define wrong-source-center #t)
   (define h (rows g))
   (define w (cols g))
   (define separator-rows
    (filter (lambda (r) (all? (lambda (c) (= (at g r c) 6)) (range 0 w)))
            (range 0 h)))
   (define separator-cols
    (filter (lambda (c) (all? (lambda (r) (= (at g r c) 6)) (range 0 h)))
            (range 0 w)))
   (define (bands n separators)
    (let loop ((cursor 0) (remaining separators) (answer '()))
     (if (null? remaining)
         (reverse (if (< cursor n) (cons (list cursor (- n 1)) answer) answer))
         (let ((s (first remaining)))
          (loop (+ s 1) (rest remaining)
                (if (< cursor s) (cons (list cursor (- s 1)) answer) answer))))))
   (define row-bands (bands h separator-rows))
   (define col-bands (bands w separator-cols))
   (define raw-panels
    (for*/list ((rb row-bands) (cb col-bands))
     (subgrid g (first rb) (first cb) (second rb) (second cb))))
   (define occupied
    (filter
     (lambda (p)
      (any? (lambda (cell) (!= (third cell) 7)) (grid-cells p)))
     raw-panels))
   (define (one-contact values)
    (if (null? values) #f (first values)))
   (define panels
    (for/list ((p occupied) (index (range 0 (length occupied))))
     (let ((ink (filter (lambda (cell) (!= (third cell) 7)) (grid-cells p))))
      (list index p
            (one-contact (map second (filter (lambda (cell) (= (first cell) 0)) ink)))
            (one-contact (map second (filter (lambda (cell) (= (first cell) 4)) ink)))
            (one-contact (map first (filter (lambda (cell) (= (second cell) 0)) ink)))
            (one-contact (map first (filter (lambda (cell) (= (second cell) 4)) ink)))))))
   (define vertical?
    (all? (lambda (p) (and (not (list-ref p 4)) (not (list-ref p 5)))) panels))
   (define (entry p) (if vertical? (list-ref p 2) (list-ref p 4)))
   (define (exit p) (if vertical? (list-ref p 3) (list-ref p 5)))
   (define starts
    (filter (lambda (p) (and (not (entry p)) (exit p))) panels))
   (define (extend order remaining)
    (let ((current (last order)))
     (if (null? remaining)
         (if (not (exit current)) (list order) '())
         (if (not (exit current))
             '()
             (apply append
                    (for/list ((candidate remaining)
                               #:when (and (entry candidate)
                                           (= (entry candidate) (exit current))))
                     (extend (append order (list candidate))
                             (remove candidate remaining))))))))
   (define solutions
    (apply append
           (for/list ((start starts))
            (extend (list start) (remove start panels)))))
   (define ordered (first solutions))
   (define middle-index (quotient (length ordered) 2))
   (define selected-source
    (if (not highlight-center)
        #f
        (first (if wrong-source-center
                   (list-ref panels middle-index)
                   (list-ref ordered middle-index)))))
   (define (render panel)
    (let ((image (second panel)))
     (if (and selected-source (= (first panel) selected-source))
         (map (lambda (row)
               (map (lambda (value) (if (= value 7) 7 9)) row))
              image)
         image)))
   (define rendered (map render ordered))
   (if vertical?
       (apply append
              (for/list ((p rendered) (i (range 0 (length rendered))))
               (if (= i (- (length rendered) 1))
                   p
                   (append p (list (make-list 5 6))))))
       (for/list ((r (range 0 5)))
        (apply append
               (for/list ((p rendered) (i (range 0 (length rendered))))
                (if (= i (- (length rendered) 1))
                    (list-ref p r)
                    (append (list-ref p r) (list 6))))))))))
