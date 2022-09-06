;;; global varaibles settings
globals [
  house-counter
  died-counter
  process
  ;;; constants
  range1-search-radius-share
  range2-search-radius-share
  range3-search-radius-share
  range4-search-radius-share
  range1-initial-connections-share
  range2-initial-connections-share
  range3-initial-connections-share
  range4-initial-connections-share
  ;;; network metrics
  nw-betcen
  nw-eigcen
  nw-clocen
  nw-clucoe
  nw-mod
  pos-spread
  neg-spread
  count-spread
  count-daily-contact
  count-daily-transmission
  count-daily-transmission-pers
]

;;; breed setup
breed [people person]
breed [households household]
undirected-link-breed [connections connection]

;;; variables declaration for breeds
households-own [
  inhabitants
  tf-link?
  house
]

connections-own [
  t-prob
  l-length
  l-infected-in
  t-range
  active?
]

people-own [
  personal-id
  household-id
  my-connection-count
  my-connection-count1
  my-connection-count2
  my-connection-count3
  my-connection-count4
  initial-degree
  infected-in
  my-daily-contacts
  actual-contacts
  sec-case-count
  susceptible?
  incubation?
  prodromal?
  contag?
  recovered?
  died?
  ill-duration
  ill-duration-l
  ill-duration-p
  ill-duration-c
  death-in
  imovable-in
  died-in
  imoved-in
  stage
  movable?
  imune?
  to-infect
  stage-counter-l
  stage-counter-p
  stage-counter-c
]

patches-own [
  house?
  house-id
  household-pop
  future-settlement?
]

to setup

  ;;; main setup

  clear-all
  reset-ticks

  setup-clusters

  setup-population

  start-epidemy

  go

end

to setup-clusters

  ask patches
     [set house? false
      set future-settlement? false]

  ask n-of initial-clusters patches with [future-settlement? = false]
      [ask patches in-radius (cluster-radius-min + (random cluster-radius-max))
          [set future-settlement? true]]

end

to setup-population ;;; setup featuring demography context

  set-constants

  setup-households

  setup-people

end

to set-constants

  ;;; set constants
  set range1-search-radius-share 0.125
  set range2-search-radius-share 0.25
  set range3-search-radius-share 0.5
  set range4-search-radius-share 1

  set range1-initial-connections-share 1
  set range2-initial-connections-share 0.75
  set range3-initial-connections-share 0.5
  set range4-initial-connections-share 0.25

end

to setup-households

  ;;; create chosen number of households (slider)
  ask n-of initial-households patches with [future-settlement? = true]
      [set house? true
       set house-counter (house-counter + 1)
       set house-id house-counter
       sprout-households 1
        [set tf-link? false
         set shape "house"
         set color white
         set size 1
         set house [house-id] of patch-here]]

  ;;; create population of households based on population coefficient variable (slider)
  ask households
     [let future-id [house-id] of self
      let actual-random ((random-exponential population-coefficient) + 4)
      hatch-people actual-random
        [move-to one-of patches in-radius 2 with [future-settlement? = true]
          set household-id future-id
          set shape "person"
          set color blue
          set size 1
          set imovable-in 200
          set death-in 200
          set movable? true
          set household-id [house-id] of patch-here
          set susceptible? true
          set incubation? false
          set prodromal? false
          set contag? false
          set recovered? false
          set imune? false
          set died? false
          set stage "susceptible"
          set personal-id [who] of self]
      set household-pop actual-random]

end

