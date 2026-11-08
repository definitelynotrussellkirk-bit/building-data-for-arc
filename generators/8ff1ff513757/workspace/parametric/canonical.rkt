(rule!
 ;; Drop the all-empty rows (an entirely empty grid becomes one zero row).
 (let ((kept (filter (lambda (row) (any? (lambda (v) (!= v 0)) row)) g)))
   (if (empty? kept) (list (make-list w 0)) kept)))