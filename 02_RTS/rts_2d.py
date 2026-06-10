from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import arcade


SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 760
HUD_HEIGHT = 154
MAP_HEIGHT = SCREEN_HEIGHT - HUD_HEIGHT
WORLD_WIDTH = 2200
WORLD_HEIGHT = 1180
CAMERA_SPEED = 560
EDGE_SCROLL_SIZE = 22
TITLE = "RTS - 2D Prototype"

PLAYER = "player"
ENEMY = "enemy"
NEUTRAL = "neutral"


def dist(a_x: float, a_y: float, b_x: float, b_y: float) -> float:
    return math.hypot(a_x - b_x, a_y - b_y)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass
class Entity:
    kind: str
    team: str
    x: float
    y: float
    radius: float
    hp: float
    max_hp: float
    speed: float = 0
    attack: float = 0
    attack_range: float = 0
    attack_cooldown: float = 0.9
    gather_rate: float = 0
    cost_gold: int = 0
    cost_wood: int = 0
    target_x: float | None = None
    target_y: float | None = None
    target: "Entity | None" = None
    cooldown: float = 0
    selected: bool = False
    carrying: int = 0
    gather_target: "ResourceNode | None" = None
    rally_x: float | None = None
    rally_y: float | None = None
    train_queue: list[str] = field(default_factory=list)
    train_timer: float = 0
    build_time: float = 0
    build_progress: float = 0
    builder: "Entity | None" = None
    complete: bool = True
    research: str | None = None
    food_cost: int = 0
    armor: int = 0

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def is_building(self) -> bool:
        return self.kind in BUILDING_STATS


@dataclass
class ResourceNode:
    kind: str
    x: float
    y: float
    radius: float
    amount: int

    @property
    def alive(self) -> bool:
        return self.amount > 0


UNIT_STATS = {
    "Peasant": dict(radius=13, hp=48, speed=94, attack=3, attack_range=26, gather_rate=10, cost_gold=55, cost_wood=0, food=1, time=5, producer="Town Hall", requires=[]),
    "Footman": dict(radius=15, hp=92, speed=72, attack=14, attack_range=30, gather_rate=0, cost_gold=90, cost_wood=15, food=2, time=7, producer="Barracks", requires=[]),
    "Archer": dict(radius=13, hp=58, speed=78, attack=10, attack_range=156, gather_rate=0, cost_gold=80, cost_wood=35, food=2, time=6.5, producer="Barracks", requires=["Lumber Mill"]),
    "Knight": dict(radius=18, hp=150, speed=104, attack=23, attack_range=34, gather_rate=0, cost_gold=165, cost_wood=45, food=3, time=11, producer="Barracks", requires=["Keep", "Blacksmith"]),
    "Priest": dict(radius=13, hp=62, speed=80, attack=6, attack_range=128, gather_rate=0, cost_gold=105, cost_wood=50, food=2, time=8, producer="Arcane Sanctum", requires=["Keep"]),
    "Mage": dict(radius=14, hp=70, speed=76, attack=18, attack_range=172, gather_rate=0, cost_gold=145, cost_wood=80, food=3, time=10, producer="Arcane Sanctum", requires=["Keep", "Blacksmith"]),
    "Catapult": dict(radius=21, hp=120, speed=48, attack=42, attack_range=245, gather_rate=0, cost_gold=190, cost_wood=120, food=4, time=13, producer="Workshop", requires=["Blacksmith"]),
    "Grunt": dict(radius=17, hp=115, speed=72, attack=17, attack_range=32, gather_rate=0, cost_gold=0, cost_wood=0, food=2, time=0, producer="", requires=[]),
    "Raider": dict(radius=18, hp=135, speed=99, attack=18, attack_range=38, gather_rate=0, cost_gold=0, cost_wood=0, food=3, time=0, producer="", requires=[]),
    "Necrolyte": dict(radius=14, hp=72, speed=76, attack=16, attack_range=160, gather_rate=0, cost_gold=0, cost_wood=0, food=3, time=0, producer="", requires=[]),
    "Ogre": dict(radius=21, hp=180, speed=64, attack=27, attack_range=38, gather_rate=0, cost_gold=0, cost_wood=0, food=4, time=0, producer="", requires=[]),
}

BUILDING_STATS = {
    "Town Hall": dict(radius=42, hp=720, cost_gold=0, cost_wood=0, time=0, provides_food=10, requires=[]),
    "Keep": dict(radius=46, hp=960, cost_gold=420, cost_wood=240, time=24, provides_food=14, requires=["Barracks"]),
    "Farm": dict(radius=25, hp=220, cost_gold=80, cost_wood=30, time=11, provides_food=6, requires=[]),
    "Barracks": dict(radius=38, hp=460, cost_gold=210, cost_wood=160, time=19, provides_food=0, requires=[]),
    "Lumber Mill": dict(radius=32, hp=360, cost_gold=140, cost_wood=90, time=16, provides_food=0, requires=[]),
    "Blacksmith": dict(radius=34, hp=410, cost_gold=180, cost_wood=130, time=18, provides_food=0, requires=["Barracks"]),
    "Arcane Sanctum": dict(radius=34, hp=380, cost_gold=220, cost_wood=160, time=21, provides_food=0, requires=["Keep"]),
    "Workshop": dict(radius=36, hp=430, cost_gold=240, cost_wood=170, time=22, provides_food=0, requires=["Blacksmith"]),
    "Tower": dict(radius=28, hp=310, attack=16, attack_range=205, attack_cooldown=1.2, cost_gold=125, cost_wood=95, time=15, provides_food=0, requires=["Lumber Mill"]),
}

