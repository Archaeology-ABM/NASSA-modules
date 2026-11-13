############################
# Epidemic Network - version 01
# by João Messias Sousa da Silva (2026)
#
# Python implementation of NASSA module 2022-Vlach-001:
#   Vlach, M. (2022). The Antonine Plague: Evaluation of its Impact through
#   Epidemiological Modelling. In Brughmans, T. & Wilson, A. (eds.),
#   Simulating Roman Economies: Theories, Methods, and Computational Models.
#   Oxford University Press, pp. 69-108.
#   https://doi.org/10.1093/oso/9780192857828.003.0003
#
# Module repository:
#   https://github.com/Archaeology-ABM/NASSA-modules/tree/main/2022-Vlach-001
#
# Replicates the following NetLogo procedures in Python:
#   setup-clusters        : create clustered settlement point candidates on the landscape
#   setup-population      : place households and people at settlement points
#   setup-people-network  : build a distance-stratified social network between people
#   create-link-with      : create a single undirected social link with a transmission probability
#   start-epidemic        : seed initial infected cases near the geographic centre
#   go                    : advance the simulation by one tick
#   infection-spread      : transmit disease along active network links
#   disease-development   : advance each person through the SEIRD disease stages
#   get-stage-duration    : sample a disease-stage duration from a normal distribution
#   active-connections-of : return active social links involving a given person
#   deactivate-connections: deactivate all links of a recovered or dead person
#   distance              : Euclidean distance between two agents
#   record-stats          : collect per-tick population counts and contact statistics
#   go loop               : repeat go() for up to MAX_TICKS or until the epidemic ends
#   person-color          : map a person's disease stage to a matplotlib display colour
#   plot-model (visualise): spatial map of agents with recent transmission links
#   plot-histograms       : dashboard of 10 simulation-result distributions
#
# Dependencies: numpy >= 1.20, networkx >= 2.0, matplotlib >= 3.0
############################

import pathlib
import random
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt


###############################################################################
##### Global constants (model parameters) ####################################
###############################################################################

# Random seed used to initialise both Python's built-in random module and NumPy's
# random generator, ensuring reproducible runs across platforms.
SEED = 123

# ---- Settlement and population setup ----------------------------------------

# Number of households placed on the landscape during setup.
INITIAL_HOUSEHOLDS = 1000

# Mean of the exponential distribution used to sample household size offset;
# actual household size = int(Exponential(POPULATION_COEFFICIENT)) + 4.
POPULATION_COEFFICIENT = 3.0

# Number of geographic cluster centres generated during setup-clusters.
INITIAL_CLUSTERS = 30

# Minimum and maximum cluster radius (in world units);
# each cluster's radius is sampled uniformly from [CLUSTER_RADIUS_MIN, CLUSTER_RADIUS_MAX].
CLUSTER_RADIUS_MIN = 5
CLUSTER_RADIUS_MAX = 10

# ---- Social network parameters ----------------------------------------------

# Maximum spatial search distance (world units) used to identify candidate
# neighbours when building the social network.  Divided by range fractions
# (see RANGE_SEARCH_RADIUS_SHARE) to define four distance rings.
SEARCH_RADIUS = 100

# Maximum number of connections a person can form per distance range;
# actual count is sampled uniformly from [0, MAX_CONNECTIONS * range_share].
MAX_CONNECTIONS = 5

# Upper bound on the number of social contacts a contagious person can
# activate on a single tick; caps overly connected individuals.
MAX_DAILY_CONTACTS = 30

# ---- Epidemic seeding -------------------------------------------------------

# Number of people placed into the incubation stage at tick 0 (index cases),
# selected as those closest to the household nearest the geographic centre.
INITIAL_INFECTED = 10

# ---- Disease transmission ---------------------------------------------------

# Probability that a contact event results in a transmission attempt,
# expressed as a percentage (divided by 100 when applied).
# Replicates the NetLogo 'spread-rate' slider.
SPREAD_RATE = 25.0

# Probability that a contagious person dies before recovering,
# expressed as a percentage (divided by 100 when applied).
# Replicates the NetLogo 'mortality-rate' slider.
MORTALITY_RATE = 20.0

# Mean and standard deviation of the normally distributed per-link
# transmission probability for each of the four distance ranges.
# Range 1 (closest) has the highest probability; range 4 (farthest) the lowest.
TRANSMISSION_PROB_RANGE1_MEAN   = 1.0
TRANSMISSION_PROB_RANGE1_STDDEV = 0.25

TRANSMISSION_PROB_RANGE2_MEAN   = 0.5
TRANSMISSION_PROB_RANGE2_STDDEV = 0.25

TRANSMISSION_PROB_RANGE3_MEAN   = 0.25
TRANSMISSION_PROB_RANGE3_STDDEV = 0.25

TRANSMISSION_PROB_RANGE4_MEAN   = 0.125
TRANSMISSION_PROB_RANGE4_STDDEV = 0.25

# ---- Disease stage durations ------------------------------------------------

# Mean and standard deviation (in ticks) of the latent (incubation) stage,
# sampled from a normal distribution (min. 1 tick).
DURATION_LATENT_MEAN   = 12
DURATION_LATENT_STDDEV = 3

# Mean and standard deviation (in ticks) of the prodromal stage.
DURATION_PRODROMAL_MEAN   = 3
DURATION_PRODROMAL_STDDEV = 2

# Mean and standard deviation (in ticks) of the contagious stage.
DURATION_CONTAGIOUS_MEAN   = 9
DURATION_CONTAGIOUS_STDDEV = 3

# ---- World and simulation control -------------------------------------------

# Side length of the square landscape (world units); agents are placed within
# [-WORLD_SIZE/2, WORLD_SIZE/2] on both axes.
WORLD_SIZE = 201

# Maximum number of ticks the simulation runs before stopping, even if the
# epidemic has not yet ended naturally.
MAX_TICKS = 300

