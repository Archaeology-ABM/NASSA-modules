class City:
    """Class representing the city under siege"""

    def __init__(self, health):
        self.health = health

    def get_effect_of_war(self, aggressor_strength, defender_strength, destruction_rate):
        """Return the destruction level based on army strengths and a destruction rate"""
        return max(0, (self.health - destruction_rate * (aggressor_strength ** 2) / defender_strength))
    
    def resolve_war(self, aggressor_strength, defender_strength, destruction_rate):
        """Resolve the destruction level based on army strengths and a destruction rate and update city health"""
        self.health = self.get_effect_of_war(aggressor_strength, defender_strength, destruction_rate)
