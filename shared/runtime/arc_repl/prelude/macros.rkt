;; ARC REPL Macros — syntactic shortcuts for common patterns

;; Transform cells matching a condition
;; (transform-where grid (= v 8) 4) → recolor 8 to 4
(defmacro transform-where (grid condition action)
  (map-grid grid (lambda (r c v) (if condition action v))))

;; when/unless — one-branch conditionals
(defmacro when (test body)
  (if test body #f))

(defmacro unless (test body)
  (if test #f body))
