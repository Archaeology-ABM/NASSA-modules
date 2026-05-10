############################
# Roman Transport Network Analysis - version 01
# by João Messias Sousa da Silva (2026)
#
# Python implementation of NASSA module 2022-Brughmans-002:
#   Brughmans, T. (2018). Importing a Roman Transport network with Netlogo, Tutorial.
#   https://github.com/Archaeology-ABM/NASSA-modules/tree/main/2022-Brughmans-002
#
# Uses the ORBIS Stanford Geospatial Network Model of the Roman World:
#   Scheidel, W. & Meeks, E. (2014). ORBIS. Stanford University Libraries.
#   https://orbis.stanford.edu
#
# Replicates the following NetLogo procedures in Python:
#   data-correction                       : 8 coordinate/attribute fixes to ORBIS node data
#   analysis-distance[-km|-days|-expense] : shortest-path distances from Rome to all nodes
#   visualise                             : transport network coloured by route type
#   provinces                             : settlements coloured by Roman province
#   visualise-distance[-km|-days|-expense]: greyscale distance maps from Rome
#
# Dependencies: networkx >= 2.0, matplotlib >= 3.0, numpy >= 1.20
############################

import io
import pathlib
import xml.etree.ElementTree as ET

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path
from matplotlib.collections import LineCollection


###############################################################################
##### NetLogo colour system ###################################################
###############################################################################

# NetLogo organises colours in 14 groups of 10 values each (total range: 0-139.9).
# Group 0 (values 0-9.9) is a greyscale: 0 = black, 9.9 = white.
# Groups 1-13 (values 10-139.9) are named hues. Within each group, the pure base
# hue sits at offset 5 (e.g. value 15 = pure red, 25 = pure orange, ..., 135 = pure pink).
# Offsets 0-5 darken the hue toward black; offsets 5-10 lighten it toward white.
# Source: https://ccl.northwestern.edu/netlogo/docs/programming.html#colors

# Pure hue RGB values (0-255 scale) at the centre of each NetLogo colour group.
_NL_BASE_RGB = {
    15:  (215,  50,  41),   # red
    25:  (241, 150,  39),   # orange
    35:  (157, 110,  72),   # brown
    45:  (237, 237,  48),   # yellow
    55:  ( 89, 176,  60),   # green
    65:  (179, 196,  61),   # lime
    75:  ( 89, 176, 145),   # turquoise
    85:  ( 84, 196, 196),   # cyan
    95:  ( 63, 147, 221),   # sky
    105: ( 37,  89, 163),   # blue
    115: (122,  75, 163),   # violet
    125: (204,  71, 166),   # magenta
    135: (218, 132, 153),   # pink
}

# Maximum greyscale value in NetLogo (corresponds to white)
_NL_GREY_MAX = 9.9

# Maximum valid NetLogo colour value
_NL_COLOR_MAX = 139.9

# Number of values per NetLogo colour group
_NL_GROUP_SIZE = 10

# Offset within a colour group at which the pure base hue sits
_NL_BASE_OFFSET = 5


