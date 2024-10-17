breed [nodes node]   ;; Define a new breed of agents called 'nodes'


;; CREATE NETWORK IN SETUP PROCEDURE

to create-network
  ;; make the initial network of two nodes and an edge
  let partner nobody
  let first-node one-of nodes
  let second-node one-of nodes with [self != first-node]
  ask first-node [ create-link-with second-node [ set color white ] ]

  ;; randomly select unattached node and connect it to a partner already in the network
  let new-node one-of nodes with [not any? link-neighbors]
  while [new-node != nobody] [
    set partner find-partner
    ask new-node [ create-link-with partner [ set color white ] ]
    ;layout
    set new-node one-of nodes with [not any? link-neighbors]
  ]
end

;; nodes with more connections (link-neighbors) are more likely to be chosen
to-report find-partner
  let pick random-float sum [count link-neighbors] of (nodes with [any? link-neighbors])
  let partner nobody
  ask nodes
  [ ;; if there's no winner yet
    if partner = nobody
    [ ifelse count link-neighbors > pick
      [ set partner self]
      [ set pick pick - (count link-neighbors)]
    ]
  ]
  report partner
end

;; THE FOLLOWING PROCEDURE IS NOT NECESSARY BUT VERY HELPFUL
;; If used, make sure to remove the semi-colon before 'layout' in the 'to create-network' function

;to layout
;  layout-spring (turtles with [any? link-neighbors]) links 0.4 6 1
;end
