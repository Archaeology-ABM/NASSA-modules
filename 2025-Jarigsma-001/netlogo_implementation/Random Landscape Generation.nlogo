breed [ settlements settlement ]

globals [
  landscape-types ;; the set of landscape types
  valid-landscape-types ;; valid landscape types for settlement placement
  land-covers ;; the set of landcover types
]

patches-own [
  landscape-type
  landscape-id

  use
  biomass
]

settlements-own [
  no-households ; counts how many households are in a settlement
]

to setup
  clear-all

  ask patches [set landscape-id 0] ;;  with landscape-id = 0, patches have an undefined landscape type
  ask patches with [landscape-id = 0] [
    set landscape-type "undefined"
    set use "undefined"
  ]

; INPUT LANDSCAPE AND LANDCOVER PARAMETERS HERE
;--------------------------------------------------------------------------------------------------------------------------------------
  ;; Landscape types, their proportion of the land, and their color should be set here.
  ;; NOTE: the landscape types should be set in order from central landscape to outermost landscape type. ID number must always start with 1.
  ;; Format: [1 "swamp" 0.5 blue]
  set landscape-types [
    [1 "levee" 0.2 brown] ; ID, landscape name, proportion of world the landscape should cover, colour
    [2 "floodbasin" 0.2 green]
  ]

 ;; Users need to define valid landscape types for settlement placement
  ;; Format: ["levee" "floodbasin" "swamp"]
  set valid-landscape-types ["levee"]


 ;; Users need to define cover types for different landscape types
  ;; [cover-id, cover-type, target-landscape-type, %cover, min. volume biomass per ha (m3), max. volume of biomass per ha (m3)]
  ;; Format: [1 "forest" "levee" 0.5 70 150]
  ;; NOTE: if the target-landscape is not a defined landscape type, please input "undefined" as the target-landscape
  set land-covers [
    [1 "forest" "levee" 0.2 80 120]
    [2 "fen" "undefined" 0.2 70 130]
  ]
;--------------------------------------------------------------------------------------------------------------------------------------


    ;; Checking that the sum of the proportion of landscape-types does not exceed 1 (100%)
  let total-proportion-types sum map [type-info -> item 2 type-info] landscape-types
  if total-proportion-types > 1 [
    user-message (word "WARNING: The combined proportion of landscape types exceeds 100% (" (total-proportion-types * 100) "%). Please reduce the proportions so they sum to 100% or less.")
    stop
  ]

  ;; Checking that the sum of the proportion of landcover does not exceed 1 (100%), for each landscape-type
  let cover-target-types remove-duplicates map [cover-info -> item 2 cover-info] land-covers
  foreach cover-target-types [ target-type ->
  let total-cover-proportion sum map [cover-info -> cover-proportion-if-target cover-info target-type] land-covers

  if total-cover-proportion > 1 [
    user-message (word "WARNING: The total land-cover proportion for landscape-type '" target-type "' exceeds 100% (" (total-cover-proportion * 100) "%). Please reduce the proportions so they sum to 100% or less.")
    stop
  ]
]

  setup-landscape
end

;; this is a helper reporter for checking landcover proportions do not exceed 1
to-report cover-proportion-if-target [cover-info target-type]
  if item 2 cover-info = target-type [
    report item 3 cover-info
  ]
  report 0
end

to setup-landscape

    resize-world min-patch-xcor max-patch-xcor min-patch-ycor max-patch-ycor
    set-patch-size patch-pixel-size

  let previous-type-id 0 ;; this is temporarily created so that landscape types will always be setup in concentric rings around the previous landscape type

  ;; looping through each landscape type
  foreach landscape-types [ type-info ->
    let type-id first type-info
    let type-name item 1 type-info
    let type-proportion item 2 type-info
    let type-color last type-info

 ;; randomly choosing a patch to be the centre of the concentric rings for the first landscape type
    if type-id = 1 [
    while [all? patches [landscape-id = 0]] [
      ask one-of patches [
          set pcolor type-color
          set landscape-type type-name
          set landscape-id type-id
        ]
    ]
    ]

      while [count patches with [landscape-id = type-id] < (count patches * type-proportion)] [
        ask patches with [(landscape-id > 0)] [
          let target one-of neighbors with [landscape-id = 0]
          if target != nobody [
            ask target [
            set pcolor type-color
            set landscape-type type-name
            set landscape-id type-id
          ]
          ]
        ]
      ]
      set previous-type-id type-id
  ]
  setup-landcover

  if include-settlements [setup-agents] ;; checks if the user wants to include settlements in their landscape
