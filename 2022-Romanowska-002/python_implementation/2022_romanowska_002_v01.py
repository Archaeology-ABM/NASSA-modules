# =============================================================================
# Module: 2022_romanowska_002_v01.py
# Title : Out of Africa - Conditional isotropic diffusion (Python reimplementation)
# Module ID (NASSA): 2022-Romanowska-002
# Module version   : 1.2.0  (incremented from 1.1.0 for this Python implementation)
#
# Python implementation contributor:
#     João Messias Sousa da Silva
#     Email : j.m.sousadasilva@vu.nl
#     ORCID : 0009-0007-4716-3957
# Creation date: 2025
#
# Original NetLogo module authors:
#     Iza Romanowska  (ORCID 0000-0002-9487-2111)
#     Colin D. Wren   (ORCID 0000-0003-4940-3997)
#     Stefani A. Crabtree (ORCID 0000-0001-8585-8943)
# Contributor:
#     Andreas Angourakis (ORCID 0000-0002-9946-8142)
#
# References:
#   - Romanowska, I., Wren, C., Crabtree, S. 2021. Agent-Based Modeling for
#     Archaeology: Simulating the Complexity of Societies. SFI Press.
#     https://www.sfipress.org/books/agent-based-modeling-archaeology
#   - Young, D. A., & Bettinger, R. L. (1992). The Numic spread: a computer
#     simulation. American Antiquity, 57(1), 85-99.
#   - NASSA guide: https://archaeology-abm.github.io/NASSA-hub/guide
#   - Original NetLogo source repository:
#     https://github.com/SantaFeInstitute/ABMA/blob/master/ch1
#
# Replicated NetLogo procedures:
#   - setup               -> OutOfAfricaModel.setup()
#   - go                  -> OutOfAfricaModel.go()
#   - reproduce-population-> OutOfAfricaModel.reproduce_population()
#   - try-to-reproduce    -> Turtle.try_to_reproduce()
#   - reproduce-at        -> Turtle.reproduce_at()
#
# Python dependencies:
#   - Python >= 3.9
#   - numpy
#   - matplotlib
#   - Pillow (PIL)    (to load the world image; stdlib fallback not provided)
#
# License: CC-BY-SA-4.0
# =============================================================================

import argparse
import random
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

### ========== NAMED CONSTANTS ========== ###

### Default simulation parameters (replicating NetLogo interface sliders/inputs)
DEFAULT_NUMBER_OF_TURTLES = 20          ### number of initial turtles (NetLogo: numberOfTurtles)
DEFAULT_INPUT_X = 361                   ### initial x of seeding centre (NetLogo: inputX)
DEFAULT_INPUT_Y = 176                   ### initial y of seeding centre (NetLogo: inputY)
DEFAULT_MAX_INITIAL_DIST = 2            ### maximum radius around seeding centre
DEFAULT_POP_GROWTH = 0.30               ### reproduction probability per tick (NetLogo: pop_growth)
DEFAULT_NUM_TICKS = 700                 ### number of simulation steps to run
DEFAULT_WORLD_WIDTH = 600               ### grid width when no image is loaded
DEFAULT_WORLD_HEIGHT = 351              ### grid height when no image is loaded
DEFAULT_RANDOM_SEED = 42                ### deterministic seed for reproducibility

### NetLogo-specific constants
NETLOGO_COLOUR_MAX = 140                ### exclusive upper bound of NetLogo colour palette
NETLOGO_WHITE_INT = 9.9                 ### NetLogo code for white (sea in the input map)
COLOUR_INCREMENT_ON_HATCH = 0.1         ### color offset applied when a turtle reproduces

### Visualisation constants
SEA_RGB_THRESHOLD = 240                 ### pixel channel >= this value is treated as "white sea"
TURTLE_SIZE_PATCHES = 2.0                ### NetLogo `set size 2` (patch size is 1 px in the .nlogo view)

### CHOOSER options: the NetLogo interface does not expose an explicit chooser, but the
### "map scenario" selection is effectively a chooser between loading an external image
### and generating a synthetic world. We expose both options and iterate over them.
MAP_SCENARIO_OPTIONS = ["synthetic", "external_image"]


### ========== HELPER: NetLogo colour conversion ========== ###