def _nl_color(netlogo_color_value):
    '''
    Convert a NetLogo colour value (float in 0-139.9) to a matplotlib RGB tuple (floats in 0-1).

    netlogo_color_value: float
        NetLogo colour value.
        Range 0-9.9  : greyscale (0 = black, 9.9 = white).
        Range 10-139.9: named colour groups, each 10 units wide,
                        centred on a base hue at offset 5.

    Returns: tuple(float, float, float) -- (R, G, B) in 0-1 range for matplotlib.
    '''
    ### clamp input to the valid NetLogo colour range
    netlogo_color_value = max(0.0, min(_NL_COLOR_MAX, float(netlogo_color_value)))

    ### greyscale range (0-9.9): map linearly from black (0.0) to white (1.0)
    if netlogo_color_value < _NL_GROUP_SIZE:
        grey_intensity = netlogo_color_value / _NL_GREY_MAX
        return (grey_intensity, grey_intensity, grey_intensity)

    ### colour groups (10-139.9)
    ### identify which colour group this value belongs to (1 = red group, 2 = orange, ...)
    group_index = int(netlogo_color_value / _NL_GROUP_SIZE)

    ### locate the base hue for this group (e.g. group 1 -> value 15, group 2 -> value 25)
    base_hue_value = group_index * _NL_GROUP_SIZE + _NL_BASE_OFFSET

    ### offset of the input value within its group (0.0-9.9)
    offset_within_group = netlogo_color_value - group_index * _NL_GROUP_SIZE

    ### get the pure base hue in RGB 0-255 scale
    base_r, base_g, base_b = _NL_BASE_RGB.get(base_hue_value, (128, 128, 128))

    if offset_within_group <= _NL_BASE_OFFSET:
        ### offsets 0-5: darken toward black by scaling with offset / 5
        darkening_factor = offset_within_group / _NL_BASE_OFFSET
        return (
            base_r / 255 * darkening_factor,
            base_g / 255 * darkening_factor,
            base_b / 255 * darkening_factor,
        )
    else:
        ### offsets 5-10: lighten toward white by blending with (255, 255, 255)
        lightening_factor = (offset_within_group - _NL_BASE_OFFSET) / _NL_BASE_OFFSET
        return (
            (base_r + (255 - base_r) * lightening_factor) / 255,
            (base_g + (255 - base_g) * lightening_factor) / 255,
            (base_b + (255 - base_b) * lightening_factor) / 255,
        )


###############################################################################
##### Node marker #############################################################
###############################################################################

# NetLogo built-in "house" shape reproduced as a matplotlib Path marker.
# Vertices are in normalised coordinates centred on (0, 0).
# matplotlib Path markers scale with the scatter 's' (size in points^2) parameter.
_HOUSE_VERTICES = np.array([
    (-0.40, -0.50),   # base bottom-left
    ( 0.40, -0.50),   # base bottom-right
    ( 0.40,  0.10),   # right wall top
    ( 0.55,  0.10),   # roof right eave
    ( 0.00,  0.65),   # roof peak
    (-0.55,  0.10),   # roof left eave
    (-0.40,  0.10),   # left wall top
    (-0.40, -0.50),   # close polygon back to start
])

# Path drawing commands: MOVETO positions the pen at the first vertex;
# LINETO draws a line to each subsequent vertex; CLOSEPOLY closes the shape.
_HOUSE_CODES = [Path.MOVETO] + [Path.LINETO] * 6 + [Path.CLOSEPOLY]

HOUSE = Path(_HOUSE_VERTICES, _HOUSE_CODES)


###############################################################################
##### Colour maps (NetLogo procedure translations) ############################
###############################################################################

# Province name -> NetLogo colour value.
# Direct translation of the colour assignments in the NetLogo 'provinces' procedure.
_PROVINCE_NL_COLOR = {
    "Italia":                   15,   # red
    "Lusitania":                 5,   # grey
    "Mauretania Caesariensis":  25,   # orange
    "Britannia":                35,   # brown
    "Aquitania":                45,   # yellow
    "Cyrenica":                 55,   # green
    "Dalmatia":                 65,   # lime
    "Belgica":                  75,   # turquoise
    "Lugudunensis":            135,   # pink
    "Raetia":                   85,   # cyan
    "Tarraconensis":            95,   # sky
    "Syria":                   105,   # blue
    "Noricum":                 115,   # violet
    "Narbonensis":               4,   # dark grey
    "Aegyptus":                125,   # magenta
    "Arabia Petraea":          125,   # magenta
    "Cilicia":                  93,   # mid-sky
    "Bithynia":                 83,   # mid-cyan
    "Germania Inferior":        73,   # mid-turquoise
    "Germania Superior":        63,   # mid-lime
    "Africa":                   53,   # mid-green
    "Alpes Cottidae":           43,   # mid-yellow
    "Pannonia Superior":        33,   # mid-brown
    "Moesia Superior":         123,   # mid-magenta
    "Sicilia":                  13,   # mid-red
    "Macadonia":                23,   # mid-orange
    "Graecia":                  23,   # mid-orange
    "Crete":                    93,   # mid-sky
    "Thracia":                 103,   # mid-blue
    "Asia":                    113,   # mid-violet
    "Moesia Inferior":         123,   # mid-magenta
    "Cappadocia":              133,   # mid-pink
    "Corsica":                   8,   # light grey
    "Armenia":                  18,   # dark red
    "Palestine":                28,   # dark orange
    "Numidia":                  38,   # dark brown
    "Dacia":                    48,   # dark yellow
    "Panonia Inferior":         58,   # dark green
    "Judea":                    68,   # dark lime
    "Mauretania Tingitana":     78,   # dark turquoise
    "Baetica":                  88,   # dark cyan
    "Epirus":                   98,   # dark sky
    "Lycia":                   108,   # dark blue
    "Baleares":                118,   # dark violet
    "Sardinia":                128,   # dark magenta
    "Cyprus":                  138,   # dark pink
    "Outside_Blacksea":         46,   # mid-yellow
}

