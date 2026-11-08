(rule!
 ;; First compute the exact canonical intersection. Its largest connected
 ;; overlap selects a whole TOP object; recover that object's missing cells.
 (lambda (g)
   (let* ((overlap (let ((dummy 0)) (let* ((divider (first (filter (lambda (r) (all? (lambda (v) (= v 5)) (row g r))) (range (rows g))))) (top (subgrid g 0 0 (- divider 1) (- (cols g) 1))) (bottom (subgrid g (+ divider 1) 0 (- (rows g) 1) (- (cols g) 1)))) (grid-from-fn (rows top) (cols top) (lambda (r c) (if (and (not (= (at top r c) 0)) (not (= (at bottom r c) 0))) 8 0))))))
          (top (take g (rows overlap)))
          (parts (objects overlap 0))
          (winner (first (sort-by parts (lambda (o) (- 0 (obj-size o))))))
          (seed (first (obj-cells winner)))
          (target (find-first (lambda (o) (member seed (obj-cells o))) (objects top 0))))
     (grid-from-fn (rows overlap) (cols overlap)
       (lambda (r c) (if (member (list r c) (obj-cells target)) 8 0))))))