to setup-people

  ;;; create links between individuals (fundamental settings for degree distribution, distance of individual contacts and transmission probability)
  ask people
    [let my-id-now [personal-id] of self
     let my-neighbor-comm1 people with [personal-id != my-id-now] in-radius (search-radius * range1-search-radius-share) ;;; agentset in range 1 (closest vicinity)
     let my-neighbor-comm2 people with [personal-id != my-id-now] in-radius (search-radius * range2-search-radius-share) ;;; agentset in range 2 (more remote individuals)
     let my-neighbor-comm3 people with [personal-id != my-id-now] in-radius (search-radius * range3-search-radius-share) ;;; agentset in range 3 (remote individuals)
     let my-neighbor-comm4 people with [personal-id != my-id-now] in-radius (search-radius * range4-search-radius-share) ;;; agentset in range 4 (individuals in maximum search radius)
     create-connections-with n-of (random (max-connections * range1-initial-connections-share)) my-neighbor-comm1 ;;; establish links in in range 1
                 [set t-prob random-normal transmission-prob-range1-mean transmission-prob-range1-stddev ;;; set link transmission probability in range 1
                  set t-range 1]
     create-connections-with n-of (random (max-connections * range2-initial-connections-share)) my-neighbor-comm2 ;;; establish links in range 2
                 [set t-prob random-normal transmission-prob-range2-mean transmission-prob-range2-stddev ;;; set link transmission probability in range 2
                  set t-range 2]
     create-connections-with n-of (random (max-connections * range3-initial-connections-share)) my-neighbor-comm3 ;;; establish links in range 3
                 [set t-prob random-normal transmission-prob-range3-mean transmission-prob-range3-stddev ;;; set link transmission probability in range 3
                  set t-range 3]
     create-connections-with n-of (random (max-connections * range4-initial-connections-share)) my-neighbor-comm4 ;;; establish links in range 4
                 [set t-prob random-normal transmission-prob-range4-mean transmission-prob-range4-stddev ;;; set link transmission probability in range 4
                  set t-range 4]
      set my-connection-count count my-connections
      set my-connection-count1 count my-connections with [t-range = 1]
      set my-connection-count2 count my-connections with [t-range = 2]
      set my-connection-count3 count my-connections with [t-range = 3]
      set my-connection-count4 count my-connections with [t-range = 4]
     set initial-degree my-connection-count]

  ask links
     [set active? true
      set l-length link-length
      set hidden? true]
end

to start-epidemy

  ;;; setup first infected individuals of the household nearest to the centre of the environment

  ask min-one-of households [distance patch 0 0]
      [let my-id [house] of self
        ask min-n-of initial-infected people [distance myself]
           [set incubation? true
            set stage "incubation"
            set stage-counter-l get-stage-duration "latent"]]
end

to go

  ;;; iterative call of the processes connected with epidemiological development and calculation of variables

  set count-daily-contact 0
  set count-daily-transmission 0
  set count-daily-transmission-pers 0

  ;;; to hide links of disease transmission (red) older than 100 iterations
  ask connections
      [if (l-infected-in < (ticks - 100))
        [set hidden? true]]

  ;;; to run simulation only any active stage of disease is present
  ifelse any? people with [incubation? = true or prodromal? = true or contag? = true]
    [infection-spread
     disease-development]
    [stop]

  ;;; update count of active links amongst suspectible individuals
  ask people with [susceptible? = true]
        [set my-connection-count count my-connections with [active? = true]]

  tick
end

to infection-spread

  ;;; procedures to calculate disease transmission between linked individuals

  set process "infection spread"

  ;;; to ask all respective agents
  if any? people with [contag? = true and movable? = true and any? connections with [active? = true]]
     [set count-daily-transmission-pers count people with [contag? = true and movable? = true and any? connections with [active? = true]]
      ask people with [contag? = true and movable? = true and any? connections with [active? = true]]
        [
          ;;; set amount of daily contacts to perform
          ifelse my-connection-count > max-daily-contacts
              [set my-daily-contacts max-daily-contacts]
              [set my-daily-contacts random my-connection-count]

          ;;; calculate each of daily contact and disease transmission probability
          repeat random (my-daily-contacts)
              [let present-my-daily-contacts my-connection-count
               set count-spread (count-spread + 1)
               set count-daily-contact (count-daily-contact + 1)
               set my-connection-count count my-connections with [active? = true]
               let my-connection one-of my-connections with [active? = true]
               if my-connection-count > 0
                  [ask my-connection
                      [ifelse (random-float 1) * (0.1 + (random present-my-daily-contacts)) < (spread-rate / 100) * t-prob
                          [set pos-spread (pos-spread + 1)
                           set count-daily-transmission (count-daily-transmission + 1)
                           set hidden? false
                           set l-infected-in ticks
                           set color red
                           ask other-end
                               [if susceptible? = true
                                   [set incubation? true
                                    set stage "incubation"
                                    set stage-counter-l get-stage-duration "latent"
                                    set susceptible? false
                                    set infected-in ticks]]
                                    ask other-end
                                          [set sec-case-count (sec-case-count + 1)]]
                          [set neg-spread (neg-spread + 1)]]]
        set my-connection-count count my-connections with [active? = true]]]]