# ---- Range fraction look-up tables ------------------------------------------

# Fraction of SEARCH_RADIUS that defines each distance ring boundary.
# Range 1 (innermost) = 12.5 %, range 4 (outermost) = 100 % of SEARCH_RADIUS.
RANGE_SEARCH_RADIUS_SHARE = {
    1: 0.125,
    2: 0.25,
    3: 0.5,
    4: 1.0,
}

# Fraction of MAX_CONNECTIONS used as the upper bound for link count
# sampling in each distance ring.  Closer ranges allow more connections.
RANGE_INITIAL_CONNECTIONS_SHARE = {
    1: 1.0,
    2: 0.75,
    3: 0.5,
    4: 0.25,
}


###############################################################################
##### Data structures #########################################################
###############################################################################

@dataclass
class Household:
    '''
    Represents a single household (settlement point) on the landscape.

    Attributes:
        id           : int  -- unique household identifier
        x            : float -- x-coordinate in world units
        y            : float -- y-coordinate in world units
        inhabitants  : List[int] -- list of person IDs belonging to this household
    '''
    id: int
    x: float
    y: float
    inhabitants: List[int] = field(default_factory=list)


@dataclass
class Person:
    '''
    Represents a single person (agent) in the simulation.

    Attributes (identity and location):
        id           : int   -- unique person identifier
        household_id : int   -- ID of the household this person belongs to
        x            : float -- x-coordinate (offset from household position)
        y            : float -- y-coordinate (offset from household position)

    Attributes (network):
        my_connection_count : int -- number of social links (degree) after setup
        initial_degree      : int -- copy of degree at time of setup (for reporting)

    Attributes (disease state flags):
        susceptible : bool -- True if the person has not yet been infected
        incubation  : bool -- True during the latent (exposed) stage
        prodromal   : bool -- True during the prodromal (pre-contagious) stage
        contag      : bool -- True while the person is contagious
        recovered   : bool -- True after recovery
        died        : bool -- True if the person died from the disease

    Attributes (mobility):
        movable : bool -- False once the person becomes immobile due to severe illness

    Attributes (tracking):
        infected_in       : int   -- tick when infection occurred (-1 = not infected)
        sec_case_count    : int   -- number of times this person has been exposed
        ill_duration      : int   -- total ticks spent ill
        ill_duration_l    : int   -- ticks spent in the latent stage
        ill_duration_p    : int   -- ticks spent in the prodromal stage
        ill_duration_c    : int   -- ticks spent in the contagious stage
        death_in          : float -- countdown timer to death (if mortality triggered)
        imovable_in       : float -- countdown timer to immobility
        died_in           : int   -- ill_duration at time of death (-1 = alive)
        imoved_in         : int   -- ill_duration at time of immobility onset (-1 = still mobile)

    Attributes (stage label):
        stage : str -- human-readable current stage label

    Attributes (stage countdown timers):
        stage_counter_l : int -- remaining ticks in the latent stage
        stage_counter_p : int -- remaining ticks in the prodromal stage
        stage_counter_c : int -- remaining ticks in the contagious stage
    '''
    id: int
    household_id: int
    x: float
    y: float

    my_connection_count: int = 0
    initial_degree: int = 0

    susceptible: bool = True
    incubation: bool = False
    prodromal: bool = False
    contag: bool = False
    recovered: bool = False
    died: bool = False

    movable: bool = True

    infected_in: int = -1
    sec_case_count: int = 0

    ill_duration: int = 0
    ill_duration_l: int = 0
    ill_duration_p: int = 0
    ill_duration_c: int = 0

    death_in: float = 200
    imovable_in: float = 200
    died_in: int = -1
    imoved_in: int = -1

    stage: str = "susceptible"

    stage_counter_l: int = 0
    stage_counter_p: int = 0
    stage_counter_c: int = 0


@dataclass
class Connection:
    '''
    Represents an undirected social link between two people.

    Attributes:
        a           : int   -- ID of the first person
        b           : int   -- ID of the second person
        t_prob      : float -- per-contact transmission probability (sampled at setup)
        t_range     : int   -- distance range category (1 = closest, 4 = farthest)
        active      : bool  -- False after either endpoint recovers or dies
        infected_in : int   -- tick on which transmission occurred (-9999 = never)
    '''
    a: int
    b: int
    t_prob: float
    t_range: int
    active: bool = True
    infected_in: int = -9999


###############################################################################
##### Main model class ########################################################
###############################################################################

