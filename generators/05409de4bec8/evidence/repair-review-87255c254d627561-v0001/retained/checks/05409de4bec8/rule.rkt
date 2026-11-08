(rule!
  (let* ((target-color
          (find-first
           (lambda (color)
             (let* ((cells (find-color g color))
                    (row-count (length (remove-duplicates (map first cells))))
                    (col-count (length (remove-duplicates (map second cells)))))
               (and (= (length cells) 4)
                    (<= row-count 3)
                    (<= col-count 3))))
           (filter (lambda (color) (!= color 0)) (grid-colors g))))
         (target-cells (find-color g target-color))
         (target-rows (remove-duplicates (map first target-cells)))
         (target-cols (remove-duplicates (map second target-cells)))
         (row-pairs
          (filter
           (lambda (row)
             (= (count-where (lambda (cell) (= (first cell) row)) target-cells) 2))
           target-rows))
         (col-pairs
          (filter
           (lambda (col)
             (= (count-where (lambda (cell) (= (second cell) col)) target-cells) 2))
           target-cols))
         (rectangle? (and (= (length row-pairs) 2) (= (length col-pairs) 2)))
         (horizontal
          (if rectangle?
              (if (> (abs (- (second col-pairs) (first col-pairs)))
                     (abs (- (second row-pairs) (first row-pairs))))
                  row-pairs
                  (list))
              row-pairs))
         (vertical
          (if rectangle?
              (if (> (abs (- (second col-pairs) (first col-pairs)))
                     (abs (- (second row-pairs) (first row-pairs))))
                  (list)
                  col-pairs)
              col-pairs)))
    (cellmap
     g (r c v)
     (if (or (find (lambda (row) (= row r)) horizontal)
             (find (lambda (col) (= col c)) vertical))
         target-color
         0))))