### Official NetLogo palette, extracted with `extract-rgb` in NetLogo 7.0.4 for
### color = 0.0, 0.1, ..., 139.9 (1400 entries). See data/netlogo_palette_7.0.4.csv.
_DATA_DIR = Path(__file__).parent / "data"
_PALETTE_FILE = _DATA_DIR / "netlogo_palette_7.0.4.csv"
### Exact `import-pcolors` result (RGB -> pcolor) from NetLogo 7.0.4 for the
### shipped world image. Used so the base map keeps NetLogo's own pcolors.
_PCOLOR_LOOKUP_FILE = _DATA_DIR / "import_pcolors_lookup_worldAboveSeaLevelElevation.csv"

_PALETTE_RGB = None   ### lazily-loaded (1400, 3) uint8 array


def _load_palette() -> np.ndarray:
    """Load the NetLogo palette table (index = round(color * 10))."""
    global _PALETTE_RGB
    if _PALETTE_RGB is None:
        table = np.loadtxt(_PALETTE_FILE, delimiter=",", skiprows=2)
        _PALETTE_RGB = table[:, 1:4].astype(np.uint8)
    return _PALETTE_RGB


def netlogo_color_to_rgb(n) -> tuple:
    """NetLogo colour number (any float) -> (r, g, b) from the official palette.
    NetLogo wraps colours into [0, 140); resolution is 0.1."""
    idx = int(round((float(n) % NETLOGO_COLOUR_MAX) * 10)) % 1400
    r, g, b = _load_palette()[idx]
    return int(r), int(g), int(b)


def netlogo_color_to_hex(n) -> str:
    """NetLogo colour number -> '#RRGGBB' using the official NetLogo palette."""
    r, g, b = netlogo_color_to_rgb(n)
    return f"#{r:02X}{g:02X}{b:02X}"


### ========== DOMAIN CLASSES ========== ###

class Turtle:
    """
    A NetLogo turtle (agent) in the Out-of-Africa model.

    Attributes
    ----------
    who : int
        Unique turtle identifier (replicates NetLogo's `who`).
    x : float
        Continuous x coordinate (NetLogo xcor).
    y : float
        Continuous y coordinate (NetLogo ycor).
    color : float
        NetLogo colour code (lineage proxy).
    size : float
        Display size.
    shape : str
        Shape identifier ("turtle").
    model : OutOfAfricaModel
        Back-reference to the owning model.

    Methods
    -------
    try_to_reproduce():
        Attempt reproduction into an adjacent free land patch.
    reproduce_at(px, py):
        Hatch a clone at a specified patch (replicates NetLogo reproduce-at).
    """

    def __init__(self, who: int, x: float, y: float, color: float,
                 model: "OutOfAfricaModel"):
        ### Declare every attribute here to avoid AttributeError later
        self.who = who
        self.x = x
        self.y = y
        self.color = color
        self.size = 2.0
        self.shape = "turtle"
        self.model = model

    def try_to_reproduce(self) -> None:
        """
        Replicates NetLogo `try-to-reproduce`: with probability pop_growth,
        pick a random adjacent (Von Neumann) free land patch and hatch there.
        """
        ### Reproduction probability check
        if self.model.rng.random() > self.model.pop_growth:
            return

        ### Determine current patch coordinates (NetLogo patch-here)
        cx = int(round(self.x)) % self.model.world_width
        cy = int(round(self.y))

        ### neighbors4 = N, S, E, W. The .nlogo world wraps horizontally only
        ### (wrap-x on, wrap-y off), so patches beyond the top/bottom edge do not exist.
        candidate_patches = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx = (cx + dx) % self.model.world_width
            ny = cy + dy
            if ny < 0 or ny >= self.model.world_height:
                continue
            ### Condition: no turtle currently on the patch AND patch is not sea (white)
            if self.model.is_land(nx, ny) and not self.model.patch_occupied(nx, ny):
                candidate_patches.append((nx, ny))

        if not candidate_patches:
            return

        ### one-of neighbors4: random choice
        tx, ty = self.model.rng.choice(candidate_patches)
        self.reproduce_at(tx, ty)

    def reproduce_at(self, px: int, py: int) -> None:
        """
        Replicates NetLogo `reproduce-at`: hatch 1 clone, slightly shift colour,
        move the hatchling to the given patch.

        Parameters
        ----------
        px : int
            Target patch x index.
        py : int
            Target patch y index.
        """
        ### NetLogo: set color color + 0.1 (colours wrap into [0, 140));
        ### rounding to 0.1 avoids floating-point drift, the palette step is 0.1
        new_color = round((self.color + COLOUR_INCREMENT_ON_HATCH) % NETLOGO_COLOUR_MAX, 1)
        child = Turtle(
            who=self.model.next_who(),
            x=float(px),
            y=float(py),
            color=new_color,
            model=self.model,
        )
        self.model.turtles.append(child)
        ### Mark patch as occupied in the occupancy map
        self.model.occupancy[py, px] = True