# Route type string -> NetLogo colour value.
# Direct translation of the colour assignments in the NetLogo 'visualise' procedure.
_ROUTE_NL_COLOR = {
    "road":       3,    # dark grey -- land roads
    "coastal":    95,   # sky -- coastal sea routes
    "overseas":   95,   # sky -- open sea routes
    "slowcoast":  95,   # sky -- slow coastal routes
    "ferry":      95,   # sky -- ferry crossings
    "slowover":   95,   # sky -- slow open sea routes
    "fastdown":   9.9,  # white -- fast downstream river routes
    "fastup":     9.9,  # white -- fast upstream river routes
    "downstream": 9.9,  # white -- downstream river routes
    "upstream":   9.9,  # white -- upstream river routes
}

# NetLogo colour value used for nodes and edges with no specific colour assignment.
_DEFAULT_NL_COLOR = 5  # mid-grey

# NetLogo settlement rank values -> matplotlib scatter marker sizes (in points^2).
# NetLogo visual sizes per rank: 6->0.2, 60->0.3, 70->0.4, 80->0.7, 90->0.9, 100->2.0 units.
# Multiplied x100 to convert to matplotlib scatter 'points^2' units.
_RANK_TO_MARKER_SIZE = {6: 20, 60: 30, 70: 40, 80: 70, 90: 90, 100: 200}

# Fallback marker size for nodes with an unrecognised or missing rank value.
_DEFAULT_MARKER_SIZE = 20

# Figure dimensions for all output plots (width, height in inches).
_FIGURE_SIZE = (14, 8)

# Edge line width for all plots (in points).
_EDGE_LINEWIDTH = 0.4

# Node marker outline width (in points).
_NODE_EDGE_LINEWIDTH = 0.3


###############################################################################
##### Main class ##############################################################
###############################################################################

