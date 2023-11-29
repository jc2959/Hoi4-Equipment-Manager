from typing import Optional

from hoi4.hoi4loadable import Hoi4Data, Hoi4Loadable, Hoi4Relationship, Hoi4RelationshipType


@Hoi4Data({
    "subtypes": ["forest", "jungle"]
})
class Environment(Hoi4Loadable):
    attack: float = 0
    movement: float = 0

    def __init__(self, json_obj: dict = None):
        Hoi4Loadable.__init__(self, "", json_obj)


@Hoi4Data({
    "headers": ["resources"],
    "is loadable": True
})
class Resources(Hoi4Loadable):
    def __init__(self, name: str = "", json_obj: dict = None):
        Hoi4Loadable.__init__(self, name=name, json_obj=json_obj)


@Hoi4Data({
    "headers": ["equipments", "duplicate_archetypes"],
    "is loadable": True,
    "relationships": {
        "resources": Resources
    }
})
class Units_Equipment(Hoi4Loadable):
    year: int = 1918

    archetype: Hoi4Relationship = None

    is_archetype: bool = False
    is_buildable: bool = False

    type: str = ""

    active: bool = False

    # Misc Abilities
    reliability: float = 0.9
    maximum_speed: float = 4

    # Defensive Abilities
    defense: float = 20
    breakthrough: float = 2
    hardness: float = 0
    armor_value: float = 0

    # Offensive Abilities
    soft_attack: float = 3
    hard_attack: float = 0.5
    ap_attack: float = 1
    air_attack: float = 0

    # Space taken in convoy
    lend_lease_cost: float = 1

    build_cost_ic: float = 0.43
    resources: Hoi4Relationship = None

    def __init__(self, name: str = "", json_obj: dict = None):
        self.relationships["archetype"] = Units_Equipment

        self.archetype = Hoi4Relationship(Hoi4RelationshipType.ONE_TO_MANY, self, "archetype")
        self.resources = Hoi4Relationship(Hoi4RelationshipType.MANY_TO_MANY, self, "resources")

        Hoi4Loadable.__init__(self, name, json_obj)


@Hoi4Data({
    "headers": ["sub_units"],
    "child types": [Environment],
    "is loadable": True,
    "relationships": {
        "need": Units_Equipment,
        "need_equipment": Units_Equipment
    }
})
class Units(Hoi4Loadable):
    abbreviation: str = ""
    forest: Environment = Environment()
    jungle: Environment = Environment()
    max_strength: float = 0
    max_organisation: float = 0
    default_morale: float = 0
    manpower: float = 0
    need: Hoi4Relationship = None
    need_equipment: Hoi4Relationship = None

    def __init__(self, name: str = "", json_obj: dict = None):
        self.need = Hoi4Relationship(Hoi4RelationshipType.MANY_TO_MANY, self, "need")
        self.need_equipment = Hoi4Relationship(Hoi4RelationshipType.ONE_TO_MANY, self, "need_equipment")

        Hoi4Loadable.__init__(self, name, json_obj)
