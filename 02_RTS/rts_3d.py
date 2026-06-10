from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pyglet
from pyglet import gl
from pyglet.graphics.shader import Shader, ShaderProgram
from pyglet.math import Mat4, Vec3


WIDTH = 1280
HEIGHT = 760
HUD_HEIGHT = 168
WORLD_SIZE = 120.0
WORLD_HALF = WORLD_SIZE / 2
CAMERA_SPEED = 24.0
EDGE_SCROLL_SIZE = 18
FOV_DEGREES = 52.0
MINIMAP_RECT = (18, 18, 132, 132)
COMMAND_GRID = (1004, 28, 64, 42, 3, 3)
TITLE = "RTS - 3D Prototype"

PLAYER = "player"
ENEMY = "enemy"
RACE_ORDER = ["Human", "Orc", "Undead", "Night Elf"]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def dist2(a_x: float, a_z: float, b_x: float, b_z: float) -> float:
    return math.hypot(a_x - b_x, a_z - b_z)


def terrain_height(x: float, z: float) -> float:
    ridge = math.sin(x * 0.12) * 0.34 + math.cos(z * 0.10) * 0.26
    roll = math.sin((x + z) * 0.075) * 0.22 + math.cos((x - z) * 0.055) * 0.18
    height = ridge + roll + terrain_level_height(x, z)
    if abs(x) < 4.2:
        height = min(height, -0.22)
    return clamp(height, -1.15, 2.15)


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    t = clamp((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def plateau(x: float, z: float, cx: float, cz: float, sx: float, sz: float, height: float) -> float:
    dx = abs(x - cx)
    dz = abs(z - cz)
    fx = 1.0 - smoothstep(sx * 0.70, sx, dx)
    fz = 1.0 - smoothstep(sz * 0.70, sz, dz)
    return height * min(fx, fz)


def terrain_level_height(x: float, z: float) -> float:
    highlands = plateau(x, z, -42, 34, 24, 18, 1.15) + plateau(x, z, 38, -30, 23, 20, 0.95)
    enemy_ridge = plateau(x, z, 48, 42, 18, 16, 0.65)
    valley = -0.42 * (1.0 - smoothstep(10, 24, abs(x + 8)))
    ramp_a = 0.55 * (smoothstep(-22, -8, x) - smoothstep(2, 16, x)) * (1.0 - smoothstep(8, 22, abs(z - 2)))
    return highlands + enemy_ridge + valley + ramp_a


@dataclass
class Thing:
    kind: str
    team: str
    x: float
    z: float
    radius: float
    hp: float
    max_hp: float
    speed: float = 0.0
    attack: float = 0.0
    attack_range: float = 0.0
    target_x: float | None = None
    target_z: float | None = None
    target: "Thing | None" = None
    selected: bool = False
    cooldown: float = 0.0
    queue: list[str] | None = None
    queue_timer: float = 0.0
    complete: bool = True
    build_time: float = 0.0
    build_progress: float = 0.0
    builder: "Thing | None" = None
    gather_target: "Decoration | None" = None
    gather_timer: float = 0.0
    carrying: float = 0.0
    rally_x: float | None = None
    rally_z: float | None = None

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def is_building(self) -> bool:
        return self.kind in BUILDINGS


@dataclass
class Decoration:
    kind: str
    x: float
    z: float
    scale: float = 1.0
    rotation: float = 0.0
    amount: float = 0.0

    @property
    def resource_kind(self) -> str | None:
        if self.kind == "gold":
            return "gold"
        if self.kind in {"tree", "pine"}:
            return "wood"
        return None


RACE_DEFS = {
    "Human": {
        "worker": "Peasant",
        "melee": "Footman",
        "ranged": "Archer",
        "heavy": "Knight",
        "hero": "Paladin",
        "hall": "Town Hall",
        "farm": "Farm",
        "barracks": "Barracks",
        "tower": "Guard Tower",
        "accent": (84, 170, 255),
    },
    "Orc": {
        "worker": "Peon",
        "melee": "Grunt",
        "ranged": "Troll Spearman",
        "heavy": "Raider",
        "hero": "Blademaster",
        "hall": "Great Hall",
        "farm": "Pig Farm",
        "barracks": "Barracks",
        "tower": "Watch Tower",
        "accent": (224, 72, 50),
    },
    "Undead": {
        "worker": "Acolyte",
        "melee": "Ghoul",
        "ranged": "Crypt Fiend",
        "heavy": "Abomination",
        "hero": "Death Knight",
        "hall": "Necropolis",
        "farm": "Ziggurat",
        "barracks": "Crypt",
        "tower": "Spirit Tower",
        "accent": (160, 92, 210),
    },
    "Night Elf": {
        "worker": "Wisp",
        "melee": "Huntress",
        "ranged": "Sentinel Archer",
        "heavy": "Dryad",
        "hero": "Keeper",
        "hall": "Tree of Life",
        "farm": "Moon Well",
        "barracks": "Ancient of War",
        "tower": "Ancient Protector",
        "accent": (92, 210, 150),
    },
}

UNIT_TEMPLATES = {
    "worker": dict(radius=0.65, hp=48, speed=6.8, attack=3, attack_range=1.2, cost_gold=55, cost_wood=0, food=1, time=5, mesh="Peasant"),
    "melee": dict(radius=0.78, hp=96, speed=5.9, attack=15, attack_range=1.35, cost_gold=90, cost_wood=15, food=2, time=7, mesh="Footman"),
    "ranged": dict(radius=0.68, hp=62, speed=6.1, attack=10, attack_range=8.5, cost_gold=80, cost_wood=35, food=2, time=6.5, mesh="Archer"),
    "heavy": dict(radius=0.95, hp=155, speed=7.5, attack=23, attack_range=1.55, cost_gold=165, cost_wood=45, food=3, time=11, mesh="Knight"),
    "hero": dict(radius=1.05, hp=260, speed=7.2, attack=30, attack_range=2.0, cost_gold=425, cost_wood=100, food=5, time=18, mesh="Knight"),
}

BUILDING_TEMPLATES = {
    "hall": dict(radius=2.7, hp=720, food=10, cost_gold=0, cost_wood=0, build_time=0, mesh="Town Hall"),
    "farm": dict(radius=1.6, hp=220, food=6, cost_gold=80, cost_wood=30, build_time=9, mesh="Farm"),
    "barracks": dict(radius=2.35, hp=460, food=0, cost_gold=210, cost_wood=160, build_time=18, mesh="Barracks"),
    "tower": dict(radius=1.45, hp=310, food=0, attack=16, attack_range=10.5, cost_gold=125, cost_wood=95, build_time=14, mesh="Tower"),
}


def build_unit_catalog() -> dict[str, dict[str, object]]:
    catalog: dict[str, dict[str, object]] = {}
    for race, defs in RACE_DEFS.items():
        for role in ("worker", "melee", "ranged", "heavy", "hero"):
            data = dict(UNIT_TEMPLATES[role])
            data["race"] = race
            data["role"] = role
            data["producer"] = defs["hall"] if role in {"worker", "hero"} else defs["barracks"]
            if race == "Orc":
                data["hp"] = int(data["hp"] * 1.10)
                data["attack"] = int(data["attack"] * 1.08)
                data["speed"] = float(data["speed"]) * 0.96
            elif race == "Undead":
                data["hp"] = int(data["hp"] * 0.94)
                data["attack"] = int(data["attack"] * 1.14)
            elif race == "Night Elf":
                data["speed"] = float(data["speed"]) * 1.08
                data["attack_range"] = float(data["attack_range"]) + (1.0 if role == "ranged" else 0.0)
            catalog[str(defs[role])] = data
    return catalog


def build_building_catalog() -> dict[str, dict[str, object]]:
    catalog: dict[str, dict[str, object]] = {}
    for race, defs in RACE_DEFS.items():
        for role in ("hall", "farm", "barracks", "tower"):
            data = dict(BUILDING_TEMPLATES[role])
            data["race"] = race
            data["role"] = role
            catalog[str(defs[role])] = data
    return catalog


UNITS = build_unit_catalog()
BUILDINGS = build_building_catalog()
TRAIN_TIME = {name: float(data["time"]) for name, data in UNITS.items()}


VERTEX_SHADER = """
#version 330 core
in vec3 position;
in vec4 color;
out vec4 vertex_color;
uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;
void main()
{
    gl_Position = projection * view * model * vec4(position, 1.0);
    vertex_color = color;
}
"""

FRAGMENT_SHADER = """
#version 330 core
in vec4 vertex_color;
out vec4 final_color;
void main()
{
    final_color = vertex_color;
}
"""


def cube_mesh(w: float, h: float, d: float, color: tuple[float, float, float, float]) -> tuple[list[float], list[float]]:
    x, y, z = w / 2, h, d / 2
    verts = [
        -x, 0, -z, x, 0, -z, x, y, -z, -x, 0, -z, x, y, -z, -x, y, -z,
        x, 0, z, -x, 0, z, -x, y, z, x, 0, z, -x, y, z, x, y, z,
        -x, 0, z, -x, 0, -z, -x, y, -z, -x, 0, z, -x, y, -z, -x, y, z,
        x, 0, -z, x, 0, z, x, y, z, x, 0, -z, x, y, z, x, y, -z,
        -x, y, -z, x, y, -z, x, y, z, -x, y, -z, x, y, z, -x, y, z,
        -x, 0, z, x, 0, z, x, 0, -z, -x, 0, z, x, 0, -z, -x, 0, -z,
    ]
    colors = list(color) * (len(verts) // 3)
    return verts, colors


def plane_mesh(size: float, color: tuple[float, float, float, float]) -> tuple[list[float], list[float]]:
    s = size / 2
    verts = [-s, 0, -s, s, 0, -s, s, 0, s, -s, 0, -s, s, 0, s, -s, 0, s]
    colors = list(color) * 6
    return verts, colors


def terrain_mesh(size: float, cells: int = 36) -> tuple[list[float], list[float]]:
    verts: list[float] = []
    colors: list[float] = []
    step = size / cells
    start = -size / 2
    palette = [
        (0.20, 0.34, 0.18, 1.0),
        (0.24, 0.39, 0.21, 1.0),
        (0.28, 0.43, 0.22, 1.0),
        (0.18, 0.30, 0.17, 1.0),
        (0.32, 0.39, 0.19, 1.0),
    ]
    for ix in range(cells):
        for iz in range(cells):
            x = start + ix * step
            z = start + iz * step
            noise = (ix * 17 + iz * 31 + (ix * iz) * 7) % len(palette)
            color = palette[noise]
            y00 = terrain_height(x, z)
            y10 = terrain_height(x + step, z)
            y11 = terrain_height(x + step, z + step)
            y01 = terrain_height(x, z + step)
            avg_height = (y00 + y10 + y11 + y01) / 4
            if avg_height > 0.42:
                color = (min(color[0] + 0.08, 1), min(color[1] + 0.06, 1), min(color[2] + 0.03, 1), 1)
            elif avg_height < -0.25:
                color = (max(color[0] - 0.05, 0), max(color[1] - 0.04, 0), max(color[2] - 0.02, 0), 1)
            tile = [
                x, y00, z,
                x + step, y11, z + step,
                x + step, y10, z,
                x, y00, z,
                x, y01, z + step,
                x + step, y11, z + step,
            ]
            verts.extend(tile)
            colors.extend(list(color) * 6)
    return verts, colors


class Mesh:
    def __init__(self, program: ShaderProgram, verts: list[float], colors: list[float]) -> None:
        self.count = len(verts) // 3
        self.vertex_list = program.vertex_list(
            self.count,
            gl.GL_TRIANGLES,
            position=("f", verts),
            color=("f", colors),
        )

    def draw(self) -> None:
        self.vertex_list.draw(gl.GL_TRIANGLES)


class ArcaneFrontiers3D(pyglet.window.Window):
    def __init__(self) -> None:
        super().__init__(WIDTH, HEIGHT, TITLE, resizable=False)
        self.set_minimum_size(WIDTH, HEIGHT)
        gl.glClearColor(0.06, 0.08, 0.07, 1)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_CULL_FACE)

        self.program = ShaderProgram(Shader(VERTEX_SHADER, "vertex"), Shader(FRAGMENT_SHADER, "fragment"))
        self.meshes: dict[str, Mesh] = {}
        self.build_meshes()
        self.decorations = self.make_decorations()

        self.labels = pyglet.graphics.Batch()
        self.fps_display = pyglet.window.FPSDisplay(self)
        self.hud_text = {
            "resources": pyglet.text.Label("", x=884, y=733, font_size=12, color=(244, 232, 191, 255)),
            "message": pyglet.text.Label("", x=650, y=137, font_size=10, width=330, multiline=True, color=(226, 211, 165, 255)),
            "title": pyglet.text.Label("", x=306, y=116, font_size=14, color=(242, 225, 176, 255)),
            "portrait": pyglet.text.Label("", x=235, y=72, anchor_x="center", font_size=17, color=(238, 232, 205, 255)),
            "hp": pyglet.text.Label("", x=306, y=90, font_size=11, color=(214, 216, 200, 255)),
            "stats": pyglet.text.Label("", x=306, y=54, font_size=10, color=(178, 181, 167, 255)),
            "queue": pyglet.text.Label("", x=306, y=34, font_size=10, color=(235, 212, 132, 255)),
            "empty_a": pyglet.text.Label("No Unit Selected", x=308, y=105, font_size=15, color=(220, 209, 180, 255)),
            "empty_b": pyglet.text.Label("Drag units or click the minimap.", x=308, y=77, font_size=11, color=(166, 162, 148, 255)),
        }
        self.command_hotkey_labels = [pyglet.text.Label("", x=0, y=0, font_size=8, color=(255, 225, 129, 255)) for _ in range(9)]
        self.command_name_labels = [pyglet.text.Label("", x=0, y=0, anchor_x="center", font_size=9, color=(230, 222, 194, 255)) for _ in range(9)]
        self.selection_labels = [pyglet.text.Label("", x=0, y=0, font_size=7, color=(222, 215, 188, 255)) for _ in range(12)]
        self.idle_label = pyglet.text.Label("", x=0, y=0, font_size=9, color=(255, 229, 160, 255))
        self.temp_label = pyglet.text.Label("", x=0, y=0, anchor_x="center", font_size=10, color=(220, 240, 255, 255))
        self.command_buttons: list[dict[str, object]] = []

        self.things: list[Thing] = []
        self.in_race_select = True
        self.player_race = "Human"
        self.enemy_race = "Orc"
        self.race_cards: list[tuple[float, float, float, float, str]] = []
        self.gold = 460
        self.wood = 300
        self.food_used = 0
        self.food_cap = 0
        self.camera_x = -44.0
        self.camera_z = -36.0
        self.camera_height = 25.0
        self.zoom = 39.0
        self.keys: set[int] = set()
        self.mouse_x = 0
        self.mouse_y = 0
        self.drag_start: tuple[int, int] | None = None
        self.drag_current: tuple[int, int] | None = None
        self.control_groups: dict[int, list[Thing]] = {i: [] for i in range(10)}
        self.last_alert: tuple[float, float] | None = None
        self.pending_building: str | None = None
        self.game_over = False
        self.victory = False
        self.wave = 0
        self.wave_timer = 30.0
        self.message = "Wybierz rase: 1 Human, 2 Orc, 3 Undead, 4 Night Elf."
        pyglet.clock.schedule_interval(self.update, 1 / 60)

    def start_match(self, race: str) -> None:
        self.player_race = race
        self.enemy_race = self.default_enemy_for(race)
        self.in_race_select = False
        self.things.clear()
        self.gold = 460
        self.wood = 300
        self.wave = 0
        self.wave_timer = 34.0
        self.game_over = False
        self.victory = False
        self.camera_x = -44.0
        self.camera_z = -36.0
        self.pending_building = None
        self.message = f"Ty: {race} vs wróg: {self.enemy_race}. Worker: F/B/T budowa, PPM na las/kopalnie zbiera."
        self.init_world()

    def default_enemy_for(self, race: str) -> str:
        return random.choice(RACE_ORDER)

    def build_meshes(self) -> None:
        self.meshes["ground"] = Mesh(self.program, *terrain_mesh(WORLD_SIZE, 56))
        self.meshes["river"] = Mesh(self.program, *cube_mesh(4.2, 0.035, WORLD_SIZE, (0.10, 0.32, 0.45, 1)))
        self.meshes["river_highlight"] = Mesh(self.program, *cube_mesh(0.7, 0.045, WORLD_SIZE, (0.20, 0.52, 0.62, 1)))
        self.meshes["river_bank"] = Mesh(self.program, *cube_mesh(1.0, 0.05, WORLD_SIZE, (0.34, 0.31, 0.19, 1)))
        self.meshes["road"] = Mesh(self.program, *cube_mesh(5.2, 0.045, 12.0, (0.39, 0.32, 0.19, 1)))
        self.meshes["road_patch"] = Mesh(self.program, *cube_mesh(7.0, 0.042, 7.0, (0.31, 0.27, 0.18, 1)))
        self.meshes["tree_trunk"] = Mesh(self.program, *cube_mesh(0.45, 1.25, 0.45, (0.31, 0.19, 0.10, 1)))
        self.meshes["tree_top"] = Mesh(self.program, *cube_mesh(1.55, 1.65, 1.55, (0.08, 0.34, 0.15, 1)))
        self.meshes["pine_top"] = Mesh(self.program, *cube_mesh(1.25, 2.2, 1.25, (0.05, 0.27, 0.13, 1)))
        self.meshes["rock"] = Mesh(self.program, *cube_mesh(1.25, 0.8, 1.0, (0.37, 0.39, 0.37, 1)))
        self.meshes["gold_mine"] = Mesh(self.program, *cube_mesh(2.3, 1.45, 2.1, (0.66, 0.50, 0.18, 1)))
        self.meshes["gold_glow"] = Mesh(self.program, *cube_mesh(1.0, 0.08, 1.0, (0.95, 0.78, 0.20, 1)))
        self.meshes["selector"] = Mesh(self.program, *cube_mesh(1.45, 0.04, 1.45, (0.1, 0.85, 1.0, 1)))
        self.meshes["Peasant"] = Mesh(self.program, *cube_mesh(0.9, 1.15, 0.9, (0.86, 0.63, 0.25, 1)))
        self.meshes["Footman"] = Mesh(self.program, *cube_mesh(1.0, 1.3, 1.0, (0.22, 0.43, 0.8, 1)))
        self.meshes["Archer"] = Mesh(self.program, *cube_mesh(0.85, 1.15, 0.85, (0.22, 0.66, 0.34, 1)))
        self.meshes["Knight"] = Mesh(self.program, *cube_mesh(1.25, 1.35, 1.35, (0.72, 0.72, 0.82, 1)))
        self.meshes["Grunt"] = Mesh(self.program, *cube_mesh(1.1, 1.35, 1.1, (0.63, 0.2, 0.16, 1)))
        self.meshes["Raider"] = Mesh(self.program, *cube_mesh(1.25, 1.35, 1.35, (0.68, 0.32, 0.16, 1)))
        self.meshes["Town Hall"] = Mesh(self.program, *cube_mesh(4.4, 3.0, 4.4, (0.32, 0.43, 0.61, 1)))
        self.meshes["Farm"] = Mesh(self.program, *cube_mesh(2.4, 1.45, 2.4, (0.56, 0.43, 0.23, 1)))
        self.meshes["Barracks"] = Mesh(self.program, *cube_mesh(3.7, 2.2, 3.4, (0.44, 0.34, 0.24, 1)))
        self.meshes["Tower"] = Mesh(self.program, *cube_mesh(1.8, 4.0, 1.8, (0.54, 0.49, 0.32, 1)))

    def make_decorations(self) -> list[Decoration]:
        decorations: list[Decoration] = []
        forest_points = [
            (-55, -15), (-52, -10), (-49, -5), (-46, 2), (-54, 9), (-50, 16), (-44, 20),
            (-28, -55), (-22, -53), (-16, -56), (-9, -51), (-1, -55), (8, -52), (17, -56),
            (22, 4), (28, 8), (34, 10), (41, 16), (49, 20), (55, 26),
            (-55, 42), (-48, 48), (-40, 53), (-31, 50), (-20, 55),
            (18, -34), (29, -39), (42, -42), (52, -36),
        ]
        for i, (x, z) in enumerate(forest_points):
            kind = "pine" if i % 3 == 0 else "tree"
            decorations.append(Decoration(kind, x, z, 0.9 + (i % 4) * 0.11, amount=320))
        for i, (x, z) in enumerate([(-7, 18), (7, 22), (16, 17), (-28, 9), (46, -8), (-53, -43), (23, -29), (41, -35), (-42, 31), (54, 45), (3, -18)]):
            decorations.append(Decoration("rock", x, z, 0.8 + (i % 3) * 0.18))
        for x, z in [(-51, -22), (-16, 8), (50, 43), (32, -46)]:
            decorations.append(Decoration("gold", x, z, 1.0, amount=2200))
        return decorations

    def init_world(self) -> None:
        p = RACE_DEFS[self.player_race]
        e = RACE_DEFS[self.enemy_race]
        self.things = [
            self.make_building(p["hall"], PLAYER, -48, -39),
            self.make_building(p["farm"], PLAYER, -41, -46),
            self.make_building(p["farm"], PLAYER, -34, -46),
            self.make_building(p["barracks"], PLAYER, -31, -37),
            self.make_building(p["tower"], PLAYER, -40, -29),
            self.make_unit(p["worker"], PLAYER, -41, -39),
            self.make_unit(p["worker"], PLAYER, -47, -45),
            self.make_unit(p["worker"], PLAYER, -36, -42),
            self.make_unit(p["melee"], PLAYER, -25, -36),
            self.make_unit(p["ranged"], PLAYER, -24, -42),
            self.make_unit(p["hero"], PLAYER, -29, -32),
            self.make_building(e["hall"], ENEMY, 49, 42),
            self.make_building(e["barracks"], ENEMY, 39, 35),
            self.make_building(e["tower"], ENEMY, 34, 43),
            self.make_unit(e["melee"], ENEMY, 28, 42),
            self.make_unit(e["melee"], ENEMY, 42, 49),
            self.make_unit(e["heavy"], ENEMY, 46, 30),
            self.make_unit(e["hero"], ENEMY, 43, 37),
        ]
        self.recalc_food()

    def make_unit(self, kind: str, team: str, x: float, z: float) -> Thing:
        data = UNITS[kind]
        return Thing(kind, team, x, z, data["radius"], data["hp"], data["hp"], data["speed"], data["attack"], data["attack_range"])

    def make_building(self, kind: str, team: str, x: float, z: float) -> Thing:
        data = BUILDINGS[kind]
        return Thing(kind, team, x, z, data["radius"], data["hp"], data["hp"], attack=data.get("attack", 0), attack_range=data.get("attack_range", 0), queue=[])

    def mesh_key(self, kind: str) -> str:
        if kind in UNITS:
            return str(UNITS[kind]["mesh"])
        if kind in BUILDINGS:
            return str(BUILDINGS[kind]["mesh"])
        return kind

    def make_construction(self, kind: str, team: str, x: float, z: float, builder: Thing) -> Thing:
        building = self.make_building(kind, team, x, z)
        building.complete = False
        building.build_time = BUILDINGS[kind]["build_time"]
        building.build_progress = 0.0
        building.builder = builder
        building.hp = max(20, building.max_hp * 0.18)
        return building

    def on_draw(self) -> None:
        self.clear()
        if self.in_race_select:
            self.set_2d()
            self.draw_race_select()
            self.fps_display.draw()
            return
        self.set_3d()
        with self.program:
            self.draw_world()
        self.set_2d()
        self.draw_world_overlays()
        self.draw_hud()
        self.fps_display.draw()
        self.draw_end_overlay()

    def draw_race_select(self) -> None:
        self.race_cards = []
        pyglet.shapes.Rectangle(0, 0, WIDTH, HEIGHT, color=(20, 18, 16)).draw()
        pyglet.text.Label("RTS - FAN PROTOTYPE 3D", x=WIDTH / 2, y=HEIGHT - 120, anchor_x="center", font_size=26, color=(238, 218, 160, 255)).draw()
        pyglet.text.Label("Wybierz rase", x=WIDTH / 2, y=HEIGHT - 170, anchor_x="center", font_size=18, color=(210, 204, 184, 255)).draw()
        rows = [
            ("1", "Human", "solidna ekonomia, rycerze i klasyczne wieze"),
            ("2", "Orc", "mocniejsze jednostki, wolniejsze tempo"),
            ("3", "Undead", "agresywne jednostki, mroczna infrastruktura"),
            ("4", "Night Elf", "szybsze oddzialy, lepszy zasieg strzelcow"),
        ]
        for i, (key, name, desc) in enumerate(rows):
            y = HEIGHT - 250 - i * 72
            color = RACE_DEFS[name]["accent"]
            self.race_cards.append((330, y - 18, 620, 48, name))
            pyglet.shapes.BorderedRectangle(330, y - 18, 620, 48, border=2, color=(43, 37, 31), border_color=color).draw()
            pyglet.text.Label(key, x=360, y=y - 2, font_size=18, color=(255, 231, 150, 255)).draw()
            pyglet.text.Label(name, x=410, y=y + 5, font_size=15, color=(235, 226, 196, 255)).draw()
            pyglet.text.Label(f"{desc}  |  enemy: random", x=410, y=y - 13, font_size=10, color=(172, 174, 162, 255)).draw()

    def set_3d(self) -> None:
        gl.glEnable(gl.GL_DEPTH_TEST)
        aspect = WIDTH / HEIGHT
        projection = Mat4.perspective_projection(aspect, 0.1, 240.0, FOV_DEGREES)
        eye = Vec3(self.camera_x, self.camera_height, self.camera_z - self.zoom)
        target = Vec3(self.camera_x, 0.0, self.camera_z + 5.0)
        view = Mat4.look_at(eye, target, Vec3(0, 1, 0))
        self.program["projection"] = projection
        self.program["view"] = view

    def set_2d(self) -> None:
        gl.glDisable(gl.GL_DEPTH_TEST)
        self.projection = Mat4.orthogonal_projection(0, WIDTH, 0, HEIGHT, -1, 1)
        self.view = Mat4()

    def draw_world(self) -> None:
        self.draw_mesh("ground", 0, -0.03, 0, follow_terrain=False)
        self.draw_environment()
        self.draw_build_preview()
        for thing in sorted(self.things, key=lambda t: t.z):
            if not thing.alive:
                continue
            if thing.selected:
                self.draw_mesh("selector", thing.x, 0.02, thing.z, scale=thing.radius * 1.55)
            self.draw_mesh(self.mesh_key(thing.kind), thing.x, 0, thing.z, team=thing.team)

    def draw_environment(self) -> None:
        self.draw_mesh("river_bank", -2.9, 0.04, 0, follow_terrain=False)
        self.draw_mesh("river_bank", 2.9, 0.04, 0, follow_terrain=False)
        self.draw_mesh("river", 0, 0.025, 0, follow_terrain=False)
        self.draw_mesh("river_highlight", -0.95, 0.05, 0, follow_terrain=False)
        road_segments = [(-45, -39, 0.0, 1.1), (-34, -38, 0.0, 1.0), (-22, -27, 0.0, 0.9), (18, 18, 0.0, 0.9), (36, 36, 0.0, 1.0), (49, 42, 0.0, 1.1)]
        for x, z, rot, scale in road_segments:
            self.draw_mesh("road_patch", x, 0.055, z, scale=scale)
        for x, z in [(-49, -38), (-38, -39), (-29, -38), (36, 36), (49, 42)]:
            self.draw_mesh("road", x, 0.06, z)
        for deco in self.decorations:
            if not self.is_near_camera(deco.x, deco.z, 55):
                continue
            self.draw_decoration(deco)

    def draw_decoration(self, deco: Decoration) -> None:
        if deco.kind == "tree":
            if deco.amount <= 0:
                return
            self.draw_mesh("tree_trunk", deco.x, 0, deco.z, scale=deco.scale)
            self.draw_mesh("tree_top", deco.x, 1.05 * deco.scale, deco.z, scale=deco.scale)
        elif deco.kind == "pine":
            if deco.amount <= 0:
                return
            self.draw_mesh("tree_trunk", deco.x, 0, deco.z, scale=deco.scale * 0.85)
            self.draw_mesh("pine_top", deco.x, 0.95 * deco.scale, deco.z, scale=deco.scale)
        elif deco.kind == "rock":
            self.draw_mesh("rock", deco.x, 0, deco.z, scale=deco.scale)
        elif deco.kind == "gold":
            if deco.amount <= 0:
                return
            self.draw_mesh("gold_mine", deco.x, 0, deco.z, scale=deco.scale)
            self.draw_mesh("gold_glow", deco.x, 1.48 * deco.scale, deco.z, scale=deco.scale)

    def draw_build_preview(self) -> None:
        if not self.pending_building or self.mouse_y < HUD_HEIGHT:
            return
        wx, wz = self.screen_to_world(self.mouse_x, self.mouse_y)
        valid = self.can_place_building(self.pending_building, wx, wz)
        self.draw_mesh(self.mesh_key(self.pending_building), wx, 0.03, wz, scale=1.0, ghost=True)
        self.draw_mesh("selector", wx, 0.06, wz, scale=BUILDINGS[self.pending_building]["radius"] * (1.7 if valid else 1.25), ghost=True)

    def is_near_camera(self, x: float, z: float, margin: float) -> bool:
        return abs(x - self.camera_x) <= margin and abs(z - self.camera_z) <= margin

    def draw_mesh(self, key: str, x: float, y: float, z: float, scale: float = 1.0, team: str = PLAYER, ghost: bool = False, scale_y: float | None = None, follow_terrain: bool = True) -> None:
        mesh = self.meshes[key]
        sy = scale if scale_y is None else scale_y
        base_y = y + (terrain_height(x, z) if follow_terrain else 0)
        model = Mat4.from_translation(Vec3(x, base_y, z)) @ Mat4.from_scale(Vec3(scale, sy, scale))
        self.program["model"] = model
        if ghost:
            gl.glDisable(gl.GL_CULL_FACE)
        mesh.draw()
        if ghost:
            gl.glEnable(gl.GL_CULL_FACE)

    def draw_hud(self) -> None:
        self.command_buttons = []
        pyglet.shapes.Rectangle(0, 0, WIDTH, HUD_HEIGHT, color=(24, 21, 18)).draw()
        pyglet.shapes.Rectangle(0, HUD_HEIGHT - 5, WIDTH, 5, color=(141, 113, 62)).draw()
        pyglet.shapes.Rectangle(0, HUD_HEIGHT - 11, WIDTH, 4, color=(52, 43, 30)).draw()
        self.draw_resource_bar()
        self.draw_minimap()
        self.draw_info_card()
        self.draw_selection_strip()
        self.draw_command_card()
        self.hud_text["message"].text = self.message
        self.hud_text["message"].draw()

    def draw_end_overlay(self) -> None:
        if not (self.game_over or self.victory):
            return
        pyglet.shapes.Rectangle(0, HUD_HEIGHT, WIDTH, HEIGHT - HUD_HEIGHT, color=(0, 0, 0, 130)).draw()
        text = "ZWYCIESTWO" if self.victory else "PORAZKA"
        color = (130, 235, 130, 255) if self.victory else (240, 85, 70, 255)
        self.temp_label.text = text
        self.temp_label.x = WIDTH / 2
        self.temp_label.y = HEIGHT / 2 + 24
        self.temp_label.font_size = 36
        self.temp_label.color = color
        self.temp_label.draw()
        self.temp_label.font_size = 10
        self.temp_label.color = (220, 240, 255, 255)

    def draw_resource_bar(self) -> None:
        x = 846
        y = HEIGHT - 33
        pyglet.shapes.BorderedRectangle(x, y, 412, 27, border=2, color=(31, 27, 22), border_color=(124, 101, 58)).draw()
        items = [("G", self.gold, (238, 198, 62)), ("L", self.wood, (98, 190, 93)), ("F", f"{self.food_used}/{self.food_cap}", (212, 218, 228)), ("W", f"{int(self.wave_timer)}", (225, 151, 81))]
        for i, (icon, value, color) in enumerate(items):
            bx = x + 13 + i * 100
            pyglet.shapes.Rectangle(bx, y + 6, 17, 15, color=color).draw()
        self.hud_text["resources"].text = f"G {self.gold}     L {self.wood}     F {self.food_used}/{self.food_cap}     W {int(self.wave_timer)}"
        self.hud_text["resources"].draw()

    def draw_minimap(self) -> None:
        x, y, size, _ = MINIMAP_RECT
        self.draw_stone_panel(x - 8, y - 8, size + 16, size + 16)
        pyglet.shapes.Rectangle(x, y, size, size, color=(31, 55, 35)).draw()
        river_x = x + size * 0.5 - 5
        pyglet.shapes.Rectangle(river_x, y, 10, size, color=(28, 82, 102)).draw()
        for deco in self.decorations:
            mx, my = self.world_to_minimap(deco.x, deco.z)
            if deco.kind in {"tree", "pine"}:
                if deco.amount <= 0:
                    continue
                pyglet.shapes.Rectangle(mx - 1.5, my - 1.5, 3, 3, color=(32, 104, 45)).draw()
            elif deco.kind == "gold":
                if deco.amount <= 0:
                    continue
                pyglet.shapes.Rectangle(mx - 2, my - 2, 4, 4, color=(222, 178, 45)).draw()
        for thing in self.things:
            if not thing.alive:
                continue
            mx, my = self.world_to_minimap(thing.x, thing.z)
            color = (84, 170, 255) if thing.team == PLAYER else (230, 68, 48)
            dot = 4 if thing.is_building else 3
            pyglet.shapes.Rectangle(mx - dot / 2, my - dot / 2, dot, dot, color=color).draw()
        cam_left = x + (self.camera_x + WORLD_HALF - 22) / WORLD_SIZE * size
        cam_bottom = y + (self.camera_z + WORLD_HALF - 16) / WORLD_SIZE * size
        pyglet.shapes.BorderedRectangle(cam_left, cam_bottom, 32 / WORLD_SIZE * size, 24 / WORLD_SIZE * size, border=1, color=(0, 0, 0, 0), border_color=(244, 222, 127)).draw()
        idle = sum(1 for t in self.things if t.team == PLAYER and t.kind == self.race_name("worker") and t.alive and not t.target and t.target_x is None)
        if idle:
            pyglet.shapes.BorderedRectangle(x + 3, y + size + 9, 54, 20, border=1, color=(74, 46, 20), border_color=(194, 160, 72)).draw()
            self.idle_label.text = f"Idle {idle}"
            self.idle_label.x = x + 9
            self.idle_label.y = y + size + 14
            self.idle_label.draw()

    def draw_info_card(self) -> None:
        selected = [t for t in self.things if t.selected and t.alive and t.team == PLAYER]
        self.draw_stone_panel(174, 18, 360, 132)
        self.draw_stone_panel(192, 36, 86, 88)
        if not selected:
            self.hud_text["empty_a"].draw()
            self.hud_text["empty_b"].draw()
            return
        primary = selected[0]
        color = (67, 123, 185) if not primary.is_building else (103, 92, 68)
        pyglet.shapes.Rectangle(208, 51, 54, 58, color=color).draw()
        self.hud_text["portrait"].text = primary.kind[:2].upper()
        self.hud_text["portrait"].draw()
        name = primary.kind if len(selected) == 1 else f"{len(selected)} Units Selected"
        self.hud_text["title"].text = name
        self.hud_text["title"].draw()
        hp_pct = clamp(primary.hp / primary.max_hp, 0, 1)
        self.hud_text["hp"].text = f"Hit Points: {int(primary.hp)}/{int(primary.max_hp)}"
        self.hud_text["hp"].draw()
        pyglet.shapes.Rectangle(306, 76, 156, 8, color=(56, 25, 22)).draw()
        pyglet.shapes.Rectangle(306, 76, 156 * hp_pct, 8, color=(74, 191, 82) if hp_pct > 0.45 else (221, 169, 58)).draw()
        if primary.is_building and not primary.complete:
            stats = f"Building... {int(100 * primary.build_progress / max(0.1, primary.build_time))}%"
        elif primary.kind == self.race_name("worker") and primary.gather_target:
            stats = f"Gathering {primary.gather_target.resource_kind}"
        else:
            stats = f"Attack {int(primary.attack)}   Range {primary.attack_range:.1f}" if primary.attack else "Worker / Structure"
        self.hud_text["stats"].text = stats
        self.hud_text["stats"].draw()
        if primary.queue:
            q = "Queue: " + ", ".join(primary.queue[:4])
            self.hud_text["queue"].text = q
            self.hud_text["queue"].draw()
        else:
            self.hud_text["queue"].text = ""

    def draw_selection_strip(self) -> None:
        selected = [t for t in self.things if t.selected and t.alive and t.team == PLAYER]
        self.draw_stone_panel(552, 18, 416, 102)
        for i, thing in enumerate(selected[:12]):
            col = i % 6
            row = i // 6
            x = 568 + col * 64
            y = 72 - row * 42
            border = (115, 210, 232) if i == 0 else (99, 83, 52)
            pyglet.shapes.BorderedRectangle(x, y, 50, 34, border=2, color=(42, 37, 31), border_color=border).draw()
            tint = (65, 120, 180) if not thing.is_building else (112, 94, 62)
            pyglet.shapes.Rectangle(x + 5, y + 6, 22, 20, color=tint).draw()
            label = self.selection_labels[i]
            label.text = thing.kind[:3]
            label.x = x + 31
            label.y = y + 18
            label.draw()
            pct = clamp(thing.hp / thing.max_hp, 0, 1)
            pyglet.shapes.Rectangle(x + 5, y + 3, 40, 3, color=(54, 20, 20)).draw()
            pyglet.shapes.Rectangle(x + 5, y + 3, 40 * pct, 3, color=(68, 205, 83)).draw()

    def draw_command_card(self) -> None:
        self.draw_stone_panel(988, 18, 274, 132)
        buttons = self.current_commands()
        x0, y0, bw, bh, cols, _rows = COMMAND_GRID
        for i in range(9):
            col = i % cols
            row = i // cols
            x = x0 + col * (bw + 10)
            y = y0 + (2 - row) * (bh + 5)
            command = buttons[i] if i < len(buttons) else None
            color = (54, 48, 40) if command else (31, 29, 25)
            pyglet.shapes.BorderedRectangle(x, y, bw, bh, border=2, color=color, border_color=(112, 91, 55)).draw()
            if command:
                self.command_buttons.append({"rect": (x, y, bw, bh), "action": command["action"]})
                hotkey_label = self.command_hotkey_labels[i]
                hotkey_label.text = command["hotkey"]
                hotkey_label.x = x + 6
                hotkey_label.y = y + bh - 15
                hotkey_label.draw()
                name_label = self.command_name_labels[i]
                name_label.text = command["label"]
                name_label.x = x + bw / 2
                name_label.y = y + 12
                name_label.draw()

    def draw_stone_panel(self, x: float, y: float, w: float, h: float) -> None:
        pyglet.shapes.BorderedRectangle(x, y, w, h, border=3, color=(43, 37, 31), border_color=(122, 101, 61)).draw()
        pyglet.shapes.Rectangle(x + 5, y + h - 9, w - 10, 3, color=(74, 63, 43)).draw()

    def draw_world_overlays(self) -> None:
        for thing in self.things:
            if not thing.alive:
                continue
            screen = self.world_to_screen(thing.x, 1.8 if not thing.is_building else 3.2, thing.z)
            if not screen:
                continue
            sx, sy = screen
            if thing.selected or thing.hp < thing.max_hp:
                width = 44 if not thing.is_building else 66
                pct = clamp(thing.hp / thing.max_hp, 0, 1)
                pyglet.shapes.Rectangle(sx - width / 2, sy + 10, width, 6, color=(50, 24, 24)).draw()
                color = (70, 220, 92) if pct > 0.45 else (228, 178, 68)
                pyglet.shapes.Rectangle(sx - width / 2, sy + 10, width * pct, 6, color=color).draw()
            if thing.selected:
                self.temp_label.text = thing.kind
                self.temp_label.x = sx
                self.temp_label.y = sy + 20
                self.temp_label.draw()
        if self.drag_start and self.drag_current:
            x1, y1 = self.drag_start
            x2, y2 = self.drag_current
            left, right = sorted((x1, x2))
            bottom, top = sorted((y1, y2))
            pyglet.shapes.BorderedRectangle(left, bottom, right - left, top - bottom, border=2, color=(60, 180, 210, 45), border_color=(120, 230, 255)).draw()

    def update(self, dt: float) -> None:
        if self.in_race_select:
            return
        self.update_camera(dt)
        if self.game_over or self.victory:
            return
        self.wave_timer -= dt
        if self.wave_timer <= 0:
            self.spawn_wave()
        for thing in self.things:
            if not thing.alive:
                continue
            thing.cooldown = max(0, thing.cooldown - dt)
            if thing.is_building and not thing.complete:
                self.update_construction(thing, dt)
                continue
            if thing.is_building:
                self.update_queue(thing, dt)
            if thing.kind == self.race_name("worker"):
                self.update_gathering(thing, dt)
            if self.unit_role(thing.kind) == "hero":
                self.update_hero_aura(thing, dt)
            self.update_attack(thing)
            self.update_move(thing, dt)
        self.things = [t for t in self.things if t.alive]
        self.recalc_food()
        self.game_over = not any(t.team == PLAYER and t.kind == self.race_name("hall") and t.alive for t in self.things)
        enemy_hall = str(RACE_DEFS[self.enemy_race]["hall"])
        self.victory = not any(t.team == ENEMY and t.kind == enemy_hall and t.alive for t in self.things)
        if self.game_over:
            self.message = "PORAZKA: Town Hall zniszczony. Uruchom ponownie, aby zagrac od nowa."
        elif self.victory:
            self.message = "ZWYCIESTWO: wroga baza padla."

    def update_camera(self, dt: float) -> None:
        dx = dz = 0.0
        if pyglet.window.key.LEFT in self.keys:
            dx -= 1
        if pyglet.window.key.RIGHT in self.keys:
            dx += 1
        if pyglet.window.key.DOWN in self.keys:
            dz -= 1
        if pyglet.window.key.UP in self.keys:
            dz += 1
        if HUD_HEIGHT <= self.mouse_y <= HEIGHT:
            if self.mouse_x <= EDGE_SCROLL_SIZE:
                dx -= 1
            if self.mouse_x >= WIDTH - EDGE_SCROLL_SIZE:
                dx += 1
            if self.mouse_y <= HUD_HEIGHT + EDGE_SCROLL_SIZE:
                dz -= 1
            if self.mouse_y >= HEIGHT - EDGE_SCROLL_SIZE:
                dz += 1
        if dx and dz:
            dx *= 0.707
            dz *= 0.707
        limit = WORLD_HALF - 18
        self.camera_x = clamp(self.camera_x + dx * CAMERA_SPEED * dt, -limit, limit)
        self.camera_z = clamp(self.camera_z + dz * CAMERA_SPEED * dt, -limit, limit)

    def update_queue(self, building: Thing, dt: float) -> None:
        if not building.complete:
            return
        if not building.queue:
            return
        building.queue_timer -= dt
        if building.queue_timer > 0:
            return
        kind = building.queue.pop(0)
        unit = self.make_unit(kind, PLAYER, building.x + random.uniform(-2.8, 2.8), building.z + random.uniform(-2.8, 2.8))
        unit.target_x = building.rally_x if building.rally_x is not None else building.x + 4
        unit.target_z = building.rally_z if building.rally_z is not None else building.z
        self.things.append(unit)
        if building.queue:
            building.queue_timer = TRAIN_TIME[building.queue[0]]

    def update_attack(self, thing: Thing) -> None:
        if thing.attack <= 0 or (thing.is_building and not thing.complete):
            return
        if thing.target and not thing.target.alive:
            thing.target = None
        enemies = [t for t in self.things if t.team != thing.team and t.alive]
        if not thing.target:
            close = [e for e in enemies if dist2(thing.x, thing.z, e.x, e.z) <= thing.attack_range + e.radius]
            if close:
                thing.target = min(close, key=lambda e: dist2(thing.x, thing.z, e.x, e.z))
        if not thing.target:
            return
        d = dist2(thing.x, thing.z, thing.target.x, thing.target.z)
        if d <= thing.attack_range + thing.target.radius:
            thing.target_x = None
            thing.target_z = None
            if thing.cooldown <= 0:
                thing.target.hp -= thing.attack
                thing.cooldown = 0.95
        elif not thing.is_building:
            thing.target_x = thing.target.x
            thing.target_z = thing.target.z

    def update_construction(self, building: Thing, dt: float) -> None:
        builder = building.builder
        if not builder or not builder.alive:
            return
        if dist2(builder.x, builder.z, building.x, building.z) > builder.radius + building.radius + 1.0:
            builder.target_x = building.x
            builder.target_z = building.z
            return
        builder.target_x = None
        builder.target_z = None
        building.build_progress += dt
        pct = clamp(building.build_progress / max(0.1, building.build_time), 0, 1)
        building.hp = max(building.hp, building.max_hp * (0.18 + 0.82 * pct))
        if building.build_progress >= building.build_time:
            building.complete = True
            building.hp = building.max_hp
            building.builder = None
            self.message = f"Budowa ukonczona: {building.kind}."

    def update_gathering(self, worker: Thing, dt: float) -> None:
        target = worker.gather_target
        if not target or target.amount <= 0:
            worker.gather_target = None
            return
        if dist2(worker.x, worker.z, target.x, target.z) > worker.radius + 2.0:
            worker.target_x = target.x
            worker.target_z = target.z
            return
        worker.target_x = None
        worker.target_z = None
        worker.gather_timer += dt
        if worker.gather_timer < 0.45:
            return
        worker.gather_timer = 0.0
        amount = min(7.0, target.amount)
        target.amount -= amount
        if target.resource_kind == "gold":
            self.gold += int(amount)
        elif target.resource_kind == "wood":
            self.wood += int(amount)

    def update_hero_aura(self, hero: Thing, dt: float) -> None:
        for ally in self.things:
            if ally.team == hero.team and ally.alive and not ally.is_building and dist2(hero.x, hero.z, ally.x, ally.z) <= 8:
                ally.hp = min(ally.max_hp, ally.hp + 1.6 * dt)

    def update_move(self, thing: Thing, dt: float) -> None:
        if thing.is_building or thing.target_x is None or thing.target_z is None:
            return
        dx = thing.target_x - thing.x
        dz = thing.target_z - thing.z
        d = math.hypot(dx, dz)
        if d < 0.15:
            thing.target_x = None
            thing.target_z = None
            return
        step = min(d, thing.speed * dt)
        thing.x += dx / d * step
        thing.z += dz / d * step
        thing.x = clamp(thing.x, -WORLD_HALF + thing.radius, WORLD_HALF - thing.radius)
        thing.z = clamp(thing.z, -WORLD_HALF + thing.radius, WORLD_HALF - thing.radius)

    def recalc_food(self) -> None:
        self.food_used = sum(UNITS[t.kind]["food"] for t in self.things if t.team == PLAYER and t.kind in UNITS)
        self.food_cap = sum(BUILDINGS[t.kind]["food"] for t in self.things if t.team == PLAYER and t.kind in BUILDINGS and t.complete)

    def spawn_wave(self) -> None:
        self.wave += 1
        self.wave_timer = max(18, 32 - self.wave)
        enemy = RACE_DEFS[self.enemy_race]
        for i in range(2 + self.wave):
            if self.wave >= 4 and i % 4 == 0:
                kind = str(enemy["heavy"])
            elif i % 3 == 0 and self.wave > 1:
                kind = str(enemy["ranged"])
            else:
                kind = str(enemy["melee"])
            unit = self.make_unit(kind, ENEMY, 49 + random.uniform(-6, 6), 42 + random.uniform(-6, 6))
            hall = next((t for t in self.things if t.team == PLAYER and t.kind == self.race_name("hall")), None)
            if hall:
                unit.target = hall
                unit.target_x = hall.x
                unit.target_z = hall.z
            self.things.append(unit)
        self.last_alert = (49, 42)
        self.message = f"Nadciaga fala {self.wave}. Kamera i walka dzialaja juz w 3D."

    def world_to_minimap(self, x: float, z: float) -> tuple[float, float]:
        mx, my, size, _ = MINIMAP_RECT
        return mx + (x + WORLD_HALF) / WORLD_SIZE * size, my + (z + WORLD_HALF) / WORLD_SIZE * size

    def minimap_to_world(self, x: float, y: float) -> tuple[float, float]:
        mx, my, size, _ = MINIMAP_RECT
        wx = ((x - mx) / size) * WORLD_SIZE - WORLD_HALF
        wz = ((y - my) / size) * WORLD_SIZE - WORLD_HALF
        limit = WORLD_HALF - 18
        return clamp(wx, -limit, limit), clamp(wz, -limit, limit)

    def current_commands(self) -> list[dict[str, str]]:
        selected = [t for t in self.things if t.selected and t.alive and t.team == PLAYER]
        if not selected:
            return [
                {"hotkey": "H", "label": "Town", "action": "focus_town"},
                {"hotkey": "I", "label": "Idle", "action": "idle_worker"},
                {"hotkey": "^A", "label": "Army", "action": "select_army"},
            ]
        primary = selected[0]
        commands: list[dict[str, str]] = []
        if primary.is_building and not primary.complete:
            commands.extend([
                {"hotkey": "S", "label": "Stop", "action": "stop"},
                {"hotkey": "H", "label": "Town", "action": "focus_town"},
            ])
            return commands
        if primary.kind == self.race_name("hall"):
            worker = self.race_name("worker")
            hero = self.race_name("hero")
            commands.append({"hotkey": "Q", "label": worker[:9], "action": f"train:{worker}"})
            commands.append({"hotkey": "Y", "label": hero[:9], "action": f"train:{hero}"})
        if primary.kind == self.race_name("barracks"):
            melee = self.race_name("melee")
            ranged = self.race_name("ranged")
            heavy = self.race_name("heavy")
            commands.extend([
                {"hotkey": "W", "label": melee[:9], "action": f"train:{melee}"},
                {"hotkey": "E", "label": ranged[:9], "action": f"train:{ranged}"},
                {"hotkey": "R", "label": heavy[:9], "action": f"train:{heavy}"},
            ])
        if primary.kind == self.race_name("worker"):
            farm = self.race_name("farm")
            barracks = self.race_name("barracks")
            tower = self.race_name("tower")
            commands.extend([
                {"hotkey": "F", "label": farm[:9], "action": f"build:{farm}"},
                {"hotkey": "B", "label": barracks[:9], "action": f"build:{barracks}"},
                {"hotkey": "T", "label": tower[:9], "action": f"build:{tower}"},
            ])
        if any(not t.is_building for t in selected):
            commands.extend([
                {"hotkey": "M", "label": "Move", "action": "hint_move"},
                {"hotkey": "A", "label": "Attack", "action": "hint_attack"},
                {"hotkey": "S", "label": "Stop", "action": "stop"},
                {"hotkey": "H", "label": "Hold", "action": "hold"},
            ])
        commands.extend([
            {"hotkey": "I", "label": "Idle", "action": "idle_worker"},
            {"hotkey": "^A", "label": "Army", "action": "select_army"},
        ])
        return commands[:9]

    def race_name(self, role: str) -> str:
        return str(RACE_DEFS[self.player_race][role])

    def unit_role(self, kind: str) -> str:
        return str(UNITS.get(kind, {}).get("role", ""))

    def run_command_action(self, action: str) -> None:
        if action.startswith("train:"):
            self.try_train(action.split(":", 1)[1])
        elif action.startswith("build:"):
            self.start_build_mode(action.split(":", 1)[1])
        elif action == "stop":
            for thing in self.things:
                if thing.selected and thing.team == PLAYER:
                    thing.target = None
                    thing.target_x = None
                    thing.target_z = None
                    thing.gather_target = None
            self.message = "Rozkaz: Stop."
        elif action == "hold":
            for thing in self.things:
                if thing.selected and thing.team == PLAYER:
                    thing.target_x = None
                    thing.target_z = None
                    thing.gather_target = None
            self.message = "Rozkaz: Hold Position."
        elif action == "focus_town":
            self.focus_kind(self.race_name("hall"))
        elif action == "idle_worker":
            self.select_idle_worker()
        elif action == "select_army":
            self.select_army()
        elif action == "hint_move":
            self.message = "Move: kliknij PPM na ziemi."
        elif action == "hint_attack":
            self.message = "Attack: kliknij PPM na wroga."

    def handle_hud_click(self, x: int, y: int) -> bool:
        mx, my, size, _ = MINIMAP_RECT
        if mx <= x <= mx + size and my <= y <= my + size:
            self.camera_x, self.camera_z = self.minimap_to_world(x, y)
            self.message = "Kamera przesunieta z minimapy."
            return True
        for button in self.command_buttons:
            bx, by, bw, bh = button["rect"]  # type: ignore[index]
            if bx <= x <= bx + bw and by <= y <= by + bh:
                self.run_command_action(str(button["action"]))
                return True
        return False

    def camera_basis(self) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
        eye = (self.camera_x, self.camera_height, self.camera_z - self.zoom)
        target = (self.camera_x, 0.0, self.camera_z + 5.0)
        forward = self.norm((target[0] - eye[0], target[1] - eye[1], target[2] - eye[2]))
        world_up = (0.0, 1.0, 0.0)
        right = self.norm(self.cross(forward, world_up))
        up = self.norm(self.cross(right, forward))
        return eye, forward, right, up

    def screen_to_world(self, x: float, y: float) -> tuple[float, float]:
        eye, forward, right, up = self.camera_basis()
        aspect = WIDTH / HEIGHT
        tan_half = math.tan(math.radians(FOV_DEGREES) / 2)
        nx = (x / WIDTH) * 2.0 - 1.0
        ny = (y / HEIGHT) * 2.0 - 1.0
        ray = self.norm((
            forward[0] + right[0] * nx * tan_half * aspect + up[0] * ny * tan_half,
            forward[1] + right[1] * nx * tan_half * aspect + up[1] * ny * tan_half,
            forward[2] + right[2] * nx * tan_half * aspect + up[2] * ny * tan_half,
        ))
        if ray[1] >= -0.001:
            return self.camera_x, self.camera_z
        t = -eye[1] / ray[1]
        world_x = eye[0] + ray[0] * t
        world_z = eye[2] + ray[2] * t
        for _ in range(3):
            ground_y = terrain_height(world_x, world_z)
            t = (ground_y - eye[1]) / ray[1]
            world_x = eye[0] + ray[0] * t
            world_z = eye[2] + ray[2] * t
        edge = WORLD_HALF - 1
        return clamp(world_x, -edge, edge), clamp(world_z, -edge, edge)

    def world_to_screen(self, x: float, y: float, z: float) -> tuple[float, float] | None:
        eye, forward, right, up = self.camera_basis()
        rel = (x - eye[0], terrain_height(x, z) + y - eye[1], z - eye[2])
        depth = self.dot(rel, forward)
        if depth <= 0.1:
            return None
        aspect = WIDTH / HEIGHT
        tan_half = math.tan(math.radians(FOV_DEGREES) / 2)
        cam_x = self.dot(rel, right)
        cam_y = self.dot(rel, up)
        ndc_x = cam_x / (depth * tan_half * aspect)
        ndc_y = cam_y / (depth * tan_half)
        if ndc_x < -1.3 or ndc_x > 1.3 or ndc_y < -1.3 or ndc_y > 1.3:
            return None
        return (ndc_x + 1.0) * WIDTH / 2, (ndc_y + 1.0) * HEIGHT / 2

    def thing_at_screen(self, x: float, y: float, team: str | None = None) -> Thing | None:
        hits: list[tuple[float, float, Thing]] = []
        for thing in self.things:
            if not thing.alive or (team and thing.team != team):
                continue
            screen = self.world_to_screen(thing.x, 1.2 if not thing.is_building else 2.0, thing.z)
            if not screen:
                continue
            sx, sy = screen
            pick_radius = max(24, thing.radius * 15 if not thing.is_building else thing.radius * 20)
            distance = math.hypot(x - sx, y - sy)
            if distance <= pick_radius:
                team_bias = 0 if thing.team == PLAYER else 12
                hits.append((distance + team_bias, thing.radius, thing))
        hits.sort(key=lambda item: (item[0], item[1]))
        return hits[0][2] if hits else None

    def decoration_at_screen(self, x: float, y: float) -> Decoration | None:
        hits: list[tuple[float, Decoration]] = []
        for deco in self.decorations:
            if not deco.resource_kind or deco.amount <= 0:
                continue
            screen = self.world_to_screen(deco.x, 1.4 * deco.scale, deco.z)
            if not screen:
                continue
            sx, sy = screen
            distance = math.hypot(x - sx, y - sy)
            if distance <= max(22, deco.scale * 18):
                hits.append((distance, deco))
        hits.sort(key=lambda item: item[0])
        return hits[0][1] if hits else None

    def things_in_screen_rect(self, x1: float, y1: float, x2: float, y2: float, team: str = PLAYER) -> list[Thing]:
        left, right = sorted((x1, x2))
        bottom, top = sorted((y1, y2))
        selected: list[Thing] = []
        for thing in self.things:
            if not thing.alive or thing.team != team or thing.is_building:
                continue
            screen = self.world_to_screen(thing.x, 1.0, thing.z)
            if not screen:
                continue
            sx, sy = screen
            if left <= sx <= right and bottom <= sy <= top:
                selected.append(thing)
        return selected

    def dot(self, a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

    def cross(self, a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
        return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])

    def norm(self, v: tuple[float, float, float]) -> tuple[float, float, float]:
        length = math.sqrt(self.dot(v, v)) or 1.0
        return v[0] / length, v[1] / length, v[2] / length

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.mouse_x = x
        self.mouse_y = y
        if self.drag_start:
            self.drag_current = (x, y)

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> None:
        self.mouse_x = x
        self.mouse_y = y
        if buttons & pyglet.window.mouse.LEFT and self.drag_start:
            self.drag_current = (x, y)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        self.zoom = clamp(self.zoom - scroll_y * 3.0, 20, 62)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if self.in_race_select:
            if button == pyglet.window.mouse.LEFT:
                for bx, by, bw, bh, race in self.race_cards:
                    if bx <= x <= bx + bw and by <= y <= by + bh:
                        self.start_match(race)
                        return
            return
        if y < HUD_HEIGHT:
            if button == pyglet.window.mouse.LEFT:
                self.handle_hud_click(x, y)
            return
        if button == pyglet.window.mouse.LEFT:
            if self.pending_building:
                wx, wz = self.screen_to_world(x, y)
                self.place_pending_building(wx, wz)
                return
            self.drag_start = (x, y)
            self.drag_current = (x, y)
        elif button == pyglet.window.mouse.RIGHT:
            if self.pending_building:
                self.pending_building = None
                self.message = "Anulowano budowe."
                return
            wx, wz = self.screen_to_world(x, y)
            selected = [t for t in self.things if t.selected and t.alive and t.team == PLAYER]
            hit = self.thing_at_screen(x, y)
            resource = self.decoration_at_screen(x, y)
            for i, thing in enumerate(selected):
                if thing.is_building:
                    thing.rally_x = wx
                    thing.rally_z = wz
                    self.message = f"Rally point ustawiony dla {thing.kind}."
                elif hit and hit.team == ENEMY:
                    thing.target = hit
                    thing.target_x = hit.x
                    thing.target_z = hit.z
                    thing.gather_target = None
                elif resource and thing.kind == self.race_name("worker"):
                    thing.target = None
                    thing.gather_target = resource
                    thing.target_x = resource.x
                    thing.target_z = resource.z
                    self.message = f"{thing.kind} zbiera {resource.resource_kind}."
                elif not thing.is_building:
                    angle = math.tau * i / max(1, len(selected))
                    thing.target = None
                    thing.gather_target = None
                    thing.target_x = wx + math.cos(angle) * 1.4
                    thing.target_z = wz + math.sin(angle) * 1.4

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> None:
        if button != pyglet.window.mouse.LEFT or not self.drag_start:
            return
        x1, y1 = self.drag_start
        self.drag_start = None
        self.drag_current = None
        additive = bool(modifiers & pyglet.window.key.MOD_SHIFT)
        if math.hypot(x - x1, y - y1) < 7:
            hit = self.thing_at_screen(x, y, PLAYER)
            if not additive:
                for thing in self.things:
                    thing.selected = False
            if hit:
                hit.selected = not hit.selected if additive else True
                self.message = f"Wybrano: {hit.kind}."
            return
        boxed = self.things_in_screen_rect(x1, y1, x, y, PLAYER)
        if not additive:
            for thing in self.things:
                thing.selected = False
        for thing in boxed:
            thing.selected = True
        if boxed:
            self.message = f"Zaznaczono grupe: {len(boxed)} jednostek."

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if self.in_race_select:
            race_keys = {
                pyglet.window.key._1: "Human",
                pyglet.window.key._2: "Orc",
                pyglet.window.key._3: "Undead",
                pyglet.window.key._4: "Night Elf",
            }
            if symbol in race_keys:
                self.start_match(race_keys[symbol])
            return
        self.keys.add(symbol)
        number = self.key_to_number(symbol)
        if number is not None:
            if modifiers & pyglet.window.key.MOD_CTRL:
                self.control_groups[number] = [t for t in self.things if t.selected and t.alive and t.team == PLAYER]
                self.message = f"Zapisano grupe {number}: {len(self.control_groups[number])} obiektow."
            else:
                self.select_group(number)
            return
        if symbol in (pyglet.window.key.Q, pyglet.window.key.W, pyglet.window.key.E, pyglet.window.key.R, pyglet.window.key.Y):
            kind = {
                pyglet.window.key.Q: self.race_name("worker"),
                pyglet.window.key.W: self.race_name("melee"),
                pyglet.window.key.E: self.race_name("ranged"),
                pyglet.window.key.R: self.race_name("heavy"),
                pyglet.window.key.Y: self.race_name("hero"),
            }[symbol]
            self.try_train(kind)
        elif symbol == pyglet.window.key.ESCAPE:
            self.pending_building = None
            for thing in self.things:
                thing.selected = False
        elif symbol == pyglet.window.key.H:
            self.focus_kind(self.race_name("hall"))
        elif symbol == pyglet.window.key.I:
            self.select_idle_worker()
        elif symbol == pyglet.window.key.A and modifiers & pyglet.window.key.MOD_CTRL:
            self.select_army()
        elif symbol == pyglet.window.key.A:
            self.run_command_action("hint_attack")
        elif symbol == pyglet.window.key.M:
            self.run_command_action("hint_move")
        elif symbol == pyglet.window.key.S:
            self.run_command_action("stop")
        elif symbol == pyglet.window.key.F:
            self.start_build_mode(self.race_name("farm"))
        elif symbol == pyglet.window.key.B:
            self.start_build_mode(self.race_name("barracks"))
        elif symbol == pyglet.window.key.T:
            self.start_build_mode(self.race_name("tower"))
        elif symbol == pyglet.window.key.SPACE and self.last_alert:
            self.camera_x, self.camera_z = self.last_alert
            self.message = "Kamera przeniesiona do ostatniego alertu."

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        self.keys.discard(symbol)

    def try_train(self, kind: str) -> None:
        data = UNITS[kind]
        if data.get("role") == "hero" and any(t.team == PLAYER and t.kind == kind and t.alive for t in self.things):
            self.message = f"{kind} juz walczy na mapie."
            return
        producers = [t for t in self.things if t.team == PLAYER and t.kind == data["producer"] and t.alive and t.complete]
        if not producers:
            self.message = f"Potrzebujesz: {data['producer']}."
            return
        queued_food = sum(UNITS[item]["food"] for p in producers for item in (p.queue or []))
        if self.food_used + queued_food + data["food"] > self.food_cap:
            self.message = "Brak miejsca w populacji. Zbuduj Farm."
            return
        if self.gold < data["cost_gold"] or self.wood < data["cost_wood"]:
            self.message = "Za malo surowcow."
            return
        self.gold -= data["cost_gold"]
        self.wood -= data["cost_wood"]
        producer = min(producers, key=lambda p: len(p.queue or []))
        producer.queue = producer.queue or []
        producer.queue.append(kind)
        if len(producer.queue) == 1:
            producer.queue_timer = TRAIN_TIME[kind]
        self.message = f"Szkolenie 3D: {kind}."

    def start_build_mode(self, kind: str) -> None:
        worker = self.selected_worker()
        if not worker:
            self.message = "Zaznacz Peasanta, aby budowac."
            return
        data = BUILDINGS[kind]
        if self.gold < data["cost_gold"] or self.wood < data["cost_wood"]:
            self.message = "Za malo surowcow na budynek."
            return
        self.pending_building = kind
        self.message = f"Budowa {kind} ({data['cost_gold']}g/{data['cost_wood']}w): kliknij LPM na mapie."

    def place_pending_building(self, x: float, z: float) -> None:
        kind = self.pending_building
        if not kind:
            return
        worker = self.selected_worker()
        if not worker:
            self.pending_building = None
            self.message = "Brak Peasanta do budowy."
            return
        data = BUILDINGS[kind]
        if self.gold < data["cost_gold"] or self.wood < data["cost_wood"]:
            self.pending_building = None
            self.message = "Za malo surowcow na budynek."
            return
        if not self.can_place_building(kind, x, z):
            self.message = "Nie mozna tu budowac."
            return
        self.gold -= data["cost_gold"]
        self.wood -= data["cost_wood"]
        building = self.make_construction(kind, PLAYER, x, z, worker)
        self.things.append(building)
        worker.target = None
        worker.gather_target = None
        worker.target_x = x
        worker.target_z = z
        self.pending_building = None
        self.message = f"Rozpoczeto budowe: {kind}."

    def selected_worker(self) -> Thing | None:
        return next((t for t in self.things if t.team == PLAYER and t.kind == self.race_name("worker") and t.selected and t.alive), None)

    def can_place_building(self, kind: str, x: float, z: float) -> bool:
        radius = BUILDINGS[kind]["radius"]
        if abs(x) > WORLD_HALF - radius or abs(z) > WORLD_HALF - radius:
            return False
        if abs(x) < 5.2:
            return False
        for thing in self.things:
            if thing.alive and dist2(x, z, thing.x, thing.z) < radius + thing.radius + 1.4:
                return False
        for deco in self.decorations:
            if deco.amount > 0 and dist2(x, z, deco.x, deco.z) < radius + 2.4 * deco.scale:
                return False
        return True

    def key_to_number(self, symbol: int) -> int | None:
        mapping = {
            pyglet.window.key._0: 0,
            pyglet.window.key._1: 1,
            pyglet.window.key._2: 2,
            pyglet.window.key._3: 3,
            pyglet.window.key._4: 4,
            pyglet.window.key._5: 5,
            pyglet.window.key._6: 6,
            pyglet.window.key._7: 7,
            pyglet.window.key._8: 8,
            pyglet.window.key._9: 9,
        }
        return mapping.get(symbol)

    def select_group(self, number: int) -> None:
        group = [t for t in self.control_groups[number] if t.alive]
        for thing in self.things:
            thing.selected = thing in group
        if group:
            limit = WORLD_HALF - 18
            self.camera_x = clamp(sum(t.x for t in group) / len(group), -limit, limit)
            self.camera_z = clamp(sum(t.z for t in group) / len(group), -limit, limit)
        self.message = f"Wybrano grupe {number}: {len(group)} obiektow."

    def focus_kind(self, kind: str) -> None:
        if kind == "Town Hall":
            kind = self.race_name("hall")
        target = next((t for t in self.things if t.team == PLAYER and t.kind == kind and t.alive), None)
        if not target:
            self.message = f"Nie znaleziono: {kind}."
            return
        self.camera_x, self.camera_z = target.x, target.z
        for thing in self.things:
            thing.selected = thing is target
        self.message = f"Kamera na: {kind}."

    def select_idle_worker(self) -> None:
        worker = next((t for t in self.things if t.team == PLAYER and t.kind == self.race_name("worker") and t.alive and not t.target and t.target_x is None), None)
        if not worker:
            self.message = "Brak bezczynnych Peasantow."
            return
        for thing in self.things:
            thing.selected = thing is worker
        self.camera_x, self.camera_z = worker.x, worker.z
        self.message = "Wybrano bezczynnego Peasanta."

    def select_army(self) -> None:
        army = [t for t in self.things if t.team == PLAYER and t.kind in UNITS and t.kind != self.race_name("worker") and t.alive]
        for thing in self.things:
            thing.selected = thing in army
        self.message = f"Wybrano cala armie: {len(army)} jednostek."


def main() -> None:
    ArcaneFrontiers3D()
    pyglet.app.run()


if __name__ == "__main__":
    main()