class EpidemicModel:
    '''
    Python reimplementation of NASSA module 2022-Vlach-001 (Vlach, M. 2022.
    The Antonine Plague: Evaluation of its Impact through Epidemiological Modelling).

    Simulates the spatial spread of an infectious disease through a socially
    connected population distributed in clustered settlements.  The model
    replicates the agent-based epidemic network originally implemented in NetLogo.

    Attributes:

    tick : int
        Current simulation tick (day).  Starts at 0, incremented by go().

    house_counter : int
        Running counter used to assign unique IDs to Household objects.

    households : Dict[int, Household]
        Map from household ID to Household object.

    people : Dict[int, Person]
        Map from person ID to Person object.

    connections : Dict[Tuple[int, int], Connection]
        Map from sorted (a, b) person-ID pair to Connection object.
        Keyed by sorted tuples to ensure each undirected link is stored once.

    graph : networkx.Graph
        Mirror of the social network structure; used for efficient degree queries
        via graph.degree().  Does not store connection metadata.

    future_settlement_points : List[Tuple[float, float]]
        Candidate (x, y) positions generated by setup_clusters(); sampled during
        setup_population() to place households.

    stats : Dict[str, List]
        Per-tick time series of population counts and contact statistics.
        Keys: 'tick', 'susceptible', 'incubation', 'prodromal', 'contagious',
              'recovered', 'died', 'infected', 'daily_contacts', 'daily_transmissions'.

    Methods:

    setup()
    setup_clusters()
    setup_population()
    setup_people_network()
    create_connection(a, b, range_id)
    start_epidemic()
    go()
    infection_spread()
    disease_development()
    get_stage_duration(stage_name)
    active_connections_of(person_id)
    deactivate_connections(person_id)
    distance(a, b)
    record_stats(daily_contacts, daily_transmissions)
    run()
    '''

    def __init__(self):
        '''
        Initialise the model with empty collections and seed both random generators.

        Seeding both random and numpy.random guarantees that all stochastic
        operations (Python random module and NumPy distributions) produce
        the same sequence across runs with the same SEED.
        '''
        ### seed Python's built-in random module (used for sampling and choices)
        random.seed(SEED)
        ### seed NumPy's random generator (used for normal and exponential distributions)
        np.random.seed(SEED)

        ### simulation clock starts at tick 0
        self.tick = 0
        ### running counter for assigning unique household IDs
        self.house_counter = 0

        ### empty agent and connection stores
        self.households: Dict[int, Household] = {}
        self.people: Dict[int, Person] = {}
        ### keyed by sorted (a, b) tuples so each undirected link is stored exactly once
        self.connections: Dict[Tuple[int, int], Connection] = {}

        ### NetworkX graph mirrors the social network for efficient degree queries
        ### (undirected because social links are symmetric)
        self.graph = nx.Graph()
        ### candidate positions populated by setup_clusters(), consumed by setup_population()
        self.future_settlement_points = []

        ### per-tick statistics collector
        self.stats = {
            "tick":                [],
            "susceptible":         [],
            "incubation":          [],
            "prodromal":           [],
            "contagious":          [],
            "recovered":           [],
            "died":                [],
            "infected":            [],
            "daily_contacts":      [],
            "daily_transmissions": [],
        }

    ###########################################################################
    ##### Setup methods #######################################################
    ###########################################################################

    def setup(self):
        '''
        Full model initialisation: clusters → population → epidemic seed → record tick-0 stats.

        Replicates the NetLogo 'setup' procedure.
        '''
        ### generate cluster candidate points, place households and people,
        ### then seed the epidemic and capture the initial state
        self.setup_clusters()
        self.setup_population()
        self.start_epidemic()
        self.record_stats()

    def setup_clusters(self):
        '''
        Generate candidate settlement positions distributed in INITIAL_CLUSTERS
        geographic clusters.

        For each cluster a centre is chosen uniformly within the world bounds.
        A radius is drawn from [CLUSTER_RADIUS_MIN, CLUSTER_RADIUS_MIN + CLUSTER_RADIUS_MAX].
        200 candidate points are scattered uniformly inside each cluster circle using
        polar coordinates.

        Replicates the NetLogo 'setup-clusters' procedure.

        Returns: None (populates self.future_settlement_points).
        '''
        for _ in range(INITIAL_CLUSTERS):
            ### pick a random cluster centre anywhere in the square world
            cluster_centre_x = random.uniform(-WORLD_SIZE / 2, WORLD_SIZE / 2)
            cluster_centre_y = random.uniform(-WORLD_SIZE / 2, WORLD_SIZE / 2)

            ### radius is uniform in [CLUSTER_RADIUS_MIN, CLUSTER_RADIUS_MIN + CLUSTER_RADIUS_MAX]
            ### replicates: min-cluster-radius + (random max-cluster-radius)
            cluster_radius = CLUSTER_RADIUS_MIN + random.random() * CLUSTER_RADIUS_MAX

            ### scatter 200 candidate points inside the cluster using polar coordinates
            ### (angle + distance), then convert to Cartesian offsets
            for _ in range(200):
                angle_radians = random.uniform(0, 2 * math.pi)
                radial_distance = random.uniform(0, cluster_radius)
                candidate_x = cluster_centre_x + math.cos(angle_radians) * radial_distance
                candidate_y = cluster_centre_y + math.sin(angle_radians) * radial_distance
                self.future_settlement_points.append((candidate_x, candidate_y))

    def setup_population(self):
        '''
        Place INITIAL_HOUSEHOLDS households on sampled cluster positions,
        populate each household with people, and build the social network.

        Household size is drawn from an exponential distribution plus a
        minimum floor: int(Exponential(POPULATION_COEFFICIENT)) + 4,
        replicating the NetLogo 'population-coefficient' parameter.

        Each person is placed within ±2 world units of their household centre,
        giving micro-level positional variation.

        Replicates the NetLogo 'setup-population' procedure.

        Returns: None (populates self.households, self.people, self.graph).
        '''
        ### sample INITIAL_HOUSEHOLDS positions from the candidate pool
        ### min() guards against fewer candidates than requested households
        selected_positions = random.sample(
            self.future_settlement_points,
            min(INITIAL_HOUSEHOLDS, len(self.future_settlement_points))
        )

        ### global person ID counter (unique across all households)
        person_id = 0

        for household_position in selected_positions:
            ### assign a unique household ID and create the Household object
            self.house_counter += 1
            household_id = self.house_counter
            household_x, household_y = household_position

            household = Household(id=household_id, x=household_x, y=household_y)
            self.households[household_id] = household

            ### sample household size: exponential offset + floor of 4
            ### max(1, ...) ensures at least one person per household
            household_size = max(
                1,
                int(np.random.exponential(POPULATION_COEFFICIENT) + 4)
            )

            for _ in range(household_size):
                ### place each person within a ±2 unit offset of the household centre
                person_x = household_x + random.uniform(-2, 2)
                person_y = household_y + random.uniform(-2, 2)

                person = Person(
                    id=person_id,
                    household_id=household_id,
                    x=person_x,
                    y=person_y,
                )

                self.people[person_id] = person
                household.inhabitants.append(person_id)
                ### add node to the NetworkX graph so degree can be queried later
                self.graph.add_node(person_id)

                person_id += 1

        ### build the distance-stratified social network after all people are placed
        self.setup_people_network()

    def setup_people_network(self):
        '''
        Build an undirected social network by linking each person to a random
        subset of nearby neighbours in each of four concentric distance rings.

        For each person and each ring:
          - candidate neighbours within the ring radius are identified,
          - a random count of links is chosen in [0, MAX_CONNECTIONS * ring_share],
          - and links are created to a random sample of candidates.

        After all links are created, each person's degree and initial_degree
        attributes are set from the NetworkX graph.

        Replicates the NetLogo 'setup-people-network' procedure.

        Returns: None (populates self.connections and self.graph).
        '''
        all_people = list(self.people.values())

        for person in all_people:
            for range_id in [1, 2, 3, 4]:
                ### compute the maximum search radius for this ring
                ring_radius = SEARCH_RADIUS * RANGE_SEARCH_RADIUS_SHARE[range_id]

                ### collect all other people within the ring radius
                candidates_in_ring = [
                    other for other in all_people
                    if other.id != person.id
                    and self.distance(person, other) <= ring_radius
                ]

                ### upper bound on link count for this ring
                max_links_this_ring = int(
                    MAX_CONNECTIONS * RANGE_INITIAL_CONNECTIONS_SHARE[range_id]
                )

                ### sample the actual link count uniformly from [0, max_links_this_ring)
                ### random.randrange(n) returns a value in [0, n-1]; guard n >= 1
                link_count = random.randrange(max_links_this_ring) if max_links_this_ring > 0 else 0

                ### take a random subset of candidates of size link_count
                chosen_neighbours = random.sample(
                    candidates_in_ring,
                    min(link_count, len(candidates_in_ring))
                )

                for neighbour in chosen_neighbours:
                    self.create_connection(person.id, neighbour.id, range_id)

        ### update each person's degree attributes from the NetworkX graph
        for person in self.people.values():
            person.my_connection_count = self.graph.degree(person.id)
            person.initial_degree = person.my_connection_count

    def create_connection(self, person_a_id: int, person_b_id: int, range_id: int):
        '''
        Create a single undirected social connection between two people if
        one does not already exist.

        The per-link transmission probability (t_prob) is drawn from a normal
        distribution whose mean and standard deviation depend on the distance range;
        it is clamped to [0, ∞) because negative probabilities are meaningless.

        Replicates the NetLogo 'create-link-with range-id' procedure.

        person_a_id : int -- ID of the first person
        person_b_id : int -- ID of the second person
        range_id    : int -- distance ring category (1 = closest, 4 = farthest)

        Returns: None (modifies self.connections and self.graph in-place).
        '''
        ### use a sorted tuple as the dictionary key so the undirected link
        ### (a, b) and (b, a) always map to the same entry
        edge_key = tuple(sorted((person_a_id, person_b_id)))

        ### skip if a link between these two people already exists
        if edge_key in self.connections:
            return

        ### look up the transmission probability parameters for this range
        if range_id == 1:
            t_prob_mean, t_prob_stddev = TRANSMISSION_PROB_RANGE1_MEAN, TRANSMISSION_PROB_RANGE1_STDDEV
        elif range_id == 2:
            t_prob_mean, t_prob_stddev = TRANSMISSION_PROB_RANGE2_MEAN, TRANSMISSION_PROB_RANGE2_STDDEV
        elif range_id == 3:
            t_prob_mean, t_prob_stddev = TRANSMISSION_PROB_RANGE3_MEAN, TRANSMISSION_PROB_RANGE3_STDDEV
        else:
            t_prob_mean, t_prob_stddev = TRANSMISSION_PROB_RANGE4_MEAN, TRANSMISSION_PROB_RANGE4_STDDEV

        ### sample transmission probability; clamp at 0 to avoid negative values
        transmission_probability = max(0.0, np.random.normal(t_prob_mean, t_prob_stddev))

        connection = Connection(
            a=person_a_id,
            b=person_b_id,
            t_prob=transmission_probability,
            t_range=range_id,
        )

        self.connections[edge_key] = connection
        ### also register the edge in the NetworkX graph for degree tracking
        self.graph.add_edge(person_a_id, person_b_id)

    def start_epidemic(self):
        '''
        Seed the epidemic by placing INITIAL_INFECTED people into the incubation stage.

        The household geographically closest to the world origin (0, 0) is chosen
        as the starting point; the INITIAL_INFECTED people nearest to that household
        are infected, replicating the NetLogo behaviour of seeding near the centre.

        Replicates the NetLogo 'start-epidemic' procedure.

        Returns: None (modifies Person objects in self.people in-place).
        '''
        ### find the household nearest to the world centre (0, 0)
        central_household = min(
            self.households.values(),
            key=lambda h: math.sqrt(h.x ** 2 + h.y ** 2)
        )

        ### rank all people by their distance to that central household
        people_by_distance = sorted(
            self.people.values(),
            key=lambda p: math.sqrt(
                (p.x - central_household.x) ** 2
                + (p.y - central_household.y) ** 2
            )
        )

        ### infect the INITIAL_INFECTED closest people: move them to incubation stage
        for person in people_by_distance[:INITIAL_INFECTED]:
            person.susceptible = False
            person.incubation = True
            person.stage = "incubation"
            ### draw latent stage duration immediately at infection time
            person.stage_counter_l = self.get_stage_duration("latent")
            person.infected_in = self.tick

    ###########################################################################
    ##### Simulation loop #####################################################
    ###########################################################################

    def go(self):
        '''
        Advance the simulation by one tick.

        The tick is only incremented if at least one person is still infectious
        (incubation, prodromal, or contagious).  Returns False when the epidemic
        has ended naturally (no more active cases), signalling run() to stop.

        Replicates the NetLogo 'go' procedure.

        Returns: bool -- True if the simulation should continue, False if it has ended.
        '''
        ### stop if no active infectious cases remain (epidemic has ended)
        has_active_cases = any(
            p.incubation or p.prodromal or p.contag
            for p in self.people.values()
        )
        if not has_active_cases:
            return False

        ### spread infection along active social links
        daily_contacts, daily_transmissions = self.infection_spread()
        ### advance every person's disease stage by one day
        self.disease_development()

        ### increment the simulation clock after both update steps
        self.tick += 1

        ### record population counts and contact statistics for this tick
        self.record_stats(daily_contacts, daily_transmissions)

        return True

    def infection_spread(self):
        '''
        Attempt disease transmission from each contagious, mobile person to
        a random sample of their active social contacts.

        For each contagious person:
          1. Count their active connections (capped at MAX_DAILY_CONTACTS).
          2. Sample a contact count from [0, capped_count).
          3. For each contact, draw a random transmission threshold and test against
             SPREAD_RATE * link.t_prob; transmit if the draw falls below the threshold.

        The draw formula `random.random() * (0.1 + random.randrange(connection_count))`
        introduces connection-count-dependent stochasticity, replicating the NetLogo
        spread mechanic where highly connected individuals have more variable outcomes.

        Replicates the NetLogo 'infection-spread' procedure.

        Returns: Tuple[int, int] -- (daily_contacts, daily_transmissions)
        '''
        daily_contacts = 0
        daily_transmissions = 0

        ### only mobile, contagious people with active links can spread disease
        active_spreaders = [
            p for p in self.people.values()
            if p.contag
            and p.movable
            and self.active_connections_of(p.id)
        ]

        for spreader in active_spreaders:
            active_links = self.active_connections_of(spreader.id)
            connection_count = len(active_links)

            if connection_count == 0:
                continue

            ### cap daily contacts at MAX_DAILY_CONTACTS for highly connected people
            contact_cap = min(connection_count, MAX_DAILY_CONTACTS)

            ### sample how many contacts occur today
            ### random.randrange(n) returns [0, n-1]; guard n >= 1
            contacts_today = random.randrange(max(1, contact_cap))

            for _ in range(random.randrange(max(1, contacts_today))):
                ### re-query active links each iteration (links can be deactivated mid-loop)
                active_links = self.active_connections_of(spreader.id)
                if not active_links:
                    continue

                daily_contacts += 1

                ### choose a random active link for this contact event
                chosen_link = random.choice(active_links)

                ### identify the contact on the other end of the link
                contact_id = (
                    chosen_link.b if chosen_link.a == spreader.id else chosen_link.a
                )
                contact_person = self.people[contact_id]

                ### transmission threshold scales with SPREAD_RATE and link t_prob
                transmission_threshold = (SPREAD_RATE / 100) * chosen_link.t_prob

                ### draw: random float multiplied by a connection-count-dependent
                ### integer offset, replicating the NetLogo stochastic mechanic
                random_draw = random.random() * (
                    0.1 + random.randrange(max(1, connection_count))
                )

                ### attempt transmission if draw falls below threshold
                if random_draw < transmission_threshold:
                    daily_transmissions += 1
                    ### mark the link as having been used for transmission this tick
                    chosen_link.infected_in = self.tick

                    ### infect the contact only if still susceptible
                    if contact_person.susceptible:
                        contact_person.susceptible = False
                        contact_person.incubation = True
                        contact_person.stage = "incubation"
                        contact_person.stage_counter_l = self.get_stage_duration("latent")
                        contact_person.infected_in = self.tick

                    ### count the exposure event regardless of susceptibility
                    contact_person.sec_case_count += 1

        return daily_contacts, daily_transmissions

    def disease_development(self):
        '''
        Advance each infected person through the SEIRD disease stages by one tick.

        Processing order (four separate passes) matches the NetLogo agent ordering:
          1. Contagious → recovery / death check (stage_counter_c countdown)
          2. Prodromal  → contagious transition (stage_counter_p countdown)
          3. Incubation → prodromal transition  (stage_counter_l countdown)
          4. Death      → apply mortality if death_in counter reached zero
          5. Immobility → apply if imovable_in counter reached zero

        The death_in and imovable_in counters are set when a person becomes
        contagious (step 2) and count down each tick during step 1.

        Replicates the NetLogo 'disease-development' procedure.

        Returns: None (modifies Person objects in self.people in-place).
        '''
        ### pass 1: contagious stage — count down, check recovery
        for person in self.people.values():
            if not person.contag:
                continue

            ### decrement stage timer and illness duration accumulators
            person.stage_counter_c -= 1
            person.ill_duration += 1
            person.ill_duration_c += 1

            ### count down death timer if it is in the active range (0-100)
            if 0 < person.death_in < 100:
                person.death_in -= 1

            ### count down immobility timer if active
            if 0 < person.imovable_in < 100:
                person.imovable_in -= 1

            ### transition to recovered when contagious duration is exhausted
            if person.stage_counter_c <= 0:
                person.contag = False
                person.recovered = True
                person.stage = "recovered"
                ### deactivate this person's links so they no longer spread disease
                self.deactivate_connections(person.id)

        ### pass 2: prodromal stage — count down, transition to contagious
        for person in self.people.values():
            if not person.prodromal:
                continue

            person.stage_counter_p -= 1
            person.ill_duration += 1
            person.ill_duration_p += 1

            if person.stage_counter_p <= 0:
                ### draw a contagious stage duration and a random offset within it
                person.stage_counter_c = self.get_stage_duration("contagious")
                random_offset = random.randrange(max(1, int(person.stage_counter_c)))

                person.prodromal = False
                person.contag = True
                person.stage = "contagious"

                ### apply mortality: if drawn, set the death countdown
                if random.random() < MORTALITY_RATE / 100:
                    ### death occurs at roughly half the random offset into the contagious stage
                    person.death_in = random_offset / 2

                ### immobility onset is set to twice the random offset
                person.imovable_in = random_offset * 2

        ### pass 3: incubation (latent) stage — count down, transition to prodromal
        for person in self.people.values():
            if not person.incubation:
                continue

            person.stage_counter_l -= 1
            person.ill_duration += 1
            person.ill_duration_l += 1

            if person.stage_counter_l <= 0:
                person.stage_counter_p = self.get_stage_duration("prodromal")
                person.incubation = False
                person.prodromal = True
                person.stage = "prodromal"

        ### pass 4: apply death to contagious people whose death_in timer has expired
        for person in self.people.values():
            if person.contag and person.death_in <= 0:
                person.contag = False
                person.died = True
                person.stage = "death"
                ### record total illness duration at time of death
                person.died_in = person.ill_duration
                self.deactivate_connections(person.id)

        ### pass 5: apply immobility to contagious people whose imovable_in timer expired
        for person in self.people.values():
            if person.contag and person.imovable_in <= 0:
                person.movable = False
                ### record illness duration at time of immobility onset
                person.imoved_in = person.ill_duration

    ###########################################################################
    ##### Helper methods ######################################################
    ###########################################################################

    def get_stage_duration(self, stage_name: str) -> int:
        '''
        Sample and return a disease-stage duration in ticks from a normal distribution.

        The result is clamped to a minimum of 1 tick so that no stage lasts zero ticks,
        and rounded to the nearest integer to match NetLogo's tick-based logic.

        Replicates the NetLogo 'random-normal' calls used for stage duration assignment.

        stage_name : str -- one of "latent", "prodromal", or "contagious"

        Returns: int -- stage duration in ticks (>= 1)
        Raises:  ValueError if stage_name is not recognised
        '''
        if stage_name == "latent":
            ### latent (incubation) stage: mean 12 ticks, std 3 ticks
            sampled_duration = np.random.normal(DURATION_LATENT_MEAN, DURATION_LATENT_STDDEV)
        elif stage_name == "prodromal":
            ### prodromal stage: mean 3 ticks, std 2 ticks
            sampled_duration = np.random.normal(DURATION_PRODROMAL_MEAN, DURATION_PRODROMAL_STDDEV)
        elif stage_name == "contagious":
            ### contagious stage: mean 9 ticks, std 3 ticks
            sampled_duration = np.random.normal(DURATION_CONTAGIOUS_MEAN, DURATION_CONTAGIOUS_STDDEV)
        else:
            raise ValueError(f"Unknown stage name: {stage_name!r}")

        ### clamp to 1 and round to nearest integer
        return max(1, round(sampled_duration))

    def active_connections_of(self, person_id: int) -> List[Connection]:
        '''
        Return all active Connection objects involving the given person.

        A connection is "active" if its .active flag is True (i.e. neither
        endpoint has yet recovered or died).

        Replicates the NetLogo link filter used in infection-spread.

        person_id : int -- ID of the person whose active links are requested

        Returns: List[Connection]
        '''
        return [
            conn for conn in self.connections.values()
            if conn.active and (conn.a == person_id or conn.b == person_id)
        ]

    def deactivate_connections(self, person_id: int):
        '''
        Deactivate all Connection objects involving the given person by setting
        their .active flag to False.

        Called when a person recovers or dies; deactivated links are excluded
        from future infection-spread and active_connections_of calls.

        Replicates the NetLogo 'ask my-links [set active? false]' idiom.

        person_id : int -- ID of the person whose links should be deactivated

        Returns: None
        '''
        for conn in self.connections.values():
            if conn.a == person_id or conn.b == person_id:
                conn.active = False

    @staticmethod
    def distance(person_a: Person, person_b: Person) -> float:
        '''
        Compute the Euclidean distance between two Person agents.

        Uses the standard 2D distance formula: sqrt((x2-x1)^2 + (y2-y1)^2).

        Replicates the NetLogo built-in 'distance' primitive.

        person_a : Person -- first agent
        person_b : Person -- second agent

        Returns: float -- Euclidean distance in world units
        '''
        delta_x = person_a.x - person_b.x
        delta_y = person_a.y - person_b.y
        return math.sqrt(delta_x ** 2 + delta_y ** 2)

    def record_stats(self, daily_contacts: int = 0, daily_transmissions: int = 0):
        '''
        Append per-tick population and contact counts to self.stats.

        Called once at tick 0 (during setup, before any go() step) and once
        after each go() step.  The "infected" series is the sum of all three
        active disease stages (incubation + prodromal + contagious).

        Replicates the NetLogo monitor and plot update logic in 'go'.

        daily_contacts      : int -- total contact events this tick (default 0 for tick 0)
        daily_transmissions : int -- successful transmissions this tick (default 0 for tick 0)

        Returns: None (appends to self.stats lists in-place).
        '''
        all_people = list(self.people.values())

        incubation_count = sum(p.incubation for p in all_people)
        prodromal_count  = sum(p.prodromal  for p in all_people)
        contagious_count = sum(p.contag     for p in all_people)

        self.stats["tick"].append(self.tick)
        self.stats["susceptible"].append(sum(p.susceptible for p in all_people))
        self.stats["incubation"].append(incubation_count)
        self.stats["prodromal"].append(prodromal_count)
        self.stats["contagious"].append(contagious_count)
        self.stats["recovered"].append(sum(p.recovered for p in all_people))
        self.stats["died"].append(sum(p.died for p in all_people))
        ### combined "infected" = everyone in any of the three active disease stages
        self.stats["infected"].append(incubation_count + prodromal_count + contagious_count)
        self.stats["daily_contacts"].append(daily_contacts)
        self.stats["daily_transmissions"].append(daily_transmissions)

    def run(self):
        '''
        Execute the simulation loop for up to MAX_TICKS ticks.

        Stops earlier if go() returns False (epidemic naturally ended).
        Equivalent to the NetLogo 'go' button with a tick limit.

        Returns: None
        '''
        for _ in range(MAX_TICKS):
            simulation_still_running = self.go()
            if not simulation_still_running:
                break


