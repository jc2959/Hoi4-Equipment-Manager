import os
from json.decoder import JSONDecodeError
from re import Match, sub as re_sub
import json
from typing import Callable, Dict, Type

from hoi4_data.hoi4loadable import Hoi4Loadable


def convert_to_json(file_contents: str) -> Dict:
    """
    Converts a Hoi4 formatted file's contents to a Json Object

    :param file_contents: The file contents of a Hoi4 formatted file
    :return: A Json Object that contains the same information as the input file's contents
    """

    json_obj = {}

    # Applies regex to reformat the file's contents
    json_str = apply_json_regex(file_contents)

    try:
        json_obj = json.loads(json_str)
    except JSONDecodeError:
        print("COULD NOT LOAD FOLLOWING")
        print(json_str)

    return json_obj


def apply_json_regex(hoi4_formatted_str: str) -> str:
    """
    Re-formats a Hoi4 file's contents into Json format

    :param hoi4_formatted_str: The raw contents of a Hoi4 file
    :return: A Json string containing exactly the same information as the input
    """
    # Regex patterns
    comments_regex_pattern = "(#[^\n]*)\n"
    attribute_regex_pattern = "((?:[^\"{}\\s=\\d])+|[^\\d\\s\\.][^\"{}\\s=]+)[\" \"\\n}]"
    newline_regex_pattern = "[^\\s][^{\\n]*(\\n)"
    lists_regex_pattern = "{[^{}=]+}"
    list_elements_regex_pattern = "\"[\\s]+\""
    lst_element_regex_pattern = ",\\s*[]}]"
    bad_commas_regex_pattern = "[{[][\\s]*,"

    # Replacement functions
    comments_rep_func: Callable[[Match], str] = lambda match: ""
    attr_rep_func: Callable[[Match], str] = lambda match: \
        match.group().replace(match.group(1), "\"" + match.group(1) + "\"")
    newline_rep_func: Callable[[Match], str] = lambda match: match.group().replace("\n", ",")
    lists_rep_func: Callable[[Match], str] = lambda match: match.group().replace("{", "[").replace("}", "]")
    list_elements_rep_func: Callable[[Match], str] = lambda match: match.group().replace("\" ", "\",")
    lst_element_rep_func: Callable[[Match], str] = lambda match: match.group().replace(",", "")

    new_file_contents = hoi4_formatted_str
    new_file_contents = "{\n" + new_file_contents + "\n}"

    # Applies the replacement functions where the regex patterns are found
    new_file_contents = re_sub(comments_regex_pattern, comments_rep_func, new_file_contents)
    new_file_contents = re_sub(attribute_regex_pattern, attr_rep_func, new_file_contents)
    new_file_contents = re_sub(newline_regex_pattern, newline_rep_func, new_file_contents)
    new_file_contents = re_sub(lists_regex_pattern, lists_rep_func, new_file_contents)
    new_file_contents = re_sub(list_elements_regex_pattern, list_elements_rep_func, new_file_contents)
    new_file_contents = re_sub(lst_element_regex_pattern, lst_element_rep_func, new_file_contents)
    new_file_contents = re_sub(bad_commas_regex_pattern, lst_element_rep_func, new_file_contents)

    # Removes any bad double quotes
    new_file_contents = new_file_contents.replace("\"\"", "\"")

    new_file_contents = new_file_contents.replace("=", ":")

    return new_file_contents


def load_all_data(path_to_hoi4_files: str, hoi4loadable_type: Type) -> Dict[str, Hoi4Loadable]:
    """
    Loads all of the Hoi4 Loadables of a certain type

    :param path_to_hoi4_files: The path to the Hoi4 files
                                (of the format "steam\\steamapps\\common\\Hearts of Iron IV\\common")
    :param hoi4loadable_type: The type of Hoi4 Loadables to load
    :return: A dictionary of the Hoi4 Loadables indexed by name
    """
    types_parent_dir = hoi4loadable_type.__name__.lower().replace("-", "\\")

    data_instance: Hoi4Loadable = hoi4loadable_type({})
    header = data_instance.header

    last_dir = types_parent_dir.split("\\")[-1]

    all_paths = []

    for roots, dirs, files in os.walk(path_to_hoi4_files):
        if roots.split("\\")[-1] == last_dir:
            if types_parent_dir in roots:
                all_paths.extend([f"{roots}\\{name}" for name in files])
                break

    return_data: Dict[str, Hoi4Loadable] = {}

    for real_path in all_paths:
        file_content = "\n".join(open(real_path, 'r').readlines())

        json_obj = convert_to_json(file_content)

        if json_obj == {}:
            continue

        for key, value in json_obj[header].items():
            return_data[key] = hoi4loadable_type(value)

    return return_data