end

to disease-development

  ;;; procedures to calculate development of the disease in individual stages - Susceptible-Latent(Incubation)-Prodromal-Contagious-Recovered/Died

  set process "disease development"

  ask people with [contag? = true]
    [set stage-counter-c (stage-counter-c - 1)
     set ill-duration (ill-duration + 1)
     set ill-duration-c (ill-duration-c + 1)
     if death-in > 0 and death-in < 100
          [set death-in (death-in - 1)]
     if imovable-in > 0 and imovable-in < 100
            [set imovable-in (imovable-in - 1)]
     if stage-counter-c <= 0
        [set contag? false
         set size 2
         set color red
         set recovered? true
         set stage "recovered"
         set color orange
         set size 1
         set contag? false
         ask my-connections
            [set active? false]]]

  ask people with [prodromal? = true]
    [set stage-counter-p (stage-counter-p - 1)
     set ill-duration (ill-duration + 1)
     set ill-duration-p (ill-duration-p + 1)
     if stage-counter-p <= 0
        [set stage-counter-c get-stage-duration "contagious"
         let my-random random int stage-counter-c
         set prodromal? false
         set contag? true
         set stage "contagious"
         if random-float 1 < mortality-rate / 100
                    [set death-in (my-random / 2)]
         set imovable-in (my-random * 2)
         set color yellow
         set size 2]]

  ask people with [incubation? = true]
    [set stage-counter-l (stage-counter-l - 1)
     set ill-duration (ill-duration + 1)
     set ill-duration-l (ill-duration-l + 1)
     if stage-counter-l <= 0
        [set stage-counter-p get-stage-duration "prodromal"
         set incubation? false
         set prodromal? true
         set stage "prodromal"
         set color green
         set size 2]]

  ask people with [contag? = true and death-in <= 0]
      [set contag? false
       set died? true
       set stage "death"
       set died-in ill-duration
       set color brown
       set size 1
       ask my-connections
             [set active? false]]

  ;;; people with deveoped contagious stage cease their movement
  ask people with [contag? = true and imovable-in <= 0]
        [set movable? false
         set imoved-in ill-duration]
end

to-report get-stage-duration [ stageName ]

  if (stageName = "latent")
  [ report round random-normal duration-latent-mean duration-latent-stddev ]

  if (stageName = "prodromal")
  [ report round random-normal duration-prodromal-mean duration-prodromal-stddev ]

  if (stageName = "contagious")
  [ report round random-normal duration-contagious-mean duration-contagious-stddev ]

  error (word "'" stageName "' is not a valid stage name.")

end
@#$#@#$#@
GRAPHICS-WINDOW
5
10
972
978
-1
-1
4.7711443
1
10
1
1
1
0
0
0
1
-100
100
-100
100
1
1
1
ticks
30.0

BUTTON
976
10
1031
43
Setup
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

BUTTON
1034
10
1089
43
GO
go
T
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

SLIDER
975
65
1101
98
initial-households
initial-households
50
2000
1000.0
10
1
NIL
HORIZONTAL

MONITOR
1361
10
1424
55
Population
count people with [died? = false]
17
1
11

PLOT
973
615
1482
735
Epidemics development
NIL
NIL
0.0
10.0
0.0
10.0
true
true
"" ""
PENS
"Prodromal" 1.0 0 -7500403 true "" "plot count people with [prodromal? = true]"
"Contag" 1.0 0 -2674135 true "" "plot count people with [contag? = true]"
"Incubation" 1.0 0 -6459832 true "" "plot count people with [incubation? = true]"
"Infected" 1.0 0 -13345367 true "" "plot count people with [incubation? = true or contag? = true or prodromal? = true]"

SLIDER
1043
398
1217
431
spread-rate
spread-rate
0
100
25.0
1
1
%
HORIZONTAL

SLIDER
1306
317
1480
350
mortality-rate
mortality-rate
0
100
20.0
1
1
%
HORIZONTAL

