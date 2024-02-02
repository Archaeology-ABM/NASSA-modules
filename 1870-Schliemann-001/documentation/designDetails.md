# Design details

This module takes the strength of two armies, one aggressor and another defender, and calculates the level of destruction of the defenders' city. 

## Inputs

Four input variables or parameters are required:
- Strength of the attacker's army
- Strength of the defender's army
- Destruction rate modulating how fast the city looses its health during the war
- Health of the defender's city, before the war

## Output

- Health of the defender's city, after the war

## Core algorithm

The destructive effect over the defenders' city is proportional to the two contending strengths and a constant rate per unit of strength of the aggressor matched by the defender. The specific mathematical formulation is:

$$warEffect=-destructionRate*\frac{(attackerStrength)^2}{defenderStrength} $$