TRAIN_TIME = {name: data["time"] for name, data in UNIT_STATS.items()}

BUILD_HOTKEYS = {
    arcade.key.F: "Farm",
    arcade.key.B: "Barracks",
    arcade.key.L: "Lumber Mill",
    arcade.key.S: "Blacksmith",
    arcade.key.C: "Arcane Sanctum",
    arcade.key.G: "Workshop",
    arcade.key.T: "Tower",
}

TRAIN_HOTKEYS = {
    arcade.key.Q: "Peasant",
    arcade.key.W: "Footman",
    arcade.key.E: "Archer",
    arcade.key.R: "Knight",
    arcade.key.P: "Priest",
    arcade.key.M: "Mage",
    arcade.key.X: "Catapult",
}


class ArcaneFrontiers2D(arcade.Window):
    def __init__(self) -> None:
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, resizable=False)
        arcade.set_background_color((31, 39, 32))
        self.entities: list[Entity] = []
        self.resources: list[ResourceNode] = []
        self.messages: list[tuple[str, float]] = []
        self.gold = 420
        self.wood = 280
        self.food_used = 0
        self.food_cap = 0
        self.wave_timer = 28.0
        self.wave = 0
        self.game_over = False
        self.victory = False
        self.pending_building: str | None = None
        self.upgrades: set[str] = set()
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.keys_down: set[int] = set()
        self.drag_start: tuple[float, float] | None = None
        self.mouse_pos = (0.0, 0.0)
        self.init_world()

    def reset_game(self) -> None:
        for e in self.entities:
            e.selected = False
        self.entities.clear()
        self.resources.clear()
        self.messages.clear()
        self.gold = 420
        self.wood = 280
        self.food_used = 0
        self.food_cap = 0
        self.wave_timer = 28.0
        self.wave = 0
        self.game_over = False
        self.victory = False
        self.pending_building = None
        self.upgrades.clear()
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.keys_down.clear()
        self.drag_start = None
        self.mouse_pos = (0.0, 0.0)
        self.init_world()

    def init_world(self) -> None:
        self.resources = [
            ResourceNode("Gold Mine", 195, 410, 38, 2600),
            ResourceNode("Gold Mine", 970, 520, 38, 2300),
            ResourceNode("Gold Mine", 1750, 820, 38, 2600),
            ResourceNode("Forest", 330, 270, 31, 950),
            ResourceNode("Forest", 405, 525, 31, 900),
            ResourceNode("Forest", 780, 300, 31, 1050),
            ResourceNode("Forest", 1120, 215, 31, 920),
            ResourceNode("Forest", 1520, 620, 31, 1100),
            ResourceNode("Forest", 1940, 940, 31, 980),
        ]
        self.entities = [
            self.make_building("Town Hall", PLAYER, 150, 160),
            self.make_building("Farm", PLAYER, 230, 90),
            self.make_building("Farm", PLAYER, 285, 85),
            self.make_building("Barracks", PLAYER, 320, 155),
            self.make_building("Lumber Mill", PLAYER, 365, 255),
            self.make_building("Tower", PLAYER, 230, 260),
            self.make_unit("Peasant", PLAYER, 235, 145),
            self.make_unit("Peasant", PLAYER, 210, 110),
            self.make_unit("Peasant", PLAYER, 270, 105),
            self.make_unit("Footman", PLAYER, 385, 180),
            self.make_unit("Archer", PLAYER, 415, 130),
            self.make_building("Town Hall", ENEMY, 1900, 830),
            self.make_building("Barracks", ENEMY, 1810, 775),
            self.make_building("Blacksmith", ENEMY, 1965, 720),
            self.make_building("Tower", ENEMY, 1780, 760),
            self.make_unit("Grunt", ENEMY, 1720, 830),
            self.make_unit("Grunt", ENEMY, 1810, 900),
            self.make_unit("Raider", ENEMY, 1850, 690),
        ]
        self.recalculate_food()
        self.message("Budowa: zaznacz Peasanta, F/B/L/S/C/G/T, potem LPM na mapie. Strzalki lub krawedz myszy ruszaja kamera.")

    def world_to_screen(self, x: float, y: float) -> tuple[float, float]:
        return x - self.camera_x, y - self.camera_y + HUD_HEIGHT

    def screen_to_world(self, x: float, y: float) -> tuple[float, float]:
        return x + self.camera_x, y - HUD_HEIGHT + self.camera_y

    def is_visible(self, x: float, y: float, radius: float = 0) -> bool:
        sx, sy = self.world_to_screen(x, y)
        return -radius <= sx <= SCREEN_WIDTH + radius and HUD_HEIGHT - radius <= sy <= SCREEN_HEIGHT + radius

    def clamp_camera(self) -> None:
        self.camera_x = clamp(self.camera_x, 0, WORLD_WIDTH - SCREEN_WIDTH)
        self.camera_y = clamp(self.camera_y, 0, WORLD_HEIGHT - MAP_HEIGHT)

    def make_unit(self, kind: str, team: str, x: float, y: float) -> Entity:
        stats = UNIT_STATS[kind]
        bonus = 0
        if team == PLAYER:
            bonus += 3 if "Steel Weapons" in self.upgrades else 0
        return Entity(
            kind=kind,
            team=team,
            x=x,
            y=y,
            radius=stats["radius"],
            max_hp=stats["hp"],
            hp=stats["hp"],
            speed=stats["speed"],
            attack=stats["attack"] + bonus,
            attack_range=stats["attack_range"],
            gather_rate=stats["gather_rate"],
            cost_gold=stats["cost_gold"],
            cost_wood=stats["cost_wood"],
            food_cost=stats["food"],
        )

    def make_building(self, kind: str, team: str, x: float, y: float) -> Entity:
        stats = BUILDING_STATS[kind]
        return Entity(
            kind=kind,
            team=team,
            x=x,
            y=y,
            radius=stats["radius"],
            max_hp=stats["hp"],
            hp=stats["hp"],
            attack=stats.get("attack", 0),
            attack_range=stats.get("attack_range", 0),
            attack_cooldown=stats.get("attack_cooldown", 1.0),
            cost_gold=stats.get("cost_gold", 0),
            cost_wood=stats.get("cost_wood", 0),
        )

    def make_construction(self, kind: str, team: str, x: float, y: float, builder: Entity) -> Entity:
        building = self.make_building(kind, team, x, y)
        building.complete = False
        building.build_time = BUILDING_STATS[kind]["time"]
        building.build_progress = 0
        building.builder = builder
        building.hp = max(12, building.max_hp * 0.12)
        return building

    def message(self, text: str) -> None:
        self.messages.append((text, 5.5))
        self.messages = self.messages[-5:]

    def on_draw(self) -> None:
        self.clear()
        self.draw_map()
        for resource in self.resources:
            if resource.alive:
                self.draw_resource(resource)
        for entity in sorted(self.entities, key=lambda e: e.y, reverse=True):
            if entity.alive:
                self.draw_entity(entity)
        self.draw_build_preview()
        self.draw_drag_box()
        self.draw_hud()
        if self.game_over or self.victory:
            self.draw_end_screen()

    def draw_map(self) -> None:
        arcade.draw_lbwh_rectangle_filled(0, HUD_HEIGHT, SCREEN_WIDTH, MAP_HEIGHT, (47, 71, 47))
        start_x = int(self.camera_x // 64) * 64
        end_x = int((self.camera_x + SCREEN_WIDTH) // 64 + 2) * 64
        for world_x in range(start_x, end_x, 64):
            sx, _ = self.world_to_screen(world_x, 0)
            arcade.draw_line(sx, HUD_HEIGHT, sx, SCREEN_HEIGHT, (58, 84, 57), 1)
        start_y = int(self.camera_y // 64) * 64
        end_y = int((self.camera_y + MAP_HEIGHT) // 64 + 2) * 64
        for world_y in range(start_y, end_y, 64):
            _, sy = self.world_to_screen(0, world_y)
            arcade.draw_line(0, sy, SCREEN_WIDTH, sy, (58, 84, 57), 1)
        river = [(980, 0), (1020, 230), (990, 420), (1070, 650), (1035, WORLD_HEIGHT), (1170, WORLD_HEIGHT), (1145, 700), (1200, 470), (1130, 240), (1170, 0)]
        river_screen = [self.world_to_screen(x, y) for x, y in river]
        arcade.draw_polygon_filled(river_screen, (44, 85, 102))
        arcade.draw_polygon_outline(river_screen, (66, 126, 143), 2)
        road_start = self.world_to_screen(35, 80)
        road_end = self.world_to_screen(2080, 940)
        arcade.draw_line(road_start[0], road_start[1], road_end[0], road_end[1], (84, 99, 62), 4)
        x0, y0 = self.world_to_screen(0, 0)
        x1, y1 = self.world_to_screen(WORLD_WIDTH, WORLD_HEIGHT)
        arcade.draw_lbwh_rectangle_outline(x0, y0, x1 - x0, y1 - y0, (139, 121, 72), 3)

    def draw_resource(self, r: ResourceNode) -> None:
        if not self.is_visible(r.x, r.y, r.radius + 55):
            return
        sx, sy = self.world_to_screen(r.x, r.y)
        if r.kind == "Gold Mine":
            arcade.draw_circle_filled(sx, sy, r.radius, (111, 92, 49))
            arcade.draw_circle_filled(sx - 8, sy + 5, r.radius * 0.65, (209, 170, 57))
            arcade.draw_text(str(int(r.amount)), sx - 22, sy - 54, (252, 232, 132), 11)
        else:
            for angle in (0, 90, 180, 270):
                dx = math.cos(math.radians(angle)) * 10
                dy = math.sin(math.radians(angle)) * 10
                arcade.draw_circle_filled(sx + dx, sy + dy, r.radius * 0.54, (28, 91, 45))
            arcade.draw_circle_filled(sx, sy, r.radius * 0.6, (37, 119, 58))
            arcade.draw_text(str(int(r.amount)), sx - 21, sy - 49, (185, 233, 164), 11)

    def draw_entity(self, e: Entity) -> None:
        if not self.is_visible(e.x, e.y, max(e.radius, e.attack_range) + 30):
            return
        sx, sy = self.world_to_screen(e.x, e.y)
        color = self.entity_color(e)
        shadow = (18, 23, 19, 145)
        arcade.draw_ellipse_filled(sx, sy - e.radius * 0.8, e.radius * 2.2, e.radius * 0.65, shadow)
        if e.is_building:
            arcade.draw_circle_filled(sx, sy, e.radius, color)
            arcade.draw_circle_outline(sx, sy, e.radius, (30, 25, 21), 3)
            if not e.complete:
                pct = clamp(e.build_progress / max(0.1, e.build_time), 0, 1)
                arcade.draw_circle_outline(sx, sy, e.radius + 8, (241, 205, 98), 3)
                arcade.draw_text(f"{int(pct * 100)}%", sx - 15, sy - 7, (255, 235, 150), 12, bold=True)
            if e.kind == "Tower":
                arcade.draw_circle_outline(sx, sy, e.attack_range, (180, 172, 85, 50), 1)
        else:
            arcade.draw_circle_filled(sx, sy, e.radius, color)
            arcade.draw_circle_filled(sx - e.radius * 0.25, sy + e.radius * 0.24, e.radius * 0.33, (238, 221, 181))
            if e.kind in {"Archer", "Mage", "Priest", "Necrolyte", "Catapult"}:
                arcade.draw_line(sx + 6, sy + 4, sx + 21, sy + 15, (94, 55, 31), 3)
            if e.kind in {"Knight", "Raider"}:
                arcade.draw_circle_outline(sx, sy, e.radius + 4, (80, 65, 45), 3)
        if e.selected:
            arcade.draw_circle_outline(sx, sy, e.radius + 7, (115, 224, 255), 3)
        self.draw_health_bar(e)
        if e.train_queue:
            arcade.draw_text(str(len(e.train_queue)), sx - 5, sy + e.radius + 14, (255, 242, 168), 13, bold=True)

    def entity_color(self, e: Entity) -> tuple[int, int, int]:
        if e.team == ENEMY:
            return {"Town Hall": (112, 39, 39), "Barracks": (118, 44, 38), "Blacksmith": (96, 57, 49), "Tower": (142, 64, 39), "Grunt": (128, 48, 35), "Raider": (152, 71, 42), "Necrolyte": (104, 42, 120), "Ogre": (91, 121, 62)}.get(e.kind, (148, 45, 42))
        color = {
            "Town Hall": (84, 102, 132),
            "Keep": (92, 118, 158),
            "Farm": (151, 127, 77),
            "Barracks": (107, 89, 69),
            "Lumber Mill": (88, 130, 73),
            "Blacksmith": (106, 96, 96),
            "Arcane Sanctum": (102, 84, 151),
            "Workshop": (118, 103, 73),
            "Tower": (129, 118, 83),
            "Peasant": (219, 177, 83),
            "Footman": (77, 118, 188),
            "Archer": (69, 155, 96),
            "Knight": (182, 182, 205),
            "Priest": (230, 225, 172),
            "Mage": (120, 102, 220),
            "Catapult": (127, 102, 66),
        }.get(e.kind, (100, 170, 210))
        if e.is_building and not e.complete:
            return tuple(max(25, int(c * 0.62)) for c in color)
        return color

    def draw_health_bar(self, e: Entity) -> None:
        width = max(34, e.radius * 2.1)
        pct = clamp(e.hp / e.max_hp, 0, 1)
        sx, sy = self.world_to_screen(e.x, e.y)
        x = sx - width / 2
        y = sy + e.radius + 7
        arcade.draw_lbwh_rectangle_filled(x, y, width, 5, (42, 24, 24))
        arcade.draw_lbwh_rectangle_filled(x, y, width * pct, 5, (67, 216, 91) if pct > 0.45 else (231, 183, 70))

    def draw_drag_box(self) -> None:
        if not self.drag_start:
            return
        x1, y1 = self.drag_start
        x2, y2 = self.mouse_pos
        left, right = sorted((x1, x2))
        bottom, top = sorted((y1, y2))
        arcade.draw_lbwh_rectangle_outline(left, bottom, right - left, top - bottom, (113, 226, 255), 2)

    def draw_build_preview(self) -> None:
        if not self.pending_building or self.mouse_pos[1] < HUD_HEIGHT:
            return
        world_x, world_y = self.screen_to_world(*self.mouse_pos)
        radius = BUILDING_STATS[self.pending_building]["radius"]
        sx, sy = self.world_to_screen(world_x, world_y)
        color = (97, 220, 118, 120) if self.can_place_building(self.pending_building, world_x, world_y) else (235, 82, 70, 130)
        arcade.draw_circle_filled(sx, sy, radius, color)
        arcade.draw_circle_outline(sx, sy, radius, (255, 245, 186), 2)

    def draw_hud(self) -> None:
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, HUD_HEIGHT, (30, 27, 24))
        arcade.draw_line(0, HUD_HEIGHT, SCREEN_WIDTH, HUD_HEIGHT, (164, 133, 72), 3)
        arcade.draw_text(f"Zloto {self.gold}", 24, 112, (255, 221, 105), 18, bold=True)
        arcade.draw_text(f"Drewno {self.wood}", 154, 112, (145, 229, 126), 18, bold=True)
        arcade.draw_text(f"Populacja {self.food_used}/{self.food_cap}", 300, 112, (206, 220, 232), 18, bold=True)
        arcade.draw_text(f"Fala za {max(0, int(self.wave_timer))}s  |  Fala {self.wave}", 510, 112, (240, 188, 115), 18, bold=True)

        selected = [e for e in self.entities if e.selected and e.alive and e.team == PLAYER]
        name = "Brak zaznaczenia" if not selected else (selected[0].kind if len(selected) == 1 else f"Grupa: {len(selected)} jednostek")
        arcade.draw_text(name, 25, 72, (232, 226, 206), 20, bold=True)
        if self.pending_building:
            arcade.draw_text(f"Budowa: {self.pending_building} - LPM stawia, ESC anuluje", 25, 42, (255, 221, 105), 15, bold=True)
        else:
            arcade.draw_text("Trenuj: Q Peasant, W Footman, E Archer, R Knight, P Priest, M Mage, X Catapult | U Keep | 1/2 ulepszenia", 25, 42, (188, 190, 184), 13)
        arcade.draw_text("Buduj: F Farm, B Barracks, L Lumber Mill, S Blacksmith, C Sanctum, G Workshop, T Tower. Kamera: strzalki/krawedz.", 25, 18, (157, 159, 151), 13)

        for index, (msg, _) in enumerate(reversed(self.messages[-3:])):
            arcade.draw_text(msg, 730, 78 - index * 24, (232, 215, 174), 13)

    def draw_end_screen(self) -> None:
        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (0, 0, 0, 150))
        text = "ZWYCIESTWO" if self.victory else "PORAZKA"
        color = (136, 235, 137) if self.victory else (245, 95, 82)
        arcade.draw_text(text, 0, 388, color, 56, width=SCREEN_WIDTH, align="center", bold=True)
        arcade.draw_text("Nacisnij ENTER, aby zaczac od nowa", 0, 342, (245, 235, 199), 20, width=SCREEN_WIDTH, align="center")

    def on_update(self, delta_time: float) -> None:
        self.update_camera(delta_time)
        if self.game_over or self.victory:
            return
        self.messages = [(m, t - delta_time) for m, t in self.messages if t - delta_time > 0]
        self.wave_timer -= delta_time
        if self.wave_timer <= 0:
            self.spawn_wave()
        for e in list(self.entities):
            if not e.alive:
                continue
            e.cooldown = max(0, e.cooldown - delta_time)
            if e.is_building and not e.complete:
                self.update_construction(e, delta_time)
                continue
            if e.team == PLAYER and e.is_building:
                self.update_training(e, delta_time)
            if e.team == ENEMY:
                self.enemy_brain(e)
            if e.kind == "Priest":
                self.update_priest(e)
            if e.attack > 0:
                self.update_attack(e)
            if e.kind == "Peasant":
                self.update_worker(e, delta_time)
            self.update_movement(e, delta_time)
        self.resolve_collisions()
        self.entities = [e for e in self.entities if e.alive]
        self.resources = [r for r in self.resources if r.alive]
        self.recalculate_food()
        player_hall = any(e.team == PLAYER and e.kind in {"Town Hall", "Keep"} and e.complete for e in self.entities)
        enemy_hall = any(e.team == ENEMY and e.kind in {"Town Hall", "Keep"} and e.complete for e in self.entities)
        self.game_over = not player_hall
        self.victory = not enemy_hall

    def recalculate_food(self) -> None:
        self.food_used = sum(e.food_cost for e in self.entities if e.team == PLAYER and e.alive and not e.is_building)
        self.food_cap = sum(BUILDING_STATS[e.kind].get("provides_food", 0) for e in self.entities if e.team == PLAYER and e.alive and e.is_building and e.complete)

    def update_construction(self, building: Entity, dt: float) -> None:
        builder = building.builder
        if not builder or not builder.alive:
            return
        if dist(builder.x, builder.y, building.x, building.y) > builder.radius + building.radius + 8:
            builder.target_x = building.x
            builder.target_y = building.y
            return
        builder.target_x = None
        builder.target_y = None
        building.build_progress += dt
        pct = clamp(building.build_progress / max(0.1, building.build_time), 0, 1)
        building.hp = max(building.hp, building.max_hp * (0.12 + pct * 0.88))
        if building.build_progress >= building.build_time:
            building.complete = True
            building.hp = building.max_hp
            building.builder = None
            self.message(f"Ukonczono budowe: {building.kind}.")

    def update_training(self, building: Entity, dt: float) -> None:
        if not building.complete:
            return
        if not building.train_queue:
            return
        building.train_timer -= dt
        if building.train_timer > 0:
            return
        kind = building.train_queue.pop(0)
        if kind == "UPGRADE_KEEP":
            building.kind = "Keep"
            building.radius = BUILDING_STATS["Keep"]["radius"]
            building.max_hp = BUILDING_STATS["Keep"]["hp"]
            building.hp = building.max_hp
            self.message("Town Hall ulepszony do Keep.")
            if building.train_queue:
                building.train_timer = self.queue_time(building.train_queue[0])
            return
        if kind == "UPGRADE_STEEL":
            self.upgrades.add("Steel Weapons")
            self.message("Ulepszenie: Steel Weapons. Nowe jednostki bija mocniej.")
            if building.train_queue:
                building.train_timer = self.queue_time(building.train_queue[0])
            return
        if kind == "UPGRADE_ARMOR":
            self.upgrades.add("Plated Armor")
            for unit in self.entities:
                if unit.team == PLAYER and not unit.is_building:
                    unit.max_hp += 8
                    unit.hp += 8
            self.message("Ulepszenie: Plated Armor. Armia jest wytrzymalsza.")
            if building.train_queue:
                building.train_timer = self.queue_time(building.train_queue[0])
            return
        angle = random.uniform(0, math.tau)
        spawn_x = building.rally_x or building.x + math.cos(angle) * (building.radius + 45)
        spawn_y = building.rally_y or building.y + math.sin(angle) * (building.radius + 45)
        unit = self.make_unit(kind, PLAYER, building.x + math.cos(angle) * (building.radius + 28), building.y + math.sin(angle) * (building.radius + 28))
        unit.target_x = spawn_x
        unit.target_y = spawn_y
        self.entities.append(unit)
        if building.train_queue:
            building.train_timer = self.queue_time(building.train_queue[0])

    def update_attack(self, e: Entity) -> None:
        enemies = [other for other in self.entities if other.team != e.team and other.team != NEUTRAL and other.alive]
        if e.target and (not e.target.alive or e.target.team == e.team):
            e.target = None
        if not e.target:
            in_range = [other for other in enemies if dist(e.x, e.y, other.x, other.y) <= e.attack_range + other.radius]
            if in_range:
                e.target = min(in_range, key=lambda other: dist(e.x, e.y, other.x, other.y))
        if not e.target:
            return
        distance = dist(e.x, e.y, e.target.x, e.target.y)
        if distance <= e.attack_range + e.target.radius:
            e.target_x = None
            e.target_y = None
            if e.cooldown <= 0:
                e.target.hp -= e.attack
                if e.kind in {"Mage", "Catapult", "Necrolyte"}:
                    splash = 48 if e.kind != "Catapult" else 72
                    for other in enemies:
                        if other is not e.target and dist(other.x, other.y, e.target.x, e.target.y) <= splash:
                            other.hp -= e.attack * 0.35
                e.cooldown = e.attack_cooldown
        elif not e.is_building:
            e.target_x = e.target.x
            e.target_y = e.target.y

    def update_priest(self, e: Entity) -> None:
        if e.cooldown > 0:
            return
        allies = [a for a in self.entities if a.team == e.team and a.alive and not a.is_building and a.hp < a.max_hp and dist(e.x, e.y, a.x, a.y) <= 150]
        if not allies:
            return
        ally = min(allies, key=lambda a: a.hp / a.max_hp)
        ally.hp = min(ally.max_hp, ally.hp + 16)
        e.cooldown = 1.1

    def update_worker(self, e: Entity, dt: float) -> None:
        if not e.gather_target or not e.gather_target.alive:
            return
        r = e.gather_target
        if dist(e.x, e.y, r.x, r.y) > e.radius + r.radius + 5:
            e.target_x = r.x
            e.target_y = r.y
            return
        e.target_x = None
        e.target_y = None
        amount = min(r.amount, e.gather_rate * dt)
        r.amount -= amount
        e.carrying += amount
        if e.carrying >= 10:
            delivered = int(e.carrying)
            if r.kind == "Gold Mine":
                self.gold += delivered
            else:
                self.wood += delivered
            e.carrying -= delivered

    def update_movement(self, e: Entity, dt: float) -> None:
        if e.is_building or e.target_x is None or e.target_y is None:
            return
        dx = e.target_x - e.x
        dy = e.target_y - e.y
        d = math.hypot(dx, dy)
        if d < 4:
            e.target_x = None
            e.target_y = None
            return
        step = min(d, e.speed * dt)
        e.x += dx / d * step
        e.y += dy / d * step
        e.x = clamp(e.x, e.radius, WORLD_WIDTH - e.radius)
        e.y = clamp(e.y, e.radius, WORLD_HEIGHT - e.radius)

    def update_camera(self, dt: float) -> None:
        dx = 0.0
        dy = 0.0
        if arcade.key.LEFT in self.keys_down or arcade.key.NUM_4 in self.keys_down:
            dx -= 1
        if arcade.key.RIGHT in self.keys_down or arcade.key.NUM_6 in self.keys_down:
            dx += 1
        if arcade.key.DOWN in self.keys_down or arcade.key.NUM_2 in self.keys_down:
            dy -= 1
        if arcade.key.UP in self.keys_down or arcade.key.NUM_8 in self.keys_down:
            dy += 1
        mx, my = self.mouse_pos
        if HUD_HEIGHT <= my <= SCREEN_HEIGHT:
            if mx <= EDGE_SCROLL_SIZE:
                dx -= 1
            elif mx >= SCREEN_WIDTH - EDGE_SCROLL_SIZE:
                dx += 1
            if my <= HUD_HEIGHT + EDGE_SCROLL_SIZE:
                dy -= 1
            elif my >= SCREEN_HEIGHT - EDGE_SCROLL_SIZE:
                dy += 1
        if dx and dy:
            scale = 1 / math.sqrt(2)
            dx *= scale
            dy *= scale
        self.camera_x += dx * CAMERA_SPEED * dt
        self.camera_y += dy * CAMERA_SPEED * dt
        self.clamp_camera()

    def resolve_collisions(self) -> None:
        movable = [e for e in self.entities if e.alive and not e.is_building]
        for i, a in enumerate(movable):
            for b in movable[i + 1 :]:
                d = dist(a.x, a.y, b.x, b.y)
                min_d = a.radius + b.radius + 2
                if 0 < d < min_d:
                    push = (min_d - d) * 0.5
                    nx, ny = (a.x - b.x) / d, (a.y - b.y) / d
                    a.x += nx * push
                    a.y += ny * push
                    b.x -= nx * push
                    b.y -= ny * push

    def enemy_brain(self, e: Entity) -> None:
        if e.is_building:
            return
        if e.target and e.target.alive:
            return
        player_targets = [p for p in self.entities if p.team == PLAYER and p.alive]
        if player_targets:
            near = min(player_targets, key=lambda p: dist(e.x, e.y, p.x, p.y))
            if dist(e.x, e.y, near.x, near.y) < 380 or self.wave >= 2:
                e.target = near
                e.target_x = near.x
                e.target_y = near.y

    def spawn_wave(self) -> None:
        self.wave += 1
        self.wave_timer = max(18.0, 32.0 - self.wave * 1.2)
        count = 2 + self.wave
        for i in range(count):
            if self.wave >= 5 and i % 5 == 0:
                kind = "Ogre"
            elif self.wave >= 3 and i % 4 == 0:
                kind = "Necrolyte"
            elif i % 3 == 0 and self.wave > 1:
                kind = "Raider"
            else:
                kind = "Grunt"
            e = self.make_unit(kind, ENEMY, 1870 + random.uniform(-70, 80), 850 + random.uniform(-80, 60))
            target = self.find_player_priority_target()
            if target:
                e.target = target
                e.target_x = target.x
                e.target_y = target.y
            self.entities.append(e)
        self.message(f"Nadciaga fala {self.wave}: {count} wrogow.")

    def find_player_priority_target(self) -> Entity | None:
        targets = [e for e in self.entities if e.team == PLAYER and e.alive]
        halls = [e for e in targets if e.kind in {"Town Hall", "Keep"}]
        return halls[0] if halls else (targets[0] if targets else None)

    def has_building(self, kind: str) -> bool:
        return any(e.team == PLAYER and e.kind == kind and e.alive and e.is_building and e.complete for e in self.entities)

    def missing_requirements(self, requirements: list[str]) -> list[str]:
        return [req for req in requirements if not self.has_building(req)]

    def can_afford(self, gold: int, wood: int) -> bool:
        return self.gold >= gold and self.wood >= wood

    def can_place_building(self, kind: str, x: float, y: float) -> bool:
        radius = BUILDING_STATS[kind]["radius"]
        if x - radius < 0 or y - radius < 0 or x + radius > WORLD_WIDTH or y + radius > WORLD_HEIGHT:
            return False
        if 960 < x < 1210 and 0 < y < WORLD_HEIGHT:
            return False
        for resource in self.resources:
            if resource.alive and dist(x, y, resource.x, resource.y) < radius + resource.radius + 20:
                return False
        for entity in self.entities:
            if entity.alive and dist(x, y, entity.x, entity.y) < radius + entity.radius + 18:
                return False
        return True

    def selected_workers(self) -> list[Entity]:
        return [e for e in self.entities if e.team == PLAYER and e.kind == "Peasant" and e.selected and e.alive]

    def queue_time(self, item: str) -> float:
        if item == "UPGRADE_KEEP":
            return BUILDING_STATS["Keep"]["time"]
        if item in {"UPGRADE_STEEL", "UPGRADE_ARMOR"}:
            return 14.0
        return TRAIN_TIME[item]

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        self.mouse_pos = (x, y)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:
        if y < HUD_HEIGHT or self.game_over or self.victory:
            return
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.pending_building:
                world_x, world_y = self.screen_to_world(x, y)
                self.place_pending_building(world_x, world_y)
                return
            self.drag_start = (x, y)
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            if self.pending_building:
                self.pending_building = None
                self.message("Anulowano budowe.")
                return
            self.issue_order(x, y)

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int) -> None:
        if button != arcade.MOUSE_BUTTON_LEFT or not self.drag_start:
            return
        x1, y1 = self.drag_start
        self.drag_start = None
        if dist(x1, y1, x, y) < 8:
            world_x, world_y = self.screen_to_world(x, y)
            clicked = self.entity_at(world_x, world_y)
            for e in self.entities:
                e.selected = False
            if clicked and clicked.team == PLAYER:
                clicked.selected = True
            return
        world_x1, world_y1 = self.screen_to_world(x1, y1)
        world_x2, world_y2 = self.screen_to_world(x, y)
        left, right = sorted((world_x1, world_x2))
        bottom, top = sorted((world_y1, world_y2))
        selected_units = [e for e in self.entities if e.team == PLAYER and e.alive and not e.is_building and left <= e.x <= right and bottom <= e.y <= top]
        if selected_units:
            for e in self.entities:
                e.selected = e in selected_units

    def entity_at(self, x: float, y: float) -> Entity | None:
        hits = [e for e in self.entities if e.alive and dist(e.x, e.y, x, y) <= e.radius + 8]
        return min(hits, key=lambda e: dist(e.x, e.y, x, y)) if hits else None

    def resource_at(self, x: float, y: float) -> ResourceNode | None:
        hits = [r for r in self.resources if r.alive and dist(r.x, r.y, x, y) <= r.radius + 10]
        return min(hits, key=lambda r: dist(r.x, r.y, x, y)) if hits else None

    def issue_order(self, x: float, y: float) -> None:
        x, y = self.screen_to_world(x, y)
        selected = [e for e in self.entities if e.selected and e.alive and e.team == PLAYER]
        if not selected:
            return
        target = self.entity_at(x, y)
        resource = self.resource_at(x, y)
        formation_count = max(1, len(selected))
        for index, e in enumerate(selected):
            if e.is_building:
                e.rally_x = x
                e.rally_y = y
                continue
            if target and target.team == ENEMY:
                e.target = target
                e.target_x = target.x
                e.target_y = target.y
                e.gather_target = None
            elif resource and e.kind == "Peasant":
                e.gather_target = resource
                e.target = None
                e.target_x = resource.x
                e.target_y = resource.y
            else:
                angle = math.tau * index / formation_count
                ring = 12 + 11 * math.sqrt(index)
                e.target = None
                e.gather_target = None
                e.target_x = x + math.cos(angle) * ring
                e.target_y = y + math.sin(angle) * ring

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        self.keys_down.add(symbol)
        if symbol == arcade.key.ENTER and (self.game_over or self.victory):
            self.reset_game()
            return
        if self.game_over or self.victory:
            return
        if symbol == arcade.key.ESCAPE:
            if self.pending_building:
                self.pending_building = None
                self.message("Anulowano budowe.")
            else:
                for e in self.entities:
                    e.selected = False
            return
        if symbol == arcade.key.A:
            self.message("Tryb atak-ruch: kliknij PPM na przeciwnika albo teren w jego strone.")
        elif symbol in BUILD_HOTKEYS:
            self.start_build_mode(BUILD_HOTKEYS[symbol])
        elif symbol in TRAIN_HOTKEYS:
            self.try_train(TRAIN_HOTKEYS[symbol])
        elif symbol == arcade.key.U:
            self.try_upgrade_keep()
        elif symbol == arcade.key.KEY_1:
            self.try_research("UPGRADE_STEEL")
        elif symbol == arcade.key.KEY_2:
            self.try_research("UPGRADE_ARMOR")

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        self.keys_down.discard(symbol)

    def try_train(self, kind: str) -> None:
        stats = UNIT_STATS[kind]
        producer_kind = stats["producer"]
        producer_kinds = {"Town Hall", "Keep"} if kind == "Peasant" else {producer_kind}
        missing = self.missing_requirements(stats["requires"])
        if missing:
            self.message(f"Brakuje: {', '.join(missing)}.")
            return
        producers = [e for e in self.entities if e.team == PLAYER and e.kind in producer_kinds and e.alive and e.complete and e.selected]
        if not producers:
            producers = [e for e in self.entities if e.team == PLAYER and e.kind in producer_kinds and e.alive and e.complete]
        if not producers:
            self.message(f"Potrzebujesz: {producer_kind}.")
            return
        queued_food = sum(UNIT_STATS[item]["food"] for p in self.entities for item in p.train_queue if item in UNIT_STATS)
        if self.food_used + queued_food + stats["food"] > self.food_cap:
            self.message("Brak miejsca w populacji.")
            return
        if self.gold < stats["cost_gold"] or self.wood < stats["cost_wood"]:
            self.message("Za malo surowcow.")
            return
        self.gold -= stats["cost_gold"]
        self.wood -= stats["cost_wood"]
        producer = min(producers, key=lambda p: len(p.train_queue))
        producer.train_queue.append(kind)
        if len(producer.train_queue) == 1:
            producer.train_timer = self.queue_time(kind)
        self.message(f"Szkolenie: {kind}.")

    def start_build_mode(self, kind: str) -> None:
        workers = self.selected_workers()
        if not workers:
            self.message("Zaznacz Peasanta, aby budowac.")
            return
        stats = BUILDING_STATS[kind]
        missing = self.missing_requirements(stats["requires"])
        if missing:
            self.message(f"Brakuje: {', '.join(missing)}.")
            return
        if not self.can_afford(stats["cost_gold"], stats["cost_wood"]):
            self.message("Za malo surowcow na budynek.")
            return
        self.pending_building = kind
        self.message(f"Wybierz miejsce budowy: {kind}.")

    def place_pending_building(self, x: float, y: float) -> None:
        kind = self.pending_building
        if not kind:
            return
        workers = self.selected_workers()
        if not workers:
            self.message("Zaznacz Peasanta, aby budowac.")
            self.pending_building = None
            return
        stats = BUILDING_STATS[kind]
        missing = self.missing_requirements(stats["requires"])
        if missing:
            self.message(f"Brakuje: {', '.join(missing)}.")
            self.pending_building = None
            return
        if not self.can_afford(stats["cost_gold"], stats["cost_wood"]):
            self.message("Za malo surowcow na budynek.")
            self.pending_building = None
            return
        if not self.can_place_building(kind, x, y):
            self.message("Nie mozna tu budowac.")
            return
        builder = workers[0]
        self.gold -= stats["cost_gold"]
        self.wood -= stats["cost_wood"]
        building = self.make_construction(kind, PLAYER, x, y, builder)
        self.entities.append(building)
        builder.target = None
        builder.gather_target = None
        builder.target_x = x
        builder.target_y = y
        self.pending_building = None
        self.message(f"Rozpoczeto budowe: {kind}.")

    def try_upgrade_keep(self) -> None:
        halls = [e for e in self.entities if e.team == PLAYER and e.kind == "Town Hall" and e.alive and e.complete]
        if not halls:
            self.message("Potrzebujesz Town Hall.")
            return
        stats = BUILDING_STATS["Keep"]
        missing = self.missing_requirements(stats["requires"])
        if missing:
            self.message(f"Brakuje: {', '.join(missing)}.")
            return
        if not self.can_afford(stats["cost_gold"], stats["cost_wood"]):
            self.message("Za malo surowcow na Keep.")
            return
        hall = halls[0]
        if hall.train_queue:
            self.message("Town Hall jest zajety.")
            return
        self.gold -= stats["cost_gold"]
        self.wood -= stats["cost_wood"]
        hall.train_queue.append("UPGRADE_KEEP")
        hall.train_timer = self.queue_time("UPGRADE_KEEP")
        self.message("Ulepszanie Town Hall do Keep.")

    def try_research(self, upgrade: str) -> None:
        name = "Steel Weapons" if upgrade == "UPGRADE_STEEL" else "Plated Armor"
        if name in self.upgrades:
            self.message("To ulepszenie jest juz gotowe.")
            return
        smiths = [e for e in self.entities if e.team == PLAYER and e.kind == "Blacksmith" and e.alive and e.complete]
        if not smiths:
            self.message("Potrzebujesz Blacksmith.")
            return
        cost_gold, cost_wood = (150, 100) if upgrade == "UPGRADE_STEEL" else (140, 120)
        if not self.can_afford(cost_gold, cost_wood):
            self.message("Za malo surowcow na ulepszenie.")
            return
        smith = smiths[0]
        if smith.train_queue:
            self.message("Blacksmith jest zajety.")
            return
        self.gold -= cost_gold
        self.wood -= cost_wood
        smith.train_queue.append(upgrade)
        smith.train_timer = self.queue_time(upgrade)
        self.message(f"Badanie: {name}.")


def main() -> None:
    ArcaneFrontiers2D()
    arcade.run()


if __name__ == "__main__":
    main()