end


to setup-landcover
  ;; loop through all landcover definitions in the landcovers list
  foreach land-covers [cover-info ->
    let cover-id item 0 cover-info
    let cover-type item 1 cover-info
    let target-type item 2 cover-info
    let cover-percent item 3 cover-info
    let min-biomass item 4 cover-info
    let max-biomass item 5 cover-info
    let biomass-diff (max-biomass - min-biomass)

    ;; calculating how many patches should be assigned the cover type
    let eligible-patches patches with [landscape-type = target-type]
    let target-count round (count eligible-patches * cover-percent)

    ;; if the user chooses to turn on the option for contiguous landcover, we start with one seed. Otherwise, landcover is assigned randomly on eligible patches
    ifelse contiguous-landcover [
      ask one-of eligible-patches [
      grow-contiguous-cover eligible-patches cover-type target-count min-biomass biomass-diff
    ]
    ] [
      let selected-patches n-of target-count eligible-patches
      ask selected-patches [
        let biomass-volume (random biomass-diff) + min-biomass
        set use cover-type
        set biomass biomass + (biomass-volume * biomass-density)
      ]
    ]
  ]

  ;; colouring patches with biomass
     ask patches with [ biomass > 0 ] [
      set pcolor scale-color green biomass 100000 1000 ;; patches are shaded according to biomass values
    ]
end

to grow-contiguous-cover [eligible cover-type target-count min-biomass biomass-diff]
 ;; picking one random eligible patch to act as the initial seed
  let seed one-of eligible
  let grown-patches (patch-set seed)

  ;; assign cover type to the seed
   ask seed [
    let biomass-volume (random biomass-diff) + min-biomass
    set use cover-type
    set biomass biomass + (biomass-volume * biomass-density)
  ]

  ;; creating the frontier with eligible patches neighbouring the seed
  let frontier no-patches
  ask seed [
    set frontier neighbors with [
    member? self eligible and not member? self grown-patches
  ]
  ]

  ;; keep growing until we hit the target number of patches
  while [count grown-patches < target-count and any? frontier] [
    ifelse any? frontier [
    let new-patch one-of frontier

    ask new-patch [
      let biomass-volume (random biomass-diff) + min-biomass
      set use cover-type
      set biomass biomass + (biomass-volume * biomass-density)
    ]

    set grown-patches (patch-set grown-patches new-patch)

    ;; updating the frontier
    ask new-patch [
      set frontier (patch-set frontier neighbors with [
      member? self eligible and
      not member? self grown-patches
      ])
      ]
    set frontier frontier with [not member? self grown-patches]
  ] [
      ;; fallback: if the set of frontier patches is empty but the target-count has not yet been reached, another seed is generated on an eligible patch
      if count grown-patches < target-count [
      let fallback-seed one-of eligible with [not member? self grown-patches]
      if fallback-seed != nobody [
      ask fallback-seed [
        let biomass-volume (random biomass-diff) + min-biomass
        set use cover-type
        set biomass biomass + (biomass-volume * biomass-density)
      ]
        set grown-patches (patch-set grown-patches fallback-seed)

       ;; updating the frontier to include neighbours of the fallback-seed
       ask fallback-seed [
            set frontier neighbors with [
          member? self eligible and
          not member? self grown-patches
        ]
      ]
    ]
  ]
  ]
  ]
end

