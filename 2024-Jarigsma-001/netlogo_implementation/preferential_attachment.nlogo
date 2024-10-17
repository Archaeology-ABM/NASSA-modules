breed [nodes node] ;; Define a breed of agents called 'nodes'

nodes-own [
  state            ;; current state (ranges from 0 to 1)
  orig-state       ;; each person's initially assigned state (either 0 or 1)
  output-state     ;; output of person's preference (0 or 1)
]

;;;
;;; SETUP PROCEDURES
;;; For this section of code to work:
;;; (1) create a slider with variable 'num-nodes' to represent the number of nodes in your network,
;;;     or replace 'num-nodes' in the code with the number of nodes in your network
;;; (2) create a slider with variable 'percent-state-1' to represent the percentage of nodes that are initialised with state 1

to setup
  clear-all
  set-default-shape nodes "circle"
  repeat num-nodes [ make-node ]
  create-network
  distribute-states
  ask patches [ set pcolor gray ]
  repeat num-nodes [ layout ]
  reset-ticks
end

to make-node
  create-nodes 1 [
    rt random-float 360
    fd max-pxcor
    set size 2
    set state 0.0
  ]
end

to distribute-states
  ask nodes [ set state 0 ]

  ;; Randomly select a proportion of nodes to initialize with state 1
  ask n-of ((percent-state-1 / 100) * num-nodes) nodes
    [ set state 1.0 ]
  ask nodes [
    set orig-state state     ;; Store the original state for resetting
    set output-state state
    update-color  ;; Update node color based on state
  ]
end

to update-color
  set color scale-color red state 0 1
end

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
    layout
    set new-node one-of nodes with [not any? link-neighbors]
  ]
end

;; nodes with more connections (link-neighbors) are more likely to be chosen
to-report find-partner
  let pick random-float sum [count link-neighbors] of (nodes with [any? link-neighbors])
  let partner nobody
  ask nodes [
    if partner = nobody
    [ ifelse count link-neighbors > pick
      [ set partner self]
      [ set pick pick - (count link-neighbors)]
    ]
  ]
  report partner
end

to layout
  layout-spring (turtles with [any? link-neighbors]) links 0.4 6 1
end