###############################################################################
##### Visualisation functions #################################################
###############################################################################

def person_color(person: Person) -> str:
    '''
    Map a Person's current disease stage to a matplotlib named colour string.

    Colour scheme replicates the NetLogo patch/agent colours used in the
    original model interface:
      died        → brown
      recovered   → orange
      contagious  → yellow
      prodromal   → green
      incubation  → red
      susceptible → dodgerblue (default)

    person : Person -- the agent whose colour is being determined

    Returns: str -- matplotlib named colour string
    '''
    ### check stages from most severe to least severe so that terminal states
    ### (died, recovered) are returned before active-disease states
    if person.died:
        return "brown"
    if person.recovered:
        return "orange"
    if person.contag:
        return "yellow"
    if person.prodromal:
        return "green"
    if person.incubation:
        return "red"
    ### default: susceptible
    return "dodgerblue"


def style_histogram_axis(ax):
    '''
    Apply a minimal white-background style to a histogram axes object.

    Sets a white background, removes the grid, and makes all spine borders light grey,
    matching the clean plotting style used in the original NetLogo histograms.

    ax : matplotlib.axes.Axes -- the axes to style

    Returns: None
    '''
    ### white background for histogram panels
    ax.set_facecolor("white")
    ### remove the grid to reduce visual noise
    ax.grid(False)
    ### set all four spine borders to a light grey colour
    for spine in ax.spines.values():
        spine.set_color("0.75")


def plot_model(model: 'EpidemicModel'):
    '''
    Produce a four-panel figure showing the spatial disease map plus three
    time-series plots (epidemic stages, population outcomes, daily contacts).

    Replicates the NetLogo 'visualise' procedure and monitor plots.

    Layout (3 rows × 5 columns):
      - Left (cols 0-2, all rows): spatial scatter map of all agents, coloured by
        disease stage, with red lines showing connections used for transmission
        in the last 100 ticks.
      - Top-right (row 0, cols 3-4): epidemic development (incubation, prodromal,
        contagious, and combined infected counts over time).
      - Mid-right (row 1, cols 3-4): population outcomes (susceptible, recovered, died).
      - Bottom-right (row 2, cols 3-4): daily contacts and transmissions.

    model : EpidemicModel -- a completed (or in-progress) simulation instance

    Returns: None (displays an interactive matplotlib figure).
    '''
    fig = plt.figure(figsize=(24, 14))

    ### subplot layout: 3 rows × 5 columns; spatial map spans columns 0-2, all rows
    ax_map      = plt.subplot2grid((3, 5), (0, 0), rowspan=3, colspan=3)
    ax_epidemic = plt.subplot2grid((3, 5), (0, 3), colspan=2)
    ax_pop      = plt.subplot2grid((3, 5), (1, 3), colspan=2)
    ax_contacts = plt.subplot2grid((3, 5), (2, 3), colspan=2)

    all_people = list(model.people.values())

    ### collect agent positions and colour each point by disease stage
    agent_x_coords = [p.x for p in all_people]
    agent_y_coords = [p.y for p in all_people]
    agent_colours  = [person_color(p) for p in all_people]

    ### black background replicates the NetLogo world appearance
    ax_map.set_facecolor("black")

    ### scatter all agents as small coloured dots
    ax_map.scatter(agent_x_coords, agent_y_coords, c=agent_colours, s=10)

    ### overlay red lines for connections that transmitted disease in the last 100 ticks
    ### 'infected_in >= model.tick - 100' matches the NetLogo 'recently-infected' link display
    for connection in model.connections.values():
        if connection.infected_in >= model.tick - 100:
            person_a = model.people[connection.a]
            person_b = model.people[connection.b]
            ax_map.plot(
                [person_a.x, person_b.x],
                [person_a.y, person_b.y],
                color="red",
                linewidth=0.7,
                alpha=0.7,
            )

    ### fix axis limits to the visible world extent and remove tick labels
    ax_map.set_xlim(-100.5, 100.5)
    ax_map.set_ylim(-100.5, 100.5)
    ax_map.set_aspect("equal", adjustable="box")
    ax_map.set_title("Settlement and disease transmission network", fontsize=16)
    ax_map.set_xticks([])
    ax_map.set_yticks([])

    tick_series = model.stats["tick"]

    ### epidemic development: per-tick stage counts
    ax_epidemic.plot(tick_series, model.stats["prodromal"],  label="Prodromal",  linewidth=2)
    ax_epidemic.plot(tick_series, model.stats["contagious"], label="Contagious", linewidth=2)
    ax_epidemic.plot(tick_series, model.stats["incubation"], label="Incubation", linewidth=2)
    ax_epidemic.plot(tick_series, model.stats["infected"],   label="Infected",   linewidth=2)
    ax_epidemic.set_title("Epidemic development", fontsize=14)
    ax_epidemic.legend(fontsize=10)

    ### population outcomes: susceptible, recovered, died
    ax_pop.plot(tick_series, model.stats["susceptible"], label="Susceptible", linewidth=2)
    ax_pop.plot(tick_series, model.stats["recovered"],   label="Recovered",   linewidth=2)
    ax_pop.plot(tick_series, model.stats["died"],        label="Died",        linewidth=2)
    ax_pop.set_title("Population outcomes", fontsize=14)
    ax_pop.legend(fontsize=10)

    ### daily contacts and transmissions
    ax_contacts.plot(
        tick_series, model.stats["daily_contacts"],      label="Daily contacts",      linewidth=2
    )
    ax_contacts.plot(
        tick_series, model.stats["daily_transmissions"], label="Daily transmissions", linewidth=2
    )
    ax_contacts.set_title("Daily contacts and transmissions", fontsize=14)
    ax_contacts.legend(fontsize=10)

    plt.tight_layout()
    plt.show()


