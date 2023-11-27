"""
Interface for the Hoi4 objects
"""

import inspect
from queue import Queue
from typing import Type, Dict, List

import data_loader
import hoi4loadabletypes
from hoi4loadable import Hoi4Loadable, Hoi4Relationship


_hoi4_data: Dict[Type[Hoi4Loadable], Dict[str, Hoi4Loadable]] = {}
"""
A dictionary store of the Hoi4 data loaded in the data\n
The parent dictionary is indexed by the type of Hoi4Loadable\n
The child dictionary is indexed by the individual names of each instance of said type
"""

_relationship_list: List[Hoi4Relationship] = []
""" The list of relationships that exist between the loaded Hoi4 Data """

_relationship_dict: Dict[Hoi4Loadable, Dict[str, List[int]]] = {}
"""
A dictionary that keeps track of the relationships each Hoi4 Entity is a child of\n
The parent dictionary is indexed by the instance of Hoi4Loadable\n
The child dictionary is indexed by the field on the parent entity that the relationship acts on
"""

_hoi4_data_queue: Queue = Queue()
"""
A queue of Hoi4Loadables that are either added by a source that is not directly the data_loader
or are those that need to be loaded after the others
"""
_relationship_queue: Queue = Queue()
"""
A queue of the Hoi4 relationships so that they can be loaded after all of the Hoi4Loadables
are loaded
"""


def load_all(path_to_hoi4_data: str):
    """
    Loads all of the Hoi4 data from the hoi4 files that can be loaded into
    Hoi4Loadables defined in hoi4.data.hoi4loadabletypes

    :param path_to_hoi4_data: The path to the Hoi4 data files (of the format
                              "steam\\steamapps\\common\\Hearts of Iron IV\\common")
    """
    # Iterates through each class in hoi4.data.hoi4loadabletypes that is a subclass of
    # Hoi4Loadables, to load the respective files into the system
    for name, obj in inspect.getmembers(hoi4loadabletypes):
        if inspect.isclass(obj) and name != "Hoi4Loadable" and issubclass(obj, Hoi4Loadable):
            loadable: Hoi4Loadable = obj()

            if loadable.is_loadable:
                _hoi4_data[obj] = data_loader.load_all_data(path_to_hoi4_data, obj)

    # Loads all of the queued data
    add_queued_hoi4_data()
    establish_relationships()


def add_queued_hoi4_data():
    """
    Loads all of the queued data into the Hoi4 data dictionary
    """
    while not _hoi4_data_queue.empty():
        data_type, name, data = _hoi4_data_queue.get()
        _hoi4_data[data_type][name] = data


def queue_add_hoi4_data(data_type: Type[Hoi4Loadable], name: str, data: Hoi4Loadable):
    """
    Adds a Hoi4Loadable entity into the _hoi4_data_queue

    :param data_type: The type of the Hoi4Loadable
    :param name: The name of the Hoi4Loadable instance
    :param data: The Hoi4Loadable instance
    """
    _hoi4_data_queue.put(item=(data_type, name, data))


def get_hoi4_data(data_type: Type[Hoi4Loadable]) -> Dict[str, Hoi4Loadable]:
    """
    :param data_type: The type of Hoi4Loadable being retrieved
    :return: A dictionary of Hoi4Loadables of the type given, indexed by name
    """
    return _hoi4_data[data_type]


def get_hoi4_instance(data_type: Type[Hoi4Loadable], name: str):
    """
    :param data_type: The type of the Hoi4Loadable being retrieved
    :param name: The name of the Hoi4Loadable being retrieved
    :return: The Hoi4Loadable with the type and name provided
    """
    return _hoi4_data[data_type][name]


def get_all_data() -> Dict[Type[Hoi4Loadable], Dict[str, Hoi4Loadable]]:
    """
    :return: A copy of the currently loaded Hoi4 Data
    """
    return _hoi4_data.copy()


def queue_relationship(relationship: Hoi4Relationship):
    """
    Queues a relationship to be loaded

    :param relationship: The relationship being loaded
    """
    _relationship_queue.put(relationship)


def establish_relationships():
    """
    Loads all of the relationships in the relationship queue
    """
    while not _relationship_queue.empty():
        relationship: Hoi4Relationship = _relationship_queue.get()

        relationship.establish_relationship(_hoi4_data[relationship.data_type])

        index = len(_relationship_list)

        _relationship_list.append(relationship)

        for hoi4_obj in relationship.entities_to:
            _add_relationship_entity_to_dict(hoi4_obj, relationship.field, index)


def _add_relationship_entity_to_dict(hoi4_obj: Hoi4Loadable, field: str, index: int):
    """
    Creates an indexing of the Hoi4Loadable given to retrieve a relationship

    :param hoi4_obj: The Hoi4Loadable being indexed
    :param field: The field the relationship acts on
    :param index: The index of the relationship within the relationship list
    """
    if hoi4_obj not in _relationship_dict:
        _relationship_dict[hoi4_obj] = {}

    if field not in _relationship_dict[hoi4_obj].keys():
        _relationship_dict[hoi4_obj][field] = []

    _relationship_dict[hoi4_obj][field].append(index)


def get_relationships_from_field_child(hoi4_obj: Hoi4Loadable, field: str) \
        -> List[Hoi4Relationship]:
    """
    Retrieves the relationships the Hoi4Loadable is a child of, that acts on a certain field

    :param hoi4_obj: The child Hoi4Loadable
    :param field: The field the relationship acts on

    :raises KeyError: If there are no relationships that act on the field, that the Hoi4Loadable
                      is a child of
    """
    relationship_indices = _relationship_dict[hoi4_obj][field]

    relationships: List[Hoi4Relationship] = []

    for relationship_index in relationship_indices:
        relationship = _relationship_list[relationship_index]

        if hoi4_obj in relationship.entities_to:
            relationships.append(_relationship_list[relationship_index])

    if len(relationships) == 0:
        raise KeyError(f"There is no relationship on the field {field} "
                       f"in which {hoi4_obj.name} is a child")

    return relationships
