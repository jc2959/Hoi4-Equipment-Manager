from typing import Dict, Type, List


class Hoi4Data(object):
    """
    Decorator for Hoi4Loadables so that they can be injected
    with relevant info if needed
    """
    def __init__(self, arg=None):
        # Allows decorator to be initialised without arguments
        self.has_args = arg is not None
        if not self.has_args:
            return

        self._header = arg["header"] if "header" in arg.keys() else ""
        """ The header for its JSON file """
        self._child_types = arg["child types"] if "child types" in arg.keys() else []
        """ The child Hoi4Loadable classes """
        self._subtypes = arg["subtypes"] if "subtypes" in arg.keys() else []
        """ The subtypes of the Hoi4Loadable """

    def __call__(self, *args, **kwargs):
        self._arg: Hoi4Loadable = args[0]

        if self.has_args:
            self._arg.header = self._header
            self._arg.child_types = self._child_types
            self._arg.subtypes = self._subtypes

        return self._arg


@Hoi4Data()
class Hoi4Loadable:
    """
    Loadable Hoi4 Data
    """

    def __init__(self, json_obj: Dict = None):
        # Decorator Variables
        self.header: str = self.header
        """ The header of the json file """
        self.child_types: List[Type[Hoi4Loadable]] = self.child_types
        """ The child Hoi4 Loadables that this instance has fields for """
        self.subtypes: List[str] = self.subtypes
        """ The subtypes of the HOI4 Loadable """

        self.load_details(json_obj)

    def load_details(self, json_obj: Dict):
        """ Loads the fields of the Hoi4 Loadable from a Json object """

        if not json_obj:
            return

        # Iterates through each field of the object and if there is a
        # corresponding key in the Json object, it then sets the field
        # to the corresponding value
        for property_name, _ in vars(self).items():
            if property_name in json_obj.keys():
                property_value = json_obj[property_name]

                # If the Json value is a dict (possible nested Json) then
                # check if there is a Hoi4 Loadable in the current instance's
                # subtypes that can be loaded from it
                if isinstance(property_value, dict):
                    for child_value in self.child_types:
                        if property_name in child_value.subtypes:
                            property_value = child_value(property_value)

                setattr(self, property_name, property_value)
