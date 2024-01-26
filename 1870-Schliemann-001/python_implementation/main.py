"""Python implementation of TroyDestroy"""
from Army import Army
from City import City

# input
GREEKS_STRENGTH = 100
TROJANS_STRENGTH = 50
DESTRUCTION_RATE = 0.42

TROY_HEALTH = 100

# initialise
greeks = Army(GREEKS_STRENGTH)

trojans = Army(TROJANS_STRENGTH)

troy = City(TROY_HEALTH)

print("Troy health before war: " + str(troy.health))

# algorithm execution
troy.resolve_war(GREEKS_STRENGTH, TROJANS_STRENGTH, DESTRUCTION_RATE)

# output
print("Troy health after war: " + str(troy.health))
