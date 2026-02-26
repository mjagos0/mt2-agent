from dataclasses import dataclass
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"


@dataclass(frozen=True)
class Spell:
    name: str
    base_path: Path

    @property
    def level_1(self) -> Path:
        return self.base_path / f"{self.name}_1.png"

    @property
    def level_m(self) -> Path:
        return self.base_path / f"{self.name}_M.png"

    @property
    def level_g(self) -> Path:
        return self.base_path / f"{self.name}_G.png"

    @property
    def level_p(self) -> Path:
        return self.base_path / f"{self.name}_P.png"

    @property
    def all_levels(self) -> list[Path]:
        return [self.level_1, self.level_m, self.level_g, self.level_p]


# --- Warrior ---

@dataclass(frozen=True)
class BodyForceSpells:
    base_path: Path = ASSETS_DIR / "spells" / "warrior" / "body_force"

    @property
    def aura_of_sword(self) -> Spell:
        return Spell("aura_of_sword", self.base_path)

    @property
    def three_way_cut(self) -> Spell:
        return Spell("three_way_cut", self.base_path)

    @property
    def sword_spin(self) -> Spell:
        return Spell("sword_spin", self.base_path)

    @property
    def berserk(self) -> Spell:
        return Spell("berserk", self.base_path)

    @property
    def dash(self) -> Spell:
        return Spell("dash", self.base_path)

    @property
    def all(self) -> list[Spell]:
        return [self.aura_of_sword, self.three_way_cut, self.sword_spin, self.berserk, self.dash]


@dataclass(frozen=True)
class MentalFightSpells:
    base_path: Path = ASSETS_DIR / "spells" / "warrior" / "mental_fight"

    @property
    def strong_body(self) -> Spell:
        return Spell("strong_body", self.base_path)

    @property
    def spirit_strike(self) -> Spell:
        return Spell("spirit_strike", self.base_path)

    @property
    def stump(self) -> Spell:
        return Spell("stump", self.base_path)

    @property
    def bash(self) -> Spell:
        return Spell("bash", self.base_path)

    @property
    def sword_strike(self) -> Spell:
        return Spell("sword_strike", self.base_path)

    @property
    def all(self) -> list[Spell]:
        return [self.strong_body, self.spirit_strike, self.stump, self.bash, self.sword_strike]


@dataclass(frozen=True)
class WarriorSpells:
    body_force: BodyForceSpells = BodyForceSpells()
    mental_fight: MentalFightSpells = MentalFightSpells()

    @property
    def all(self) -> list[Spell]:
        return self.body_force.all + self.mental_fight.all


# --- Shaman ---

@dataclass(frozen=True)
class DragonForceSpells:
    base_path: Path = ASSETS_DIR / "spells" / "shaman" / "dragon_force"

    @property
    def dragons_strength(self) -> Spell:
        return Spell("dragons_strength", self.base_path)

    @property
    def blessing(self) -> Spell:
        return Spell("blessing", self.base_path)

    @property
    def reflect(self) -> Spell:
        return Spell("reflect", self.base_path)

    @property
    def dragon_roar(self) -> Spell:
        return Spell("dragon_roar", self.base_path)

    @property
    def shooting_dragon(self) -> Spell:
        return Spell("shooting_dragon", self.base_path)

    @property
    def flying_talisman(self) -> Spell:
        return Spell("flying_talisman", self.base_path)

    @property
    def all(self) -> list[Spell]:
        return [self.dragons_strength, self.blessing, self.reflect, self.dragon_roar, self.shooting_dragon, self.flying_talisman]


@dataclass(frozen=True)
class HealingForceSpells:
    base_path: Path = ASSETS_DIR / "spells" / "shaman" / "healing_force"

    @property
    def swiftness(self) -> Spell:
        return Spell("swiftness", self.base_path)

    @property
    def attack_up(self) -> Spell:
        return Spell("attack_up", self.base_path)

    @property
    def cure(self) -> Spell:
        return Spell("cure", self.base_path)

    @property
    def lightning_throw(self) -> Spell:
        return Spell("lightning_throw", self.base_path)

    @property
    def lightning_claw(self) -> Spell:
        return Spell("lightning_claw", self.base_path)

    @property
    def summon_lightning(self) -> Spell:
        return Spell("summon_lightning", self.base_path)

    @property
    def all(self) -> list[Spell]:
        return [self.swiftness, self.attack_up, self.cure, self.lightning_throw, self.lightning_claw, self.summon_lightning]


@dataclass(frozen=True)
class ShamanSpells:
    dragon_force: DragonForceSpells = DragonForceSpells()
    healing_force: HealingForceSpells = HealingForceSpells()

    @property
    def all(self) -> list[Spell]:
        return self.dragon_force.all + self.healing_force.all


