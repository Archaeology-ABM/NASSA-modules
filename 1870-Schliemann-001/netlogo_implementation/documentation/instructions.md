# Instructions

## Version without agents

1. Select input values in the interface:
   1. `par_greeks-strength`, `par_trojans-strength`: the strength of the contending armies (if could represent number of soldiers, units, etc). The interface sliders allow for 0 to 100, but this is not required by design.
   2. `par_destruction-rate`: this is a multiplier rate expressing how many much attackers strength, weighted in relation to the defenders strength, is necessary to decrease one unit of the city health.
2. Press "setup". Observe that a default value for `troy-health` is assigned in code (`init-troy-health`).
3. Press "resolve-trojan-war".
4. Observe change in `troy-health`

![](TroyDestroy%20interface.png)

## Version with agents

1. Select input values in the interface:
   1. `par_greeks-strength`, `par_trojans-strength`: the strength of the contending armies (if could represent number of soldiers, units, etc). The interface sliders allow for 0 to 100, but this is not required by design.
   2. `par_destruction-rate`: this is a multiplier rate expressing how many much attackers strength, weighted in relation to the defenders strength, is necessary to decrease one unit of the city health.
2. Press "setup".
3. Press "resolve-trojan-war".
4. Observe change in `troy-health`

![](TroyDestroy_agents%20interface.png)