MONITOR
1361
56
1411
101
latent
count people with [incubation? = true]
17
1
11

MONITOR
1413
56
1473
101
prodromal
count people with [prodromal? = true]
17
1
11

MONITOR
1475
56
1539
101
contagious
count people with [contag? = true]
17
1
11

MONITOR
1541
56
1601
101
recovered
count people with [recovered? = true]
17
1
11

PLOT
1484
679
1757
827
Household population size
NIL
NIL
2.0
30.0
0.0
10.0
true
false
"" ""
PENS
"default" 1.0 1 -16777216 true "" "histogram [household-pop] of patches with [house? = true]"

MONITOR
1361
102
1418
147
Count
count links
17
1
11

MONITOR
1426
10
1484
55
dens/km2
count people / 400
2
1
11

MONITOR
1603
56
1667
101
susceptible
count people with [susceptible? = true]
1
1
11

MONITOR
1092
10
1221
55
Actual process
process
17
1
11

SLIDER
974
300
1101
333
initial-infected
initial-infected
1
10
10.0
1
1
NIL
HORIZONTAL

BUTTON
1664
158
1736
191
Hide links
ask links\n  [set hidden? true]
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

MONITOR
1486
10
1536
55
Died%
count people with [died? = true] / (count people / 100)
1
1
11

BUTTON
1664
192
1736
225
Unhide links
ask links\n  [set hidden? false]
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

BUTTON
1654
228
1753
261
Hide recovered
ask people with [recovered? = true or died? = true]\n   [set hidden? true]
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

PLOT
975
736
1484
856
Population
NIL
NIL
0.0
10.0
0.0
10.0
true
true
"" ""
PENS
"Died" 1.0 0 -11221820 true "" "plot count people with [died? = true]"
"Recovered" 1.0 0 -955883 true "" "plot count people with [recovered? = true]"
"Susceptible" 1.0 0 -7500403 true "" "plot count people with [susceptible? = true]"
"Total" 1.0 0 -16448764 true "" "plot count people - count people with [died? = true]"

MONITOR
1538
10
1588
55
Sus%
count people with [susceptible? = true] / (count people / 100)
1
1
11

BUTTON
1654
262
1753
295
Unhide recovered
ask people with [recovered? = true or died? = true]\n   [set hidden? false]
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

SLIDER
975
99
1101
132
population-coefficient
population-coefficient
1
5
3.0
1
1
NIL
HORIZONTAL

SLIDER
973
232
1100
265
search-radius
search-radius
10
200
100.0
10
1
NIL
HORIZONTAL

MONITOR
1417
102
1474
147
Degree
mean [my-connection-count] of people
2
1
11

SLIDER
975
133
1101
166
initial-clusters
initial-clusters
5
50
30.0
5
1
NIL
HORIZONTAL

SLIDER
975
167
1101
200
cluster-radius-min
cluster-radius-min
1
cluster-radius-max
5.0
1
1
NIL
HORIZONTAL

PLOT
1485
531
1757
677
Degree distribution
NIL
NIL
0.0
30.0
0.0
1.0
true
false
"" ""
PENS
"default" 1.0 1 -16777216 true "" "histogram [my-connection-count] of people"

MONITOR
1669
56
1719
101
died
count people with [died? = true]
17
1
11

MONITOR
1528
102
1601
147
MEAN lenght
mean [l-length * 0.1] of connections
1
1
11

PLOT
1486
370
1757
528
Link lenght (km)
NIL
NIL
0.0
5.0
0.0
10.0
true
false
"" ""
PENS
"default" 0.1 1 -16777216 true "" "histogram [l-length * 0.1] of links"

SLIDER
974
334
1101
367
max-daily-contacts
max-daily-contacts
5
100
30.0
5
1
NIL
HORIZONTAL

SLIDER
1315
180
1474
213
duration-latent-mean
duration-latent-mean
1
20
12.0
1
1
NIL
HORIZONTAL

SLIDER
1316
211
1476
244
duration-prodromal-mean
duration-prodromal-mean
1
20
3.0
1
1
NIL
HORIZONTAL

SLIDER
1316
243
1475
276
duration-contagious-mean
duration-contagious-mean
1
20
9.0
1
1
NIL
HORIZONTAL

