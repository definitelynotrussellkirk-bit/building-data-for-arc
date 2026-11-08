(rule!
 ;; The modal input color is background. The largest other color is the
 ;; target frame, whose bounding rectangle is the output domain.
 ;; External multicolor rectangular pieces must tile all target background
 ;; cells by translation only. Row-major first-hole search backtracks over
 ;; the complete inventory and carries the resulting positioned pieces.
 ;; Preserve frame cells and the internal orientation/colors of every piece.
 (lambda (g)
  (let ()
   (define bg (pick-max (grid-colors g) (lambda (x) (count-color g x))))
   (define frame (pick-max (grid-colors g bg) (lambda (x) (count-color g x))))
   (define bb (bbox-of-cells (find-color g frame)))
   (define board (subgrid g (first bb) (second bb) (third bb) (fourth bb)))
   (define outside
    (grid-from-fn (rows g) (cols g)
     (lambda (r c)
      (if (and (<= (first bb) r) (<= r (third bb))
               (<= (second bb) c) (<= c (fourth bb))) bg (at g r c)))))
   (define pieces
    (map (lambda (obj) (subgrid outside (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj)))
         (objects-multicolor outside bg)))
   (define (covered r c piece)
    (positions-in-rect r c (+ r (rows piece) -1) (+ c (cols piece) -1)))
   (define (search holes inventory)
    (if (null? holes) '()
     (let* ((anchor (first holes)) (r (first anchor)) (c (second anchor)))
      (let try ((options inventory))
       (if (null? options) #f
        (let* ((piece (first options)) (used (covered r c piece)))
         (if (andmap (lambda (p) (member p holes)) used)
          (let ((tail (search (filter (lambda (p) (not (member p used))) holes)
                              (remove piece inventory))))
           (if tail (cons (list r c piece) tail) (try (rest options))))
          (try (rest options)))))))))
   (define placed (search (find-color board bg) pieces))
   (define selected-piece (third (first placed)))
   (define selected-frame (pick-max (grid-colors selected-piece) (lambda (x) (count-color selected-piece x))))
   (define assembled
    (for/fold ((out board)) ((record placed))
     (for*/fold ((acc out)) ((r (range (rows (third record)))) (c (range (cols (third record)))))
      (set-cell acc (+ (first record) r) (+ (second record) c) (at (third record) r c)))))
   (grid-from-fn (rows board) (cols board)
    (lambda (r c) (if (= (at board r c) frame) selected-frame (at assembled r c)))))))