to setup-agents
  set-default-shape settlements "house"
  let num-settlements 0 ;; creating a counter for the number of settlements

  while [num-settlements < max-settlements] [
    let household-count (random max-households-per-settlement) + 1 ; ensures that there is at least one household in each settlement

    ; find valid patches for settlements
    let valid-patch one-of patches with [
      member? landscape-type valid-landscape-types and not any? settlements-here
    ]

    if valid-patch != nobody [
      ask valid-patch [
        sprout-settlements 1 [
          set no-households household-count
        ]
      ]
    ]

    set num-settlements num-settlements + 1
  ]
end
@#$#@#$#@
GRAPHICS-WINDOW
284
10
721
448
-1
-1
13.0
1
10
1
1
1
0
0
0
1
-16
16
-16
16
0
0
1
ticks
30.0

BUTTON
22
26
88
59
NIL
setup
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

INPUTBOX
844
94
941
154
max-patch-ycor
16.0
1
0
Number

INPUTBOX
845
24
941
84
max-patch-xcor
16.0
1
0
Number

INPUTBOX
741
23
834
83
min-patch-xcor
-16.0
1
0
Number

INPUTBOX
740
93
829
153
min-patch-ycor
-16.0
1
0
Number

INPUTBOX
956
66
1050
126
patch-pixel-size
13.0
1
0
Number

SWITCH
21
70
202
103
include-settlements
include-settlements
0
1
-1000

INPUTBOX
21
178
170
238
max-settlements
10.0
1
0
Number

INPUTBOX
19
253
215
313
max-households-per-settlement
5.0
1
0
Number

SWITCH
23
122
197
155
contiguous-landcover
contiguous-landcover
0
1
-1000

INPUTBOX
737
253
860
327
biomass-density
439.0
1
0
Number

TEXTBOX
873
254
1023
324
Density of biomass used in calculations (e.g. wood = 439 kg/m³). This is used to convert volume-based biomass availability to mass.
11
3.0
1

@#$#@#$#@
## WHAT IS IT?

This model simulates a simplified settlement-landscape interaction where users can define different landscape types, land covers, and rules for settlement placement. It is designed to allow flexible configuration of environmental and social parameters. Landscapes are arranged in contiguous zones.

## HOW IT WORKS

The model generates the landscape in concentric rings, starting from a randomly chosen central patch. Each landscape type is defined by the user in the landscape-types list in the setup procedure, including its name (e.g. flood-basin, levee), proportion of total land, and display color. Land covers (e.g., forest, fen) are added on top of these landscape types. Land covers are also defined by the user in the cover-types list. Users specify where and how much they occur, and how much biomass they contain.

Settlements are placed only on landscape types listed in valid-landscape-types, and only if no other settlement exists on the target patch. The number of settlements and the number of households per settlement are also user-defined in the interface.

## HOW TO USE IT

(how to use the model, including a description of each of the items in the Interface tab)

## THINGS TO NOTICE

Landscapes are generated in concentric patterns, with each type expanding outward from the previous one.

## THINGS TO TRY

Change the landscape-types list to add more types or change the proportions and colors.

Modify land-covers to simulate different ecological scenarios (e.g., denser forests, larger fen areas).

## EXTENDING THE MODEL

(suggested things to add or change in the Code tab to make the model more complicated, detailed, accurate, etc.)

## NETLOGO FEATURES

(interesting or unusual features of NetLogo that the model uses, particularly in the Code tab; or where workarounds were needed for missing features)

## RELATED MODELS

1. Joyce, J. A. (2019). Farming along the limes: Using agent-based modelling to investigate possibilities for subsistence and surplus-based agricultural production in the Lower Rhine delta between 12BCE and 270CE. [PhD-Thesis - Research and graduation internal, Vrije Universiteit Amsterdam].

2. Verhagen, P., Joyce, J., & Groenhuijzen, M. R. (Eds.). (2019). Finding the limits of the limes: Modelling demography, economy and transport on the edge of the Roman Empire (1st ed.). Springer Cham. https://doi.org/10.1007/978-3-030-04576-0

## CREDITS AND REFERENCES