MONITOR
1590
10
1640
55
MEAN R
mean [sec-case-count] of people + 1
3
1
11

PLOT
1484
828
1756
978
Link transmission probability
NIL
NIL
0.0
2.0
0.0
10.0
true
false
"" ""
PENS
"default" 0.1 1 -16777216 true "" "histogram [t-prob] of links"

MONITOR
1734
10
1811
55
Spread count
count-spread
17
1
11

MONITOR
1813
10
1867
55
Positive
pos-spread
17
1
11

MONITOR
1921
10
1975
55
Negative
neg-spread
17
1
11

MONITOR
1869
10
1919
55
%
pos-spread / (count-spread / 100)
2
1
11

MONITOR
1976
10
2026
55
%
neg-spread / (count-spread / 100)
2
1
11

SLIDER
1472
179
1644
212
duration-latent-stddev
duration-latent-stddev
1
10
3.0
0.5
1
NIL
HORIZONTAL

SLIDER
1474
211
1646
244
duration-prodromal-stddev
duration-prodromal-stddev
1
10
2.0
0.5
1
NIL
HORIZONTAL

SLIDER
1475
242
1650
275
duration-contagious-stddev
duration-contagious-stddev
1
10
3.0
0.5
1
NIL
HORIZONTAL

PLOT
975
857
1482
977
Infected contacts
NIL
NIL
0.0
10.0
0.0
5.0
true
true
"" ""
PENS
"Contacts" 1.0 0 -16777216 true "" "if any? people with [contag? = true] [plot count-daily-contact]"

PLOT
1758
80
2024
230
Whole illness
NIL
NIL
0.0
50.0
0.0
10.0
true
false
"" ""
PENS
"default" 1.0 1 -16777216 true "" "histogram [ill-duration] of people with [ill-duration > 0]"

PLOT
1758
232
2024
377
Latent
NIL
NIL
0.0
25.0
0.0
10.0
true
false
"" ""
PENS
"default" 1.0 1 -16777216 true "" "histogram [ill-duration-l] of people with [ill-duration-l > 0]"

PLOT
1759
378
2026
528
Prodromal
NIL
NIL
0.0
20.0
0.0
10.0
true
false
"" ""
PENS
"default" 1.0 1 -16777216 true "" "histogram [ill-duration-p] of people with [ill-duration-p > 0]"

PLOT
1759
531
2026
679
Contagious
NIL
NIL
0.0
20.0
0.0
10.0
true
false
"" ""
PENS
"default" 1.0 1 -16777216 true "" "histogram [ill-duration-c] of people with [ill-duration-c > 0]"

PLOT
1759
680
2026
826
Died in
NIL
NIL
0.0
50.0
0.0
10.0
true
false
"" ""
PENS
"default" 1.0 1 -16777216 true "" "histogram [died-in] of people with [died? = true and died-in > 0]"

PLOT
1759
828
2025
978
Imoved in
NIL
NIL
0.0
50.0
0.0
10.0
true
false
"" ""
PENS
"default" 1.0 1 -16777216 true "" "histogram [imoved-in] of people with [imoved-in > 0]"

MONITOR
1476
102
1526
147
STD
standard-deviation [my-connection-count] of people
2
1
11

TEXTBOX
1109
69
1225
97
initial count of households
11
0.0
1

TEXTBOX
1109
102
1220
130
household size variance coefficient
11
0.0
1

TEXTBOX
1110
136
1222
164
initial count of clusters/settlements
11
0.0
1

TEXTBOX
1109
186
1218
214
Minimum/maximum cluster radius
11
0.0
1

TEXTBOX
1109
235
1233
277
maximum search distance to establish links
11
0.0
1

SLIDER
973
266
1100
299
max-connections
max-connections
1
20
5.0
1
1
NIL
HORIZONTAL

TEXTBOX
1371
159
1558
177
DISEASE STAGE DURATION SETTINGS
11
0.0
1

TEXTBOX
1657
124
1770
156
VISIBILITY OF LINKS/RECOVERED
11
0.0
1

TEXTBOX
1286
17
1336
45
Basic properties
11
0.0
1

TEXTBOX
1285
63
1353
93
Disease stage count
11
0.0
1

