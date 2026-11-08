(rule!
  (let* ((mark-rows (map fst (find-color g 1)))
         (mark-cols (map snd (filter (lambda (p) (= (fst p) 0)) (find-color g 2)))))
    (reduce (lambda (out r)
      (reduce (lambda (acc c) (set-cell acc r c 3)) out mark-cols))
      g mark-rows)))