class OutOfAfricaModel:
    """
    Out-of-Africa conditional isotropic diffusion model.

    Attributes
    ----------
    world_width : int
        Grid width (number of patches along x).
    world_height : int
        Grid height (number of patches along y).
    pcolors : np.ndarray
        2D array (height, width) of NetLogo colour codes for each patch.
    is_land_mask : np.ndarray
        Boolean 2D array (height, width); True for land patches.
    occupancy : np.ndarray
        Boolean 2D array (height, width); True where a turtle currently sits.
    turtles : list[Turtle]
        List of all turtles in the world.
    number_of_turtles : int
        Initial number of turtles.
    input_x : int
        Seeding centre x.
    input_y : int
        Seeding centre y.
    max_initial_distance : int
        Max radius for initial placement.
    pop_growth : float
        Probability of reproduction per tick.
    tick_counter : int
        Current simulation step count.
    rng : random.Random
        Deterministic random generator.
    population_history : list[int]
        Number of turtles at the end of each tick.
    map_scenario : str
        'synthetic' or 'external_image'.
    _who_counter : int
        Internal unique-ID counter for turtles.

    Methods
    -------
    setup(): Initialise world and place turtles.
    go(): Advance one tick.
    reproduce_population(): Ask every turtle to try reproducing.
    run(n_ticks): Advance the model for n_ticks steps.
    is_land(px, py): True if the patch is land (not sea).
    patch_occupied(px, py): True if a turtle sits on the patch.
    next_who(): Return a new unique turtle id.
    visualise(save_path=None): Display plots of final state and growth.
    summary(): Print a textual summary of key outputs.
    """

    def __init__(self,
                 number_of_turtles: int = DEFAULT_NUMBER_OF_TURTLES,
                 input_x: int = DEFAULT_INPUT_X,
                 input_y: int = DEFAULT_INPUT_Y,
                 max_initial_distance: int = DEFAULT_MAX_INITIAL_DIST,
                 pop_growth: float = DEFAULT_POP_GROWTH,
                 world_width: int = DEFAULT_WORLD_WIDTH,
                 world_height: int = DEFAULT_WORLD_HEIGHT,
                 map_scenario: str = "synthetic",
                 world_image_path: str = None,
                 random_seed: int = DEFAULT_RANDOM_SEED):
        ### Declare EVERY attribute up front (NASSA rule: avoid AttributeError)
        self.world_width = world_width
        self.world_height = world_height
        self.pcolors = np.zeros((world_height, world_width), dtype=float)
        self.is_land_mask = np.ones((world_height, world_width), dtype=bool)
        self.occupancy = np.zeros((world_height, world_width), dtype=bool)
        self.turtles = []
        self.number_of_turtles = number_of_turtles
        self.input_x = input_x
        self.input_y = input_y
        self.max_initial_distance = max_initial_distance
        self.pop_growth = pop_growth
        self.tick_counter = 0
        self.rng = random.Random(random_seed)
        self.population_history = []
        self.map_scenario = map_scenario
        self.world_image_path = world_image_path
        self._who_counter = 0

    ### ---------- utility ---------- ###

    def next_who(self) -> int:
        """Return a fresh unique turtle id (mimics NetLogo `who`)."""
        wid = self._who_counter
        self._who_counter += 1
        return wid

    def is_land(self, px: int, py: int) -> bool:
        """True if the patch at (px, py) is land (not sea)."""
        px = px % self.world_width
        if py < 0 or py >= self.world_height:
            return False
        return bool(self.is_land_mask[py, px])

    def patch_occupied(self, px: int, py: int) -> bool:
        """True if a turtle currently sits on patch (px, py)."""
        px = px % self.world_width
        if py < 0 or py >= self.world_height:
            return False
        return bool(self.occupancy[py, px])

    ### ---------- world initialisation ---------- ###

    def _load_world_from_image(self, image_path: str) -> None:
        """
        Replicates NetLogo `import-pcolors`: load an image, resize to the world,
        convert white-ish pixels to sea (pcolor = NETLOGO_WHITE_INT) and
        everything else to land. Land patches get a NetLogo-ish green colour.
        """
        img = Image.open(image_path).convert("RGB")
        ### Resize so that the grid matches the image, or vice versa
        img = img.resize((self.world_width, self.world_height), Image.NEAREST)
        ### Image row 0 is the TOP, but the grid has y=0 at the BOTTOM (as in
        ### NetLogo), so flip vertically to keep the map right-side up.
        arr = np.flipud(np.asarray(img)).astype(np.int64)  ### shape (H, W, 3)
        ### Base-map colours (pcolor): exact NetLogo import-pcolors result where
        ### known, nearest palette colour (RGB distance) otherwise.
        self.pcolors = self._rgb_to_netlogo_pcolor(arr)
        ### NetLogo rule: land = pcolor != white
        self.is_land_mask = self.pcolors != NETLOGO_WHITE_INT

    @staticmethod
    def _rgb_to_netlogo_pcolor(arr: np.ndarray) -> np.ndarray:
        """Map an (H, W, 3) RGB array to NetLogo pcolor numbers.

        NOTE: the exact nearest-colour rule inside NetLogo's import-pcolors was
        not reverse-engineered. For the shipped image every RGB value is looked
        up in a table produced by NetLogo 7.0.4 itself (exact). Unknown RGB
        values fall back to the nearest entry of the official palette
        (approximate, base-map appearance only; pure white stays exact: 9.9).
        """
        lookup = {}
        if _PCOLOR_LOOKUP_FILE.exists():
            data = np.loadtxt(_PCOLOR_LOOKUP_FILE, delimiter=",", skiprows=2)
            lookup = {(int(r), int(g), int(b)): float(c) for r, g, b, c in data}
        palette = _load_palette().astype(np.int64)
        codes = np.arange(1400) / 10.0
        flat = arr.reshape(-1, 3)
        uniq, inv = np.unique(flat, axis=0, return_inverse=True)
        out = np.empty(len(uniq))
        for i, (r, g, b) in enumerate(uniq):
            key = (int(r), int(g), int(b))
            if key in lookup:
                out[i] = lookup[key]
            elif key == (255, 255, 255):
                out[i] = NETLOGO_WHITE_INT
            else:
                out[i] = codes[((palette - uniq[i]) ** 2).sum(1).argmin()]
        return out[inv.reshape(-1)].reshape(arr.shape[:2])

    def _build_synthetic_world(self) -> None:
        """
        Build a synthetic world: a large land continent with a surrounding
        sea strip. This provides a standalone-runnable example when no
        external image is supplied.
        """
        ### Fill everything with land (green)
        self.pcolors[:, :] = 55.0
        self.is_land_mask[:, :] = True
        ### Create a sea border and a couple of islands/water bodies
        border = 5
        self.pcolors[:border, :] = NETLOGO_WHITE_INT
        self.pcolors[-border:, :] = NETLOGO_WHITE_INT
        self.pcolors[:, :border] = NETLOGO_WHITE_INT
        self.pcolors[:, -border:] = NETLOGO_WHITE_INT
        self.is_land_mask[:border, :] = False
        self.is_land_mask[-border:, :] = False
        self.is_land_mask[:, :border] = False
        self.is_land_mask[:, -border:] = False
        ### Add a small inland sea (water barrier) to make diffusion non-trivial
        sea_y0, sea_y1 = self.world_height // 3, self.world_height // 3 + 15
        sea_x0, sea_x1 = self.world_width // 2, self.world_width // 2 + 40
        self.pcolors[sea_y0:sea_y1, sea_x0:sea_x1] = NETLOGO_WHITE_INT
        self.is_land_mask[sea_y0:sea_y1, sea_x0:sea_x1] = False

    def setup(self) -> None:
        """
        Replicates NetLogo `setup`: clear world, load spatial input, place
        `number_of_turtles` within max_initial_distance of (input_x, input_y),
        reset tick counter.
        """
        ### Reset state
        self.turtles = []
        self.occupancy[:, :] = False
        self.tick_counter = 0
        self.population_history = []
        self._who_counter = 0

        ### Load / build world
        if self.map_scenario == "external_image" and self.world_image_path is not None:
            try:
                self._load_world_from_image(self.world_image_path)
            except (FileNotFoundError, OSError) as err:
                ### Fall back to synthetic world if the image cannot be loaded
                print(f"[WARN] Could not load '{self.world_image_path}': {err}. "
                      "Falling back to synthetic world.")
                self._build_synthetic_world()
        else:
            self._build_synthetic_world()

        ### Place the initial turtles.
        ### NetLogo: `set color random 140` (INTEGER 0..139) and `setxy x y`.
        ### The .nlogo computes thisAgentX/thisAgentY but never uses them, so all
        ### initial turtles start on the same point (inputX, inputY).
        for _ in range(self.number_of_turtles):
            color = float(self.rng.randrange(NETLOGO_COLOUR_MAX))
            turtle = Turtle(
                who=self.next_who(),
                x=float(self.input_x),
                y=float(self.input_y),
                color=color,
                model=self,
            )
            self.turtles.append(turtle)
            self.occupancy[int(self.input_y), int(self.input_x) % self.world_width] = True

        ### Record tick-0 population
        self.population_history.append(len(self.turtles))

    ### ---------- simulation loop ---------- ###

    def reproduce_population(self) -> None:
        """Replicates NetLogo `reproduce-population`: ask every turtle to try reproducing."""
        ### Snapshot the current turtle list: NetLogo semantics is to iterate
        ### over the agentset as it was at the start of the ask; new hatchlings
        ### do not act in the same tick.
        current = list(self.turtles)
        for turtle in current:
            turtle.try_to_reproduce()

    def go(self) -> None:
        """Replicates NetLogo `go`: one simulation step."""
        self.reproduce_population()
        self.tick_counter += 1
        self.population_history.append(len(self.turtles))

    def run(self, n_ticks: int) -> None:
        """Run the simulation for n_ticks steps."""
        for _ in range(n_ticks):
            self.go()

    ### ---------- reporting & visualisation ---------- ###

    def summary(self) -> None:
        """Print a concise summary of key outputs."""
        print("=" * 60)
        print(f"Out-of-Africa model summary (scenario: {self.map_scenario})")
        print("-" * 60)
        print(f"World size            : {self.world_width} x {self.world_height}")
        print(f"Initial turtles       : {self.number_of_turtles}")
        print(f"Seed point (x, y)     : ({self.input_x}, {self.input_y})")
        print(f"Max initial distance  : {self.max_initial_distance}")
        print(f"pop_growth            : {self.pop_growth}")
        print(f"Ticks elapsed         : {self.tick_counter}")
        print(f"Final population      : {len(self.turtles)}")
        ### Count distinct ancestral colours (rough lineage proxy: integer base colour)
        base_colours = {int(t.color // 10) * 10 for t in self.turtles}
        print(f"Distinct base colours : {len(base_colours)}")
        occupied_land = int(np.sum(self.occupancy & self.is_land_mask))
        total_land = int(np.sum(self.is_land_mask))
        if total_land > 0:
            pct = 100.0 * occupied_land / total_land
            print(f"Land cells occupied   : {occupied_land}/{total_land} "
                  f"({pct:.2f}% of land)")
        print("=" * 60)

    def _build_patch_rgb(self) -> np.ndarray:
        """Base map: each patch painted with its own pcolor (official palette)."""
        palette = _load_palette()
        idx = np.rint(self.pcolors * 10).astype(int) % 1400
        return palette[idx].astype(float) / 255.0

    def _render_world(self, supersample: int = 4) -> np.ndarray:
        """Base map + agents as an RGB image (origin lower-left).

        The NetLogo view uses patch size 1 and turtles of size 2, so each agent
        covers a 2x2-patch square centred on its position. Agents are painted in
        `who` order (later on top) on a supersampled canvas without smoothing.
        """
        S = supersample
        base = self._build_patch_rgb()
        canvas = np.repeat(np.repeat(base, S, axis=0), S, axis=1)
        h, w = canvas.shape[:2]
        half = TURTLE_SIZE_PATCHES / 2.0
        for t in self.turtles:
            r, g, b = netlogo_color_to_rgb(t.color)
            x0 = int(round((t.x + 0.5 - half) * S)); x1 = int(round((t.x + 0.5 + half) * S))
            y0 = int(round((t.y + 0.5 - half) * S)); y1 = int(round((t.y + 0.5 + half) * S))
            ### sprite is clipped at the edges (no wrapping of the drawing itself)
            canvas[max(y0, 0):min(y1, h), max(x0, 0):min(x1, w)] = (r / 255.0, g / 255.0, b / 255.0)
        return canvas

    def visualise(self, save_path: str = None) -> None:
        """
        Visualise the current model state: world grid with turtles, and a
        population-over-time curve. Calls plt.show() to display interactively.

        Parameters
        ----------
        save_path : str or None
            If provided, also save the figure to this path.
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        ### -------- Panel 1: world + turtles --------
        ax_world = axes[0]
        ### NetLogo grid: (0,0) at bottom-left -> origin='lower'
        ax_world.imshow(self._render_world(), origin="lower", interpolation="nearest",
                        extent=[-0.5, self.world_width - 0.5, -0.5, self.world_height - 0.5])
        ### Mark the seeding point with an "X" label (NetLogo plabel)
        ax_world.text(self.input_x, self.input_y, "X",
                      color="black", fontsize=14, fontweight="bold",
                      ha="center", va="center")
        ax_world.set_title(f"Out of Africa — scenario: {self.map_scenario}\n"
                           f"tick={self.tick_counter}, N={len(self.turtles)}")
        ax_world.set_xlabel("x (patches)")
        ax_world.set_ylabel("y (patches)")
        ax_world.set_xlim(-0.5, self.world_width - 0.5)
        ax_world.set_ylim(-0.5, self.world_height - 0.5)
        ax_world.set_aspect("equal")

        ### -------- Panel 2: population over time --------
        ax_pop = axes[1]
        ax_pop.plot(range(len(self.population_history)),
                    self.population_history,
                    color=netlogo_color_to_hex(105),  ### NetLogo blue
                    linewidth=2.0, marker="o", markersize=3)
        ax_pop.set_title("Population over time")
        ax_pop.set_xlabel("Tick")
        ax_pop.set_ylabel("Number of turtles")
        ax_pop.grid(True, linestyle="--", alpha=0.5)

        fig.tight_layout()

        ### Only save when caller explicitly requests it
        if save_path is not None:
            fig.savefig(save_path, dpi=150)

        ### Always display interactively
        plt.show()


### ========== MAIN ENTRY POINT ========== ###

def _parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Out of Africa - Conditional isotropic diffusion "
                    "(NASSA Python reimplementation)."
    )
    parser.add_argument(
        "--scenario",
        choices=MAP_SCENARIO_OPTIONS + ["all"],
        default="all",
        help="Which map scenario to run. 'all' runs every option (default).",
    )
    parser.add_argument(
        "--ticks", type=int, default=DEFAULT_NUM_TICKS,
        help=f"Number of simulation ticks (default: {DEFAULT_NUM_TICKS}).",
    )
    return parser.parse_args()


def _default_image_path() -> str:
    """
    Return the external world-image path. The NetLogo module expects a PNG
    (e.g. 'world.png' or 'ch1_map.png'). By default it uses the
    'worldAboveSeaLevelElevation.png' file shipped next to this script.
    """
    # Edit the file name below to use a different land/sea map.
    data_path = Path(__file__).parent / "worldAboveSeaLevelElevation.png"
    return str(data_path)


def main() -> None:
    """Entry point: iterate over all chooser options (map scenarios) by default."""
    args = _parse_args()

    ### Decide which scenarios to run
    if args.scenario == "all":
        scenarios_to_run = MAP_SCENARIO_OPTIONS
    else:
        scenarios_to_run = [args.scenario]

    for scenario in scenarios_to_run:
        print(f"\n>>> Running scenario: {scenario}")
        model = OutOfAfricaModel(
            number_of_turtles=DEFAULT_NUMBER_OF_TURTLES,
            input_x=DEFAULT_INPUT_X,
            input_y=DEFAULT_INPUT_Y,
            max_initial_distance=DEFAULT_MAX_INITIAL_DIST,
            pop_growth=DEFAULT_POP_GROWTH,
            world_width=DEFAULT_WORLD_WIDTH,
            world_height=DEFAULT_WORLD_HEIGHT,
            map_scenario=scenario,
            world_image_path=_default_image_path() if scenario == "external_image" else None,
            random_seed=DEFAULT_RANDOM_SEED,
        )
        model.setup()
        model.run(args.ticks)
        model.summary()
        ### Visualise interactively (plt.show inside)
        model.visualise()


if __name__ == "__main__":
    main()