# --- Sura ---

@dataclass(frozen=True)
class WeaponrySpells:
    base_path: Path = ASSETS_DIR / "spells" / "sura" / "weaponry"

    @property
    def finger_strike(self) -> Spell:
        return Spell("finger_strike", self.base_path)

    @property
    def enchanted_blade(self) -> Spell:
        return Spell("enchanted_blade", self.base_path)

    @property
    def enchanted_armour(self) -> Spell:
        return Spell("enchanted_armour", self.base_path)

    @property
    def dragon_swirl(self) -> Spell:
        return Spell("dragon_swirl", self.base_path)

    @property
    def fear(self) -> Spell:
        return Spell("fear", self.base_path)

    @property
    def dispel(self) -> Spell:
        return Spell("dispel", self.base_path)

    @property
    def all(self) -> list[Spell]:
        return [self.finger_strike, self.enchanted_blade, self.enchanted_armour, self.dragon_swirl, self.fear, self.dispel]


@dataclass(frozen=True)
class BlackMagicSpells:
    base_path: Path = ASSETS_DIR / "spells" / "sura" / "black_magic"

    @property
    def dark_strike(self) -> Spell:
        return Spell("dark_strike", self.base_path)

    @property
    def flame_spirit(self) -> Spell:
        return Spell("flame_spirit", self.base_path)

    @property
    def spirit_strike(self) -> Spell:
        return Spell("spirit_strike", self.base_path)

    @property
    def flame_strike(self) -> Spell:
        return Spell("flame_strike", self.base_path)

    @property
    def dark_protection(self) -> Spell:
        return Spell("dark_protection", self.base_path)

    @property
    def dark_orb(self) -> Spell:
        return Spell("dark_orb", self.base_path)

    @property
    def all(self) -> list[Spell]:
        return [self.dark_strike, self.flame_spirit, self.spirit_strike, self.flame_strike, self.dark_protection, self.dark_orb]


@dataclass(frozen=True)
class SuraSpells:
    weaponry: WeaponrySpells = WeaponrySpells()
    black_magic: BlackMagicSpells = BlackMagicSpells()

    @property
    def all(self) -> list[Spell]:
        return self.weaponry.all + self.black_magic.all


# --- Ninja ---

@dataclass(frozen=True)
class ArcherySpells:
    base_path: Path = ASSETS_DIR / "spells" / "ninja" / "archery"

    @property
    def repetitive_shot(self) -> Spell:
        return Spell("repetitive_shot", self.base_path)

    @property
    def fire_arrow(self) -> Spell:
        return Spell("fire_arrow", self.base_path)

    @property
    def poison_arrow(self) -> Spell:
        return Spell("poison_arrow", self.base_path)

    @property
    def arrow_shower(self) -> Spell:
        return Spell("arrow_shower", self.base_path)

    @property
    def feather_walk(self) -> Spell:
        return Spell("feather_walk", self.base_path)

    @property
    def all(self) -> list[Spell]:
        return [self.repetitive_shot, self.fire_arrow, self.poison_arrow, self.arrow_shower, self.feather_walk]


@dataclass(frozen=True)
class BladeFightSpells:
    base_path: Path = ASSETS_DIR / "spells" / "ninja" / "blade_fight"

    @property
    def ambush(self) -> Spell:
        return Spell("ambush", self.base_path)

    @property
    def rolling_dagger(self) -> Spell:
        return Spell("rolling_dagger", self.base_path)

    @property
    def poisonous_cloud(self) -> Spell:
        return Spell("poisonous_cloud", self.base_path)

    @property
    def fast_attack(self) -> Spell:
        return Spell("fast_attack", self.base_path)

    @property
    def stealth(self) -> Spell:
        return Spell("stealth", self.base_path)

    @property
    def all(self) -> list[Spell]:
        return [self.ambush, self.rolling_dagger, self.poisonous_cloud, self.fast_attack, self.stealth]


@dataclass(frozen=True)
class NinjaSpells:
    archery: ArcherySpells = ArcherySpells()
    blade_fight: BladeFightSpells = BladeFightSpells()

    @property
    def all(self) -> list[Spell]:
        return self.archery.all + self.blade_fight.all


# --- Top-level ---

@dataclass(frozen=True)
class GameIcons:
    warrior: WarriorSpells = WarriorSpells()
    shaman: ShamanSpells = ShamanSpells()
    sura: SuraSpells = SuraSpells()
    ninja: NinjaSpells = NinjaSpells()

    @property
    def all(self) -> list[Spell]:
        return self.warrior.all + self.shaman.all + self.sura.all + self.ninja.all