1. Joyce, J. A. (2019). Farming along the limes: Using agent-based modelling to investigate possibilities for subsistence and surplus-based agricultural production in the Lower Rhine delta between 12BCE and 270CE. [PhD-Thesis - Research and graduation internal, Vrije Universiteit Amsterdam].

2. Verhagen, P., Joyce, J., & Groenhuijzen, M. R. (Eds.). (2019). Finding the limits of the limes: Modelling demography, economy and transport on the edge of the Roman Empire (1st ed.). Springer Cham. https://doi.org/10.1007/978-3-030-04576-0
@#$#@#$#@
default
true
0
Polygon -7500403 true true 150 5 40 250 150 205 260 250

airplane
true
0
Polygon -7500403 true true 150 0 135 15 120 60 120 105 15 165 15 195 120 180 135 240 105 270 120 285 150 270 180 285 210 270 165 240 180 180 285 195 285 165 180 105 180 60 165 15

arrow
true
0
Polygon -7500403 true true 150 0 0 150 105 150 105 293 195 293 195 150 300 150

box
false
0
Polygon -7500403 true true 150 285 285 225 285 75 150 135
Polygon -7500403 true true 150 135 15 75 150 15 285 75
Polygon -7500403 true true 15 75 15 225 150 285 150 135
Line -16777216 false 150 285 150 135
Line -16777216 false 150 135 15 75
Line -16777216 false 150 135 285 75

bug
true
0
Circle -7500403 true true 96 182 108
Circle -7500403 true true 110 127 80
Circle -7500403 true true 110 75 80
Line -7500403 true 150 100 80 30
Line -7500403 true 150 100 220 30

butterfly
true
0
Polygon -7500403 true true 150 165 209 199 225 225 225 255 195 270 165 255 150 240
Polygon -7500403 true true 150 165 89 198 75 225 75 255 105 270 135 255 150 240
Polygon -7500403 true true 139 148 100 105 55 90 25 90 10 105 10 135 25 180 40 195 85 194 139 163
Polygon -7500403 true true 162 150 200 105 245 90 275 90 290 105 290 135 275 180 260 195 215 195 162 165
Polygon -16777216 true false 150 255 135 225 120 150 135 120 150 105 165 120 180 150 165 225
Circle -16777216 true false 135 90 30
Line -16777216 false 150 105 195 60
Line -16777216 false 150 105 105 60

car
false
0
Polygon -7500403 true true 300 180 279 164 261 144 240 135 226 132 213 106 203 84 185 63 159 50 135 50 75 60 0 150 0 165 0 225 300 225 300 180
Circle -16777216 true false 180 180 90
Circle -16777216 true false 30 180 90
Polygon -16777216 true false 162 80 132 78 134 135 209 135 194 105 189 96 180 89
Circle -7500403 true true 47 195 58
Circle -7500403 true true 195 195 58

circle
false
0
Circle -7500403 true true 0 0 300

circle 2
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240

cow
false
0
Polygon -7500403 true true 200 193 197 249 179 249 177 196 166 187 140 189 93 191 78 179 72 211 49 209 48 181 37 149 25 120 25 89 45 72 103 84 179 75 198 76 252 64 272 81 293 103 285 121 255 121 242 118 224 167
Polygon -7500403 true true 73 210 86 251 62 249 48 208
Polygon -7500403 true true 25 114 16 195 9 204 23 213 25 200 39 123

cylinder
false
0
Circle -7500403 true true 0 0 300

dot
false
0
Circle -7500403 true true 90 90 120

face happy
false
0
Circle -7500403 true true 8 8 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Polygon -16777216 true false 150 255 90 239 62 213 47 191 67 179 90 203 109 218 150 225 192 218 210 203 227 181 251 194 236 217 212 240

face neutral
false
0
Circle -7500403 true true 8 7 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Rectangle -16777216 true false 60 195 240 225

face sad
false
0
Circle -7500403 true true 8 8 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Polygon -16777216 true false 150 168 90 184 62 210 47 232 67 244 90 220 109 205 150 198 192 205 210 220 227 242 251 229 236 206 212 183

fish
false
0
Polygon -1 true false 44 131 21 87 15 86 0 120 15 150 0 180 13 214 20 212 45 166
Polygon -1 true false 135 195 119 235 95 218 76 210 46 204 60 165
Polygon -1 true false 75 45 83 77 71 103 86 114 166 78 135 60
Polygon -7500403 true true 30 136 151 77 226 81 280 119 292 146 292 160 287 170 270 195 195 210 151 212 30 166
Circle -16777216 true false 215 106 30

flag
false
0
Rectangle -7500403 true true 60 15 75 300
Polygon -7500403 true true 90 150 270 90 90 30
Line -7500403 true 75 135 90 135
Line -7500403 true 75 45 90 45

flower
false
0
Polygon -10899396 true false 135 120 165 165 180 210 180 240 150 300 165 300 195 240 195 195 165 135
Circle -7500403 true true 85 132 38
Circle -7500403 true true 130 147 38
Circle -7500403 true true 192 85 38
Circle -7500403 true true 85 40 38
Circle -7500403 true true 177 40 38
Circle -7500403 true true 177 132 38
Circle -7500403 true true 70 85 38
Circle -7500403 true true 130 25 38
Circle -7500403 true true 96 51 108
Circle -16777216 true false 113 68 74
Polygon -10899396 true false 189 233 219 188 249 173 279 188 234 218
Polygon -10899396 true false 180 255 150 210 105 210 75 240 135 240

house
false
0
Rectangle -7500403 true true 45 120 255 285
Rectangle -16777216 true false 120 210 180 285
Polygon -7500403 true true 15 120 150 15 285 120
Line -16777216 false 30 120 270 120

leaf
false
0
Polygon -7500403 true true 150 210 135 195 120 210 60 210 30 195 60 180 60 165 15 135 30 120 15 105 40 104 45 90 60 90 90 105 105 120 120 120 105 60 120 60 135 30 150 15 165 30 180 60 195 60 180 120 195 120 210 105 240 90 255 90 263 104 285 105 270 120 285 135 240 165 240 180 270 195 240 210 180 210 165 195
Polygon -7500403 true true 135 195 135 240 120 255 105 255 105 285 135 285 165 240 165 195

line
true
0
Line -7500403 true 150 0 150 300

line half
true
0
Line -7500403 true 150 0 150 150

pentagon
false
0
Polygon -7500403 true true 150 15 15 120 60 285 240 285 285 120

person
false
0
Circle -7500403 true true 110 5 80
Polygon -7500403 true true 105 90 120 195 90 285 105 300 135 300 150 225 165 300 195 300 210 285 180 195 195 90
Rectangle -7500403 true true 127 79 172 94
Polygon -7500403 true true 195 90 240 150 225 180 165 105
Polygon -7500403 true true 105 90 60 150 75 180 135 105

plant
false
0
Rectangle -7500403 true true 135 90 165 300
Polygon -7500403 true true 135 255 90 210 45 195 75 255 135 285
Polygon -7500403 true true 165 255 210 210 255 195 225 255 165 285
Polygon -7500403 true true 135 180 90 135 45 120 75 180 135 210
Polygon -7500403 true true 165 180 165 210 225 180 255 120 210 135
Polygon -7500403 true true 135 105 90 60 45 45 75 105 135 135
Polygon -7500403 true true 165 105 165 135 225 105 255 45 210 60
Polygon -7500403 true true 135 90 120 45 150 15 180 45 165 90

sheep
false
15
Circle -1 true true 203 65 88
Circle -1 true true 70 65 162
Circle -1 true true 150 105 120
Polygon -7500403 true false 218 120 240 165 255 165 278 120
Circle -7500403 true false 214 72 67
Rectangle -1 true true 164 223 179 298
Polygon -1 true true 45 285 30 285 30 240 15 195 45 210
Circle -1 true true 3 83 150
Rectangle -1 true true 65 221 80 296
Polygon -1 true true 195 285 210 285 210 240 240 210 195 210
Polygon -7500403 true false 276 85 285 105 302 99 294 83
Polygon -7500403 true false 219 85 210 105 193 99 201 83

square
false
0
Rectangle -7500403 true true 30 30 270 270

square 2
false
0
Rectangle -7500403 true true 30 30 270 270
Rectangle -16777216 true false 60 60 240 240

star
false
0
Polygon -7500403 true true 151 1 185 108 298 108 207 175 242 282 151 216 59 282 94 175 3 108 116 108

target
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240
Circle -7500403 true true 60 60 180
Circle -16777216 true false 90 90 120
Circle -7500403 true true 120 120 60

tree
false
0
Circle -7500403 true true 118 3 94
Rectangle -6459832 true false 120 195 180 300
Circle -7500403 true true 65 21 108
Circle -7500403 true true 116 41 127
Circle -7500403 true true 45 90 120
Circle -7500403 true true 104 74 152

triangle
false
0
Polygon -7500403 true true 150 30 15 255 285 255

triangle 2
false
0
Polygon -7500403 true true 150 30 15 255 285 255
Polygon -16777216 true false 151 99 225 223 75 224

truck
false
0
Rectangle -7500403 true true 4 45 195 187
Polygon -7500403 true true 296 193 296 150 259 134 244 104 208 104 207 194
Rectangle -1 true false 195 60 195 105
Polygon -16777216 true false 238 112 252 141 219 141 218 112
Circle -16777216 true false 234 174 42
Rectangle -7500403 true true 181 185 214 194
Circle -16777216 true false 144 174 42
Circle -16777216 true false 24 174 42
Circle -7500403 false true 24 174 42
Circle -7500403 false true 144 174 42
Circle -7500403 false true 234 174 42

turtle
true
0
Polygon -10899396 true false 215 204 240 233 246 254 228 266 215 252 193 210
Polygon -10899396 true false 195 90 225 75 245 75 260 89 269 108 261 124 240 105 225 105 210 105
Polygon -10899396 true false 105 90 75 75 55 75 40 89 31 108 39 124 60 105 75 105 90 105
Polygon -10899396 true false 132 85 134 64 107 51 108 17 150 2 192 18 192 52 169 65 172 87
Polygon -10899396 true false 85 204 60 233 54 254 72 266 85 252 107 210
Polygon -7500403 true true 119 75 179 75 209 101 224 135 220 225 175 261 128 261 81 224 74 135 88 99

wheel
false
0
Circle -7500403 true true 3 3 294
Circle -16777216 true false 30 30 240
Line -7500403 true 150 285 150 15
Line -7500403 true 15 150 285 150
Circle -7500403 true true 120 120 60
Line -7500403 true 216 40 79 269
Line -7500403 true 40 84 269 221
Line -7500403 true 40 216 269 79
Line -7500403 true 84 40 221 269

wolf
false
0
Polygon -16777216 true false 253 133 245 131 245 133
Polygon -7500403 true true 2 194 13 197 30 191 38 193 38 205 20 226 20 257 27 265 38 266 40 260 31 253 31 230 60 206 68 198 75 209 66 228 65 243 82 261 84 268 100 267 103 261 77 239 79 231 100 207 98 196 119 201 143 202 160 195 166 210 172 213 173 238 167 251 160 248 154 265 169 264 178 247 186 240 198 260 200 271 217 271 219 262 207 258 195 230 192 198 210 184 227 164 242 144 259 145 284 151 277 141 293 140 299 134 297 127 273 119 270 105
Polygon -7500403 true true -1 195 14 180 36 166 40 153 53 140 82 131 134 133 159 126 188 115 227 108 236 102 238 98 268 86 269 92 281 87 269 103 269 113

x
false
0
Polygon -7500403 true true 270 75 225 30 30 225 75 270
Polygon -7500403 true true 30 75 75 30 270 225 225 270
@#$#@#$#@
NetLogo 6.4.0
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
default
0.0
-0.2 0 0.0 1.0
0.0 1 1.0 0.0
0.2 0 0.0 1.0
link direction
true
0
Line -7500403 true 150 150 90 180
Line -7500403 true 150 150 210 180
@#$#@#$#@
0
@#$#@#$#@