TEXTBOX
1285
116
1381
134
Link properties
11
0.0
1

TEXTBOX
1258
187
1304
205
latent
11
0.0
1

TEXTBOX
1258
166
1313
184
PERIOD
11
0.0
1

TEXTBOX
1258
220
1309
238
prodromal
11
0.0
1

TEXTBOX
1258
252
1314
270
contagious
11
0.0
1

TEXTBOX
1247
319
1302
347
mortality rate
11
0.0
1

TEXTBOX
984
401
1043
431
spread probability
11
0.0
1

TEXTBOX
1109
311
1219
329
number of initial cases
11
0.0
1

TEXTBOX
1109
338
1220
380
maximum number of daily contacts
11
0.0
1

TEXTBOX
1109
265
1253
307
maximum number of connections per distance range
11
0.0
1

TEXTBOX
1760
61
1952
89
DISEASE STAGE DURATION (DAYS)
11
0.0
1

MONITOR
1537
318
1587
363
1
count connections with [t-range = 1]
17
1
11

MONITOR
1588
318
1638
363
2
count connections with [t-range = 2]
17
1
11

MONITOR
1639
318
1689
363
3
count connections with [t-range = 3]
17
1
11

MONITOR
1690
318
1747
363
4
count connections with [t-range = 4]
17
1
11

TEXTBOX
1537
298
1758
326
LINK COUNT IN SEARCH DISTANCE RANGES
11
0.0
1

TEXTBOX
986
49
1091
67
MAIN SETTINGS
11
0.0
1

SLIDER
973
199
1101
232
cluster-radius-max
cluster-radius-max
cluster-radius-min + 1
100
10.0
1
1
NIL
HORIZONTAL

TEXTBOX
1070
380
1220
398
TRANSMISSION RATES
11
0.0
1

SLIDER
989
438
1227
471
transmission-prob-range1-mean
transmission-prob-range1-mean
0
1
1.0
0.001
1
NIL
HORIZONTAL

SLIDER
1228
438
1466
471
transmission-prob-range1-stddev
transmission-prob-range1-stddev
0
1
0.25
0.001
1
NIL
HORIZONTAL

SLIDER
989
471
1227
504
transmission-prob-range2-mean
transmission-prob-range2-mean
0
1
0.5
0.001
1
NIL
HORIZONTAL

SLIDER
1228
471
1466
504
transmission-prob-range2-stddev
transmission-prob-range2-stddev
0
1
0.25
0.001
1
NIL
HORIZONTAL

SLIDER
990
503
1228
536
transmission-prob-range3-mean
transmission-prob-range3-mean
0
1
0.25
0.001
1
NIL
HORIZONTAL

SLIDER
1229
504
1467
537
transmission-prob-range3-stddev
transmission-prob-range3-stddev
0
1
0.25
0.001
1
NIL
HORIZONTAL

SLIDER
991
537
1229
570
transmission-prob-range4-mean
transmission-prob-range4-mean
0
1
0.125
0.001
1
NIL
HORIZONTAL

SLIDER
1229
537
1467
570
transmission-prob-range4-stddev
transmission-prob-range4-stddev
0
1
0.25
0.001
1
NIL
HORIZONTAL

@#$#@#$#@
## WHAT IS IT?

(a general understanding of what the model is trying to show or explain)

## HOW IT WORKS

(what rules the agents use to create the overall behavior of the model)

## HOW TO USE IT

(how to use the model, including a description of each of the items in the Interface tab)

## THINGS TO NOTICE

(suggested things for the user to notice while running the model)

## THINGS TO TRY

(suggested things for the user to try to do (move sliders, switches, etc.) with the model)

## EXTENDING THE MODEL

(suggested things to add or change in the Code tab to make the model more complicated, detailed, accurate, etc.)

## NETLOGO FEATURES

(interesting or unusual features of NetLogo that the model uses, particularly in the Code tab; or where workarounds were needed for missing features)

## RELATED MODELS

(models in the NetLogo Models Library and elsewhere which are of related interest)

## CREDITS AND REFERENCES

(a reference to the model's URL on the web if it has one, as well as any other necessary credits, citations, and links)
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
NetLogo 6.2.2
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
