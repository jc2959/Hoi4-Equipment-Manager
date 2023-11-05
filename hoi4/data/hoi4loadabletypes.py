from hoi4.data.hoi4loadable import Hoi4Data, Hoi4Loadable, Hoi4Relationship


@Hoi4Data({
    "subtypes": ["forest", "jungle"]
})
class Environment(Hoi4Loadable):
    def __init__(self,  json_obj: dict = None):
        self.attack = 0
        self.movement = 0
        Hoi4Loadable.__init__(self, "", json_obj)


@Hoi4Data({
    "headers": ["equipments", "duplicate_archetypes"],
    "is loadable": True,
})
class Units_Equipment(Hoi4Loadable):
    def __init__(self, name: str = "", json_obj: dict = None):
        self.relationships["archetype"] = Units_Equipment

        self.year = 1918

        self.archetype: Hoi4Relationship = None

        self.is_archetype = False
        self.is_buildable = False

        self.type = ""

        self.active = False

        # Misc Abilities
        self.reliability = 0.9
        self.maximum_speed = 4

        # Defensive Abilities
        self.defense = 20
        self.breakthrough = 2
        self.hardness = 0
        self.armor_value = 0

        # Offensive Abilities
        self.soft_attack = 3
        self.hard_attack = 0.5
        self.ap_attack = 1
        self.air_attack = 0

        # Space taken in convoy
        self.lend_lease_cost = 1

        self.build_cost_ic = 0.43
        self.resources = {}

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
    def __init__(self, name: str = "", json_obj: dict = None):
        self.abbreviation = ""
        self.forest = Environment()
        self.jungle = Environment()
        self.max_strength = 0
        self.max_organisation = 0
        self.default_morale = 0
        self.manpower = 0
        self.need: Hoi4Relationship = None
        self.need_equipment: Hoi4Relationship = None
        Hoi4Loadable.__init__(self, name, json_obj)
