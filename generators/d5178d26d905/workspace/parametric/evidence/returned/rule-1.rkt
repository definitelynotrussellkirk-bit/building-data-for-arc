(rule!
 ;; A full gray(5) column splits the board: one side is a REFERENCE
 ;; panel drawn only in 0/4 (yellow marks the line columns, and its
 ;; rarer rows mark SPECIAL rows), the other a TEMPLATE panel of
 ;; colored vertical lines whose special rows show a highlight fill.
 ;; Repaint the reference: line columns take the template line colors;
 ;; each special reference row takes its matching template row's fill,
 ;; keeping a line cell colored only where the template kept it.
 (lambda (g)
   (let ()
     (define div-col
       (find-first (lambda (c) (all? (lambda (r) (= (at g r c) 5))
                                     (range 0 h)))
                   (range 0 w)))
     (define (panel cstart cend)  ;; non-gray rows of the region, cropped
       (map (lambda (r) (for/list ((cx (range cstart cend))) (at g r cx)))
            (filter (lambda (r) (any? (lambda (cx) (not (= (at g r cx) 5)))
                                      (range cstart cend)))
                    (range 0 h))))
     (define left (panel 0 div-col))
     (define right (panel (+ div-col 1) w))
     (define (ref? mat)
       (all? (lambda (row) (all? (lambda (v) (or (zero? v) (= v 4))) row))
             mat))
     (define ref (if (ref? left) left right))
     (define tmp (if (ref? left) right left))
     (define tmp-w (length (first tmp)))
     (define tmp-normal  ;; the template's most common row
       (pick-max (remove-duplicates tmp)
                 (lambda (row) (count-if (lambda (r2) (equal? r2 row))
                                         tmp))))
     (define line-cols
       (filter (lambda (cx) (not (zero? (nth tmp-normal cx))))
               (range 0 tmp-w)))
     (define line-colors (map (lambda (cx) (nth tmp-normal cx)) line-cols))
     (define tmp-specials
       (filter (lambda (i) (not (equal? (nth tmp i) tmp-normal)))
               (range 0 (length tmp))))
     (define (yellows row) (count-if (lambda (v) (= v 4)) row))
     (define ref-normal  ;; the ref row with the fewest (but >0) yellows
       (pick-min (filter (lambda (row) (> (yellows row) 0)) ref) yellows))
     (define ref-line-cols
       (filter (lambda (cx) (= (nth ref-normal cx) 4))
               (range 0 (length (first ref)))))
     (define ref-specials
       (reverse
        (filter (lambda (i) (and (> (yellows (nth ref i)) 0)
                                 (not (equal? (nth ref i) ref-normal))))
                (range 0 (length ref)))))
     (define (index-in lst v)
       (let loop ((xs lst) (i 0))
         (cond ((null? xs) -1)
               ((= (car xs) v) i)
               (else (loop (cdr xs) (+ i 1))))))
     (define (fill-of tmp-row)  ;; the row's color off the line columns
       (let loop ((cx 0))
         (cond ((>= cx tmp-w) 0)
               ((member? cx line-cols) (loop (+ cx 1)))
               (else (nth tmp-row cx)))))
     (build-grid (length ref) (length (first ref)) (rr cc)
                 (let ((si (index-in ref-specials rr)))
                   (if (>= si 0)
                       (let* ((tmp-row (nth tmp (nth tmp-specials si)))
                              (fill (fill-of tmp-row)))
                         (if (member? cc ref-line-cols)
                             (let* ((k (index-in ref-line-cols cc))
                                    (tv (nth tmp-row (nth line-cols k)))
                                    (lc (nth line-colors k)))
                               (if (= tv lc) lc fill))
                             fill))
                       (if (member? cc ref-line-cols)
                           (nth line-colors (index-in ref-line-cols cc))
                           0)))))))
