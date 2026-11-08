(rule!
 ;; Complete a dense square color table whose zero cells are erased observations.
 ;; Stage A repairs every zero with a visible transpose partner.  Stage B consumes
 ;; that intermediate and closes any remaining holes under the row/column suffix
 ;; mirrors that leave indices 0 and 1 fixed.  The alternative stops after A.
 (lambda (g)
  (let ()
   (define completion "closure")
   (define rival "")
   (define h (rows g))
   (define w (cols g))
   (define prefix (cond [(equal? rival "wrong_prefix_one") 1]
                        [(equal? rival "wrong_prefix_three") 3]
                        [else 2]))
   (define (mirror-index i n) (if (< i prefix) i (- (+ n prefix -1) i)))
   (define (transpose-source r c)
    (if (equal? rival "anti_diagonal") (list (- h 1 c) (- w 1 r)) (list c r)))
   ;; A: simultaneous transpose repair from the original input.
   (define stage-a
    (if (equal? rival "fold_only") g
     (for*/fold ([out g]) ([r (in-range h)] [c (in-range w)])
      (let* ([p (transpose-source r c)] [rr (first p)] [cc (second p)])
       (if (and (= (at g r c) 0) (in-bounds? rr cc h w) (!= (at g rr cc) 0))
           (set-cell out r c (at g rr cc)) out)))))
   (define b-source (if (equal? rival "stage_b_original") g stage-a))
   (define (candidates r c)
    (let ([mr (mirror-index r h)] [mc (mirror-index c w)])
     (cond [(equal? rival "row_only") (list (list mr c))]
           [(equal? rival "column_only") (list (list r mc))]
           [(equal? rival "double_only") (list (list mr mc))]
           [else (list (list mr c) (list r mc) (list mr mc))])))
   ;; B: fill the residual cells using A's repaired grid as the donor table.
   (define stage-b
    (for*/fold ([out stage-a]) ([r (in-range h)] [c (in-range w)])
     (if (!= (at stage-a r c) 0) out
      (let ([v (for/first ([p (in-list (candidates r c))]
                           #:when (!= (at b-source (first p) (second p)) 0))
                 (at b-source (first p) (second p)))])
       (if v (set-cell out r c v) out)))))
   (define forced-closure
    (member rival '("fold_only" "row_only" "column_only" "double_only"
                    "stage_b_original" "wrong_prefix_one" "wrong_prefix_three")))
   (define use-closure
    (if (equal? rival "other_setting") (equal? completion "transpose_only")
        (or forced-closure (equal? completion "closure"))))
   (cond [(equal? rival "identity") g]
         [(equal? rival "fill_one")
          (for*/fold ([out g]) ([r (in-range h)] [c (in-range w)])
           (if (= (at g r c) 0) (set-cell out r c 1) out))]
         [use-closure stage-b]
         [else stage-a]))))
