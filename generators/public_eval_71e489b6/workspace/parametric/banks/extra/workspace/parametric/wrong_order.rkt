(rule!
 ;; Binary fields contain thin black defects and stray blue impulses/tips.
 ;; Detect BOTH kinds on the original grid, preserving narrow structural channels.
 ;; Erase stray blue, then outline black defects in orange using 8-neighbors.
 ;; A solid 2x2 core distinguishes structural components from thin defects.
 (lambda (g)
  (let ()
   (define (adj p ds)
     (filter (lambda (q) (in-bounds? (first q) (second q) h w))
       (map (lambda (d) (list (+ (first p) (first d)) (+ (second p) (second d)))) ds)))
   (define (has-core? o)
     (for/or ([p (obj-cells o)])
       (and (member (list (+ (first p) 1) (second p)) (obj-cells o))
            (member (list (first p) (+ (second p) 1)) (obj-cells o))
            (member (list (+ (first p) 1) (+ (second p) 1)) (obj-cells o)))))
   (define blues (filter (lambda (o) (= (obj-color o) 1)) (objects g -1)))
   (define blacks (filter (lambda (o) (= (obj-color o) 0)) (objects g -1)))
   (define stray
     (remove-duplicates (append
       (apply append (map obj-cells (filter (lambda (o) (not (has-core? o))) blues)))
       (filter (lambda (p)
          (<= (count-if (lambda (q) (= (at g (first q) (second q)) 1)) (adj p cardinal-deltas)) 1))
          (find-color g 1)))))
   (define holes
     (remove-duplicates (append
       (apply append (map obj-cells (filter (lambda (o) (not (has-core? o))) blacks)))
       (filter (lambda (p)
          (let* ([ns (adj p cardinal-deltas)]
                 [n (count-if (lambda (q) (= (at g (first q) (second q)) 1)) ns)])
            (or (>= n 3) (= n (length ns))))) (find-color g 0)))))
   (define clean (recolor-cells g stray 0))
   (define (outline ps)
     (filter (lambda (p) (not (member p holes)))
       (remove-duplicates (apply append (map (lambda (p) (adj p all-8-deltas)) ps)))))
   (define rims (outline holes))
   (define painted (recolor-cells clean rims 7))
   ;; Counterfactual: select the largest black defect before outlining.
   (define mask (cellmap g (r c v) (if (member (list r c) holes) 1 0)))
   (define defects (objects mask 0))
   (if (null? defects) clean
     (recolor-cells clean (outline (obj-cells (pick-max defects obj-size))) 7)))))
