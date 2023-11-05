from typing import Dict, Type, List, Tuple, Union
import inspect

from hoi4 import hoi4interface


class Hoi4Data(object):
    """
    Decorator for Hoi4Loadables so that they can be injected
    with relevant info if needed
    """
    def __init__(self, arg={}):
        # Allows decorator to be initialised without arguments

        self._allowed_headers = arg["headers"] if "headers" in arg.keys() else []
        """ The header for its JSON file """
        self._child_types = arg["child types"] if "child types" in arg.keys() else []
        """ The child Hoi4Loadable classes """
        self._subtypes = arg["subtypes"] if "subtypes" in arg.keys() else []
        """ The subtypes of the Hoi4Loadable """
        self._is_loadable = arg["is loadable"] if "is loadable" in arg.keys() else False
        """ Whether the obj can be loaded from a file """
        self._relationships = arg["relationships"] if "relationships" in arg.keys() else {}
        """ The relationships the data has, indexed by its field name """

    def __call__(self, *args, **kwargs):
        self._arg: Hoi4Loadable = args[0]

        self._arg.allowed_headers = self._allowed_headers
        self._arg.child_types = self._child_types
        self._arg.subtypes = self._subtypes
        self._arg.is_loadable = self._is_loadable
        self._arg.relationships = self._relationships

        return self._arg


@Hoi4Data()
class Hoi4Loadable:
    """
    Loadable Hoi4 Data
    """

    def __init__(self, name: str = "", json_obj: Dict = None):
        # Decorator Variables
        self.allowed_headers: List[str] = self.allowed_headers
        """ The header of the json file """
        self.child_types: List[Type[Hoi4Loadable]] = self.child_types
        """ The child Hoi4 Loadables that this instance has fields for """
        self.subtypes: List[str] = self.subtypes
        """ The subtypes of the HOI4 Loadable """
        self.is_loadable: bool = self.is_loadable
        """ The whether the obj can be loaded from a file """
        self.relationships: Dict[str, Type[Hoi4Loadable]] = self.relationships

        self.name = name

        self.load_details(json_obj)

    def load_details(self, json_obj: Dict):
        """ Loads the fields of the Hoi4 Loadable from a Json object """

        if not json_obj:
            return

        # Iterates through each field of the object and if there is a
        # corresponding key in the Json object, it then sets the field
        # to the corresponding value
        for property_name, _ in vars(self).items():
            if property_name in self.relationships.keys():
                if property_name in json_obj.keys():
                    setattr(self, property_name, Hoi4Relationship(self, property_name, json_obj[property_name]))
            elif property_name not in vars(Hoi4Loadable()).keys() and property_name in json_obj.keys():
                property_value = json_obj[property_name]

                # If the Json value is a dict (possible nested Json) then
                # check if there is a Hoi4 Loadable in the current instance's
                # subtypes that can be loaded from it
                if isinstance(property_value, dict):
                    for child_value in self.child_types:
                        if property_name in child_value.subtypes:
                            property_value = child_value(property_value)

                setattr(self, property_name, property_value)


class Hoi4Relationship:
    def __init__(self, entity_from: Hoi4Loadable, field: str, loading_data: Union[Dict, str]):
        self.members: List[Tuple[Hoi4Loadable, int]] = []

        self.field = field

        self.entity_from: Hoi4Loadable = entity_from
        self.entities_to: List[Hoi4Loadable] = []

        self.data_type: Type[Hoi4Loadable] = entity_from.relationships[field]

        if isinstance(loading_data, dict):
            self.json_obj: Dict[str, int] = loading_data
        else:
            self.json_obj: Dict[str, int] = {loading_data: 0}

        hoi4interface.queue_relationship(self)

    def establish_relationship(self, data: Dict[str, Hoi4Loadable]):
        for key, value in self.json_obj.items():
            hoi4_obj = data[key]
            self.entities_to.append(hoi4_obj)

            self.members.append((hoi4_obj, value))