class RomanTransportNetwork:
    '''
    Python reimplementation of NASSA module 2022-Brughmans-002
    (Brughmans, T. 2018. Importing a Roman Transport network with Netlogo, Tutorial).

    Loads the ORBIS Stanford directed transport network from a GraphML file
    (https://orbis.stanford.edu) and exposes methods for distance analysis
    and visualisation that replicate the original NetLogo procedures.

    Attributes:

    G: networkx.DiGraph
        Directed ORBIS transport graph. Nodes represent Roman settlements and
        junctions; directed edges represent transport routes with attributes:
        'km'         : route length in kilometres (float)
        'days'       : travel time in days (float)
        'expense'    : cost index (float)
        'route-type' : route category string (road, coastal, overseas, etc.)

    name_attr: str
        Node attribute key used as the settlement name label.
        Set to 'town-name' if present in the graph, otherwise 'label'.

    pos: dict
        Node position dictionary mapping node ID strings to (x, y) coordinate tuples.
        Derived from node 'x' and 'y' attributes. Used for all matplotlib plots.

    rome_node: str
        Node ID of Roma in the graph.

    alex_node: str
        Node ID of Alexandria in the graph.

    Methods:

    analyse_distance_to_rome(weight_attr=None)

    plot_network()

    plot_provinces()

    plot_distance_map(weight_attr=None)
    '''

    def __init__(self, graphml_path: str):
        '''
        Load and preprocess the ORBIS GraphML network file.

        graphml_path: str -- file path to the ORBIS .graphml file.
        '''
        ###############################################################
        ### 1. Read and repair the GraphML file #######################
        ###############################################################

        ### read the full file content as a string so text-level fixes can be applied
        raw_content = open(graphml_path, encoding="utf-8").read()

        ### fix namespace URI: ORBIS files use the older '/graphml' URI suffix,
        ### but NetworkX's graphml reader expects the standard '/xmlns' URI
        raw_content = raw_content.replace(
            'xmlns="http://graphml.graphdrawing.org/xmlns/graphml"',
            'xmlns="http://graphml.graphdrawing.org/xmlns"',
        )

        ### parse the corrected XML string into an element tree for structural cleaning
        GRAPHML_NS = "http://graphml.graphdrawing.org/xmlns"
        xml_tree = ET.fromstring(raw_content)

        ### identify and remove vendor-only <key> elements (e.g. from the visone editor)
        ### that define neither 'attr.name' nor 'yfiles.type' --
        ### NetworkX cannot interpret these and raises a parse error if they remain
        invalid_key_ids: set[str] = set()
        for key_element in xml_tree.findall(f"{{{GRAPHML_NS}}}key"):
            has_attr_name = key_element.get("attr.name") is not None
            has_yfiles    = key_element.get("yfiles.type") is not None
            if not has_attr_name and not has_yfiles:
                invalid_key_ids.add(key_element.get("id", ""))
                xml_tree.remove(key_element)

        ### remove any <data> child elements that reference the now-deleted keys
        if invalid_key_ids:
            for xml_container in xml_tree.iter():
                for data_element in list(xml_container.findall(f"{{{GRAPHML_NS}}}data")):
                    if data_element.get("key") in invalid_key_ids:
                        xml_container.remove(data_element)

        ### serialise the cleaned element tree back to a string and pass it to NetworkX
        clean_buffer = io.StringIO()
        clean_buffer.write(ET.tostring(xml_tree, encoding="unicode", xml_declaration=False))
        clean_buffer.seek(0)

        ### nx.DiGraph: directed graph -- edge direction encodes travel direction
        self.G: nx.DiGraph = nx.read_graphml(clean_buffer)

        ### ensure the graph is directed even if the GraphML file omits the declaration
        if not self.G.is_directed():
            self.G = self.G.to_directed()

        ###############################################################
        ### 2. Ensure edge weight attributes are numeric ##############
        ###############################################################

        ### GraphML serialisation may store numeric values as strings;
        ### cast km, days, and expense to float so Dijkstra's algorithm can use them
        for _, _, edge_data in self.G.edges(data=True):
            for weight_key in ("km", "days", "expense"):
                if weight_key in edge_data:
                    try:
                        edge_data[weight_key] = float(edge_data[weight_key])
                    except (TypeError, ValueError):
                        pass

        ###############################################################
        ### 3. Apply the NetLogo 'data-correction' procedure ##########
        ###############################################################

        self._apply_data_corrections()

        ###############################################################
        ### 4. Determine which node attribute holds the town name #####
        ###############################################################

        ### inspect the first node to detect the naming attribute convention
        _, first_node_data = next(iter(self.G.nodes(data=True)))
        if "town-name" in first_node_data:
            self.name_attr = "town-name"
        else:
            self.name_attr = "label"

        ###############################################################
        ### 5. Build position dictionary for matplotlib plotting ######
        ###############################################################

        ### skip nodes that lack valid x or y coordinate attributes
        self.pos = {
            node_id: (float(node_data["x"]), float(node_data["y"]))
            for node_id, node_data in self.G.nodes(data=True)
            if node_data.get("x") not in (None, "") and node_data.get("y") not in (None, "")
        }

        ###############################################################
        ### 6. Locate Roma and Alexandria in the graph ################
        ###############################################################

        self.rome_node = self._find_node_by_name("Roma")
        self.alex_node = self._find_node_by_name("Alexandria")

    ###################################################################
    ##### Internal helpers ############################################
    ###################################################################

    def _apply_data_corrections(self):
        '''
        Replicates the NetLogo 'data-correction' procedure.

        Applies 8 hard-coded corrections to node coordinates and attributes
        for ORBIS nodes whose GraphML data is known to be missing or inaccurate.
        Node ID keys are ORBIS settlement identifier strings.
        '''
        ### each entry maps an ORBIS node ID to a dict of attribute overrides
        node_corrections = {
            "50317": dict(x=12.258,  y=41.78,  label="Portus",
                          modern="Italy",  province="Italia",  rank=90),
            "50522": dict(x=16.21,   y=41.36,  label="Aufidus",
                          modern="Italy",  province="Italia",  rank=60),
            "50572": dict(x=25.213,  y=37.412, label="Rheneia",
                          modern="Greece", province="Graecia", rank=60),
            "50457": dict(x=23.589,  y=35.232, label="Kriou Metopon",
                          modern="Greece", province="Crete",   rank=60),
            "50786": dict(x=25.75,   y=36.75,  label="Kerea",
                          modern="Greece", province="Graecia", rank=60),
            "50789": dict(x=26.459,  y=37.005, label="Lebinthos",
                          modern="Greece", province="Graecia", rank=60),
            "50790": dict(x=23.625,  y=37.875, label="Leros",
                          modern="Greece", province="Graecia", rank=60),
            "50792": dict(x=25.37,   y=37.44,  label="Mykonos",
                          modern="Greece", province="Graecia", rank=60),
        }

        ### apply corrections only to nodes that exist in the loaded graph
        for node_id, corrected_attributes in node_corrections.items():
            if node_id not in self.G.nodes:
                continue
            for attr_key, attr_value in corrected_attributes.items():
                self.G.nodes[node_id][attr_key] = attr_value

    def _find_node_by_name(self, settlement_name: str):
        '''
        Return the node ID of the settlement whose name attribute matches the given string.

        settlement_name: str -- settlement name to search for (e.g. "Roma", "Alexandria").

        Returns: str -- node ID of the matching settlement.
        Raises:  ValueError if no node with that name is found.
        '''
        for node_id, node_data in self.G.nodes(data=True):
            if node_data.get(self.name_attr) == settlement_name:
                return node_id
        raise ValueError(f"Could not find node with name {settlement_name!r}")

    def _size_from_rank(self, rank_value):
        '''
        Map a NetLogo settlement rank value to a matplotlib scatter marker size (points^2).

        NetLogo visual sizes per rank: 6->0.2, 60->0.3, 70->0.4, 80->0.7, 90->0.9, 100->2.0.
        These are multiplied x100 to convert to matplotlib scatter 'points^2' units.

        rank_value: int or float -- settlement rank from the ORBIS node attributes.

        Returns: int -- marker size in points^2.
        '''
        try:
            rank_as_int = int(float(rank_value))
        except (TypeError, ValueError):
            return _DEFAULT_MARKER_SIZE
        return _RANK_TO_MARKER_SIZE.get(rank_as_int, _DEFAULT_MARKER_SIZE)

    def _get_node_sizes(self):
        '''
        Return a list of marker sizes (points^2) for all positioned nodes,
        in the same iteration order as self.pos.

        Returns: list[int]
        '''
        rank_attributes = nx.get_node_attributes(self.G, "rank")
        return [self._size_from_rank(rank_attributes.get(node_id, 0)) for node_id in self.pos]

    def _format_distance(self, distance_value):
        '''
        Format a distance value for stdout display.
        Integer values (or floats within floating-point precision of an integer)
        are printed without decimals; all other values are printed with 3 decimal places.

        distance_value: int or float -- distance value to format.

        Returns: str
        '''
        if isinstance(distance_value, int) or abs(distance_value - round(distance_value)) < 1e-9:
            return f"{int(round(distance_value))}"
        return f"{distance_value:.3f}"

    ###################################################################
    ##### Shared drawing helpers ######################################
    ###################################################################

    def _setup_axes(self, title="", figsize=_FIGURE_SIZE):
        '''
        Create a matplotlib Figure and Axes with a black background,
        matching the default NetLogo world appearance.

        title:   str   -- optional plot title displayed in white text.
        figsize: tuple -- (width, height) in inches.

        Returns: tuple(matplotlib.figure.Figure, matplotlib.axes.Axes)
        '''
        fig, ax = plt.subplots(figsize=figsize)

        ### black figure and axes backgrounds to match the NetLogo world
        fig.patch.set_facecolor("black")
        ax.set_facecolor("black")

        ### equal aspect ratio preserves geographic proportions;
        ### axis labels and ticks are hidden for a clean map appearance
        ax.set_aspect("equal")
        ax.axis("off")

        if title:
            ax.set_title(title, color="white", fontsize=11)

        return fig, ax

    def _draw_edges(self, ax, route_color_map, default_nl_color=_DEFAULT_NL_COLOR, linewidth=_EDGE_LINEWIDTH):
        '''
        Draw all graph edges as matplotlib LineCollections, grouped by colour.
        Grouping into LineCollections (instead of one artist per edge) greatly
        reduces the number of matplotlib objects and improves rendering performance.

        ax:               matplotlib.axes.Axes -- target axes object.
        route_color_map:  dict {str: tuple} -- maps route-type strings to (R,G,B) tuples.
        default_nl_color: float -- NetLogo colour value for route types not in the map.
        linewidth:        float -- line width in points.
        '''
        ### group edge coordinate segments by their display colour
        segments_by_color: dict[tuple, list] = {}
        default_rgb = _nl_color(default_nl_color)

        for source_node, target_node, edge_data in self.G.edges(data=True):
            ### skip edges whose endpoint nodes have no position (cannot be drawn)
            if source_node not in self.pos or target_node not in self.pos:
                continue
            ### look up the route type colour; use the default if the type is not mapped
            route_type = edge_data.get("route-type", "")
            rgb_color = route_color_map.get(route_type, default_rgb)
            segments_by_color.setdefault(rgb_color, []).append(
                [self.pos[source_node], self.pos[target_node]]
            )

        ### add one LineCollection per unique colour to the axes
        for rgb_color, segments in segments_by_color.items():
            ax.add_collection(
                LineCollection(
                    segments,
                    colors=[rgb_color] * len(segments),
                    linewidths=linewidth,
                    zorder=1,   # edges drawn below nodes (zorder 3)
                )
            )

    def _draw_nodes(self, ax, node_colors, sizes=None):
        '''
        Draw settlement nodes as house-shaped scatter markers.

        ax:          matplotlib.axes.Axes -- target axes object.
        node_colors: list[tuple] -- (R,G,B) colour tuples, one per node in self.pos order.
        sizes:       list[int] or None -- marker sizes in points^2; defaults to rank-based sizes.
        '''
        if sizes is None:
            sizes = self._get_node_sizes()

        ### extract x and y coordinates in the same iteration order as self.pos
        x_coords = [self.pos[node_id][0] for node_id in self.pos]
        y_coords = [self.pos[node_id][1] for node_id in self.pos]

        ### ax.scatter accepts a matplotlib Path object as the 'marker' argument,
        ### enabling the custom house shape defined in the HOUSE constant above
        ax.scatter(
            x_coords, y_coords,
            s=sizes,
            c=node_colors,
            marker=HOUSE,
            linewidths=_NODE_EDGE_LINEWIDTH,
            edgecolors="white",
            zorder=3,   # nodes drawn above edges (zorder 1)
        )

    ###################################################################
    ##### Analysis methods ############################################
    ###################################################################

    def analyse_distance_to_rome(self, weight_attr: str | None = None):
        '''
        Compute shortest-path distances from all settlements to Rome and print
        the closest settlement, the furthest settlement, and the distance to Alexandria.

        Replicates four NetLogo procedures:
          analysis-distance         (weight_attr=None  -- unweighted hop count)
          analysis-distance-km      (weight_attr='km')
          analysis-distance-days    (weight_attr='days')
          analysis-distance-expense (weight_attr='expense')

        weight_attr: str or None
            Edge attribute to use as distance weight.
            None     : unweighted shortest paths (each edge counts as 1 hop).
            'km'     : weighted by route length in kilometres.
            'days'   : weighted by travel time in days.
            'expense': weighted by cost index.

        Prints results to stdout. Returns None.
        '''
        ### reverse the graph so a single-source search starting at Rome
        ### yields distances from all other nodes TO Rome
        ### (equivalent to searching paths TO Rome in the original directed graph)
        reversed_graph = self.G.reverse()

        if weight_attr is None:
            ### unweighted: each edge contributes 1 to the path length
            distances = nx.single_source_shortest_path_length(reversed_graph, self.rome_node)
        else:
            ### weighted: Dijkstra's algorithm using the specified edge attribute
            distances = nx.single_source_dijkstra_path_length(
                reversed_graph, self.rome_node, weight=weight_attr
            )

        ### find the closest and furthest reachable settlements
        closest_node  = min(distances, key=distances.get)
        furthest_node = max(distances, key=distances.get)

        def get_settlement_name(node_id):
            ### retrieve the human-readable settlement name from node attributes
            return self.G.nodes[node_id].get(self.name_attr, str(node_id))

        print(f"closest settlement:  {get_settlement_name(closest_node)}, "
              f"{self._format_distance(distances[closest_node])}")
        print(f"furthest settlement: {get_settlement_name(furthest_node)}, "
              f"{self._format_distance(distances[furthest_node])}")
        print(f"distance Alexandria: {self._format_distance(distances[self.alex_node])}")

    ###################################################################
    ##### Visualisation methods #######################################
    ###################################################################

    def plot_network(self):
        '''
        Plot the Roman transport network coloured by route type.

        Replicates the NetLogo 'visualise' procedure:
          - House-shaped nodes sized by settlement rank, filled in default grey.
          - Edges coloured by route type:
              roads        -> dark grey (NetLogo colour 3)
              sea routes   -> sky blue  (NetLogo colour 95)
              river routes -> white     (NetLogo colour 9.9)
        '''
        _, ax = self._setup_axes("Roman transport network (visualise)")

        ### build a route-type -> matplotlib RGB colour map from the NetLogo colour values
        edge_color_map = {route: _nl_color(nl_val) for route, nl_val in _ROUTE_NL_COLOR.items()}
        self._draw_edges(ax, edge_color_map, default_nl_color=_DEFAULT_NL_COLOR)

        ### all nodes use the default grey -- the NetLogo 'visualise' procedure
        ### assigns no province-based colour to nodes
        node_rgb = _nl_color(_DEFAULT_NL_COLOR)
        self._draw_nodes(ax, [node_rgb] * len(self.pos))

        plt.tight_layout()
        plt.show()

    def plot_provinces(self):
        '''
        Plot the Roman transport network with settlements coloured by province.

        Replicates the NetLogo 'provinces' procedure:
          - House-shaped nodes coloured by Roman province using exact NetLogo colour values.
          - Nodes with an unrecognised or missing province fall back to default grey.
          - Edges coloured by route type (same colour scheme as plot_network).
        '''
        _, ax = self._setup_axes("Roman transport network - provinces")

        ### edges: same route-type colour scheme as plot_network
        edge_color_map = {route: _nl_color(nl_val) for route, nl_val in _ROUTE_NL_COLOR.items()}
        self._draw_edges(ax, edge_color_map, default_nl_color=_DEFAULT_NL_COLOR)

        ### nodes: map each settlement to its province colour; fall back to grey if unknown
        default_rgb = _nl_color(_DEFAULT_NL_COLOR)
        node_colors = []
        for node_id in self.pos:
            province_name = self.G.nodes[node_id].get("province", "")
            if province_name in _PROVINCE_NL_COLOR:
                node_colors.append(_nl_color(_PROVINCE_NL_COLOR[province_name]))
            else:
                node_colors.append(default_rgb)

        self._draw_nodes(ax, node_colors)

        plt.tight_layout()
        plt.show()

    def plot_distance_map(self, weight_attr: str | None = None):
        '''
        Plot a greyscale distance map showing how far each settlement is from Rome.

        Replicates four NetLogo procedures:
          visualise-distance         (weight_attr=None  -- unweighted hop count)
          visualise-distance-km      (weight_attr='km')
          visualise-distance-days    (weight_attr='days')
          visualise-distance-expense (weight_attr='expense')

        Node colours use the exact NetLogo greyscale formula:
          netlogo_color = max(0, 9.9 - (distance / max_distance) x 10)
        The closest settlement maps to white (9.9); the furthest maps to black (0).
        Unreachable settlements are drawn black.

        Edges are drawn black and are invisible against the black background,
        matching the NetLogo procedure behaviour.

        weight_attr: str or None
            Edge attribute to use as distance weight.
            None     : unweighted shortest paths (each edge counts as 1 hop).
            'km'     : weighted by route length in kilometres.
            'days'   : weighted by travel time in days.
            'expense': weighted by cost index.
        '''
        ### reverse the graph to compute distances from Rome to all nodes
        reversed_graph = self.G.reverse()

        if weight_attr is None:
            distances = nx.single_source_shortest_path_length(reversed_graph, self.rome_node)
            plot_title = "Distance to Rome (unweighted)"
        else:
            distances = nx.single_source_dijkstra_path_length(
                reversed_graph, self.rome_node, weight=weight_attr
            )
            plot_title = f"Distance to Rome - {weight_attr}"

        ### find the maximum distance value for normalisation
        max_distance = max(distances.values()) if distances else 1

        _, ax = self._setup_axes(plot_title)

        ### edges: drawn black, invisible against the black background (matches NetLogo)
        self._draw_edges(ax, {}, default_nl_color=0, linewidth=0.3)

        ### assign a greyscale NetLogo colour to each node using the NetLogo formula
        node_colors = []
        for node_id in self.pos:
            node_distance = distances.get(node_id)
            if node_distance is None:
                ### unreachable node -> black (NetLogo colour 0)
                node_colors.append(_nl_color(0))
            else:
                ### apply exact NetLogo greyscale formula:
                ### closer to Rome -> higher value -> lighter (white = 9.9)
                ### farther from Rome -> lower value -> darker (black = 0)
                nl_grey_value = max(0.0, _NL_GREY_MAX - (node_distance / max_distance) * _NL_GROUP_SIZE)
                node_colors.append(_nl_color(nl_grey_value))

        self._draw_nodes(ax, node_colors)

        plt.tight_layout()
        plt.show()