def plot_histograms(model: 'EpidemicModel'):
    '''
    Produce a 4×3 grid of histograms summarising simulation outcomes.

    Replicates the NetLogo histogram monitors and BehaviorSpace output plots.

    Panels (row, col):
      (0,0) Link length (km)           -- Euclidean distances of all social links
      (1,0) Degree distribution        -- number of social connections per person
      (2,0) Household population size  -- number of inhabitants per household
      (3,0) Link transmission prob.    -- per-link transmission probability values
      (0,1) Prodromal stage duration   -- ticks spent in the prodromal stage
      (1,1) Contagious stage duration  -- ticks spent in the contagious stage
      (2,1) Died in (tick)             -- illness duration at time of death
      (3,1) Immobile in (tick)         -- illness duration at onset of immobility
      (0,2) Latent stage duration      -- ticks spent in the latent stage
      (1,2) Whole illness duration     -- total ticks ill (any stage)
      (2,2) (empty)
      (3,2) (empty)

    model : EpidemicModel -- a completed simulation instance

    Returns: None (displays an interactive matplotlib figure).
    '''
    all_people = list(model.people.values())

    ### compute per-person degree from the NetworkX graph
    degree_values = [model.graph.degree(p.id) for p in all_people]

    ### household size = number of inhabitants per household
    household_sizes = [len(h.inhabitants) for h in model.households.values()]

    ### compute Euclidean link length and transmission probability for every connection
    link_lengths = []
    link_transmission_probs = []
    for conn in model.connections.values():
        person_a = model.people[conn.a]
        person_b = model.people[conn.b]
        link_length = math.sqrt(
            (person_a.x - person_b.x) ** 2
            + (person_a.y - person_b.y) ** 2
        )
        link_lengths.append(link_length)
        link_transmission_probs.append(conn.t_prob)

    ### collect stage durations only for people who passed through each stage
    latent_durations    = [p.ill_duration_l for p in all_people if p.ill_duration_l > 0]
    prodromal_durations = [p.ill_duration_p for p in all_people if p.ill_duration_p > 0]
    contagious_durations= [p.ill_duration_c for p in all_people if p.ill_duration_c > 0]
    whole_illness       = [p.ill_duration   for p in all_people if p.ill_duration   > 0]

    ### died_in and imoved_in are -1 for people who never died / became immobile
    died_in_values   = [p.died_in   for p in all_people if p.died_in   > 0]
    imoved_in_values = [p.imoved_in for p in all_people if p.imoved_in > 0]

    fig, axes = plt.subplots(4, 3, figsize=(18, 16))
    fig.suptitle("Simulation results dashboard", fontsize=18)

    ### column 0: network and population structure
    axes[0, 0].hist(link_lengths,           bins=40, edgecolor="black", facecolor="white")
    axes[0, 0].set_title("Link length (world units)")
    axes[0, 0].set_xlim(0, 5)

    axes[1, 0].hist(degree_values,          bins=30, edgecolor="black", facecolor="white")
    axes[1, 0].set_title("Degree distribution")
    axes[1, 0].set_xlim(0, 30)

    axes[2, 0].hist(household_sizes,        bins=30, edgecolor="black", facecolor="white")
    axes[2, 0].set_title("Household population size")
    axes[2, 0].set_xlim(0, 30)

    axes[3, 0].hist(link_transmission_probs, bins=30, edgecolor="black", facecolor="white")
    axes[3, 0].set_title("Link transmission probability")
    axes[3, 0].set_xlim(0, 2)

    ### column 1: disease stage durations and terminal events
    axes[0, 1].hist(prodromal_durations,    bins=20, edgecolor="black", facecolor="white")
    axes[0, 1].set_title("Prodromal stage duration (ticks)")
    axes[0, 1].set_xlim(0, 20)

    axes[1, 1].hist(contagious_durations,   bins=20, edgecolor="black", facecolor="white")
    axes[1, 1].set_title("Contagious stage duration (ticks)")
    axes[1, 1].set_xlim(0, 20)

    axes[2, 1].hist(died_in_values,         bins=20, edgecolor="black", facecolor="white")
    axes[2, 1].set_title("Illness duration at death (ticks)")
    axes[2, 1].set_xlim(0, 50)

    axes[3, 1].hist(imoved_in_values,       bins=20, edgecolor="black", facecolor="white")
    axes[3, 1].set_title("Illness duration at immobility onset (ticks)")
    axes[3, 1].set_xlim(0, 50)

    ### column 2: latent and whole-illness durations; remaining cells are unused
    axes[0, 2].hist(latent_durations,       bins=25, edgecolor="black", facecolor="white")
    axes[0, 2].set_title("Latent stage duration (ticks)")
    axes[0, 2].set_xlim(0, 25)

    axes[1, 2].hist(whole_illness,          bins=30, edgecolor="black", facecolor="white")
    axes[1, 2].set_title("Whole illness duration (ticks)")
    axes[1, 2].set_xlim(0, 50)

    ### hide unused panels in column 2
    axes[2, 2].axis("off")
    axes[3, 2].axis("off")

    ### apply consistent minimal styling to all panels
    for ax in axes.flat:
        style_histogram_axis(ax)

    plt.tight_layout()
    plt.show()


###############################################################################
##### Script entry point ######################################################
###############################################################################

if __name__ == "__main__":
    ### locate data files relative to this script's directory so the module
    ### works correctly regardless of where it is called from
    _script_directory = pathlib.Path(__file__).parent

    ### construct and initialise the model
    model = EpidemicModel()
    model.setup()

    ### run the simulation for up to MAX_TICKS ticks
    model.run()

    ### print a summary of the completed simulation
    print("Simulation finished")
    print(f"Final tick:        {model.tick}")
    print(f"Total population:  {len(model.people)} people")
    print(f"Total households:  {len(model.households)} households")
    print(f"Total connections: {len(model.connections)} links")

    ### produce the spatial map and the histogram dashboard
    plot_model(model)
    plot_histograms(model)