###############################################################################
##### Script entry point ######################################################
###############################################################################

if __name__ == "__main__":
    ### locate the ORBIS graphml file relative to this script's directory,
    ### so the module works regardless of where it is installed
    _script_directory = pathlib.Path(__file__).parent
    model = RomanTransportNetwork(str(_script_directory / "orbis.graphml"))

    ### distance analyses -- results can be compared with the NetLogo output
    print("Unweighted (NetLogo: analysis-distance):")
    model.analyse_distance_to_rome(weight_attr=None)

    print("\nWeighted by days (NetLogo: analysis-distance-days):")
    model.analyse_distance_to_rome(weight_attr="days")

    print("\nWeighted by km (NetLogo: analysis-distance-km):")
    model.analyse_distance_to_rome(weight_attr="km")

    print("\nWeighted by expense (NetLogo: analysis-distance-expense):")
    model.analyse_distance_to_rome(weight_attr="expense")

    ### visualisations -- each method replicates one NetLogo procedure
    model.plot_network()                           # visualise
    model.plot_provinces()                         # provinces
    model.plot_distance_map(weight_attr=None)      # visualise-distance
    model.plot_distance_map(weight_attr="km")      # visualise-distance-km
    model.plot_distance_map(weight_attr="days")    # visualise-distance-days
    model.plot_distance_map(weight_attr="expense") # visualise-distance-expense
