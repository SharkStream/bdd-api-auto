import os
import re
from helpers.constants import RESOURCES
from utils.common import read_json_file
from utils.file_handle import get_abs_file_path

OPTIONAL_FIELD_PREFIX = "##"
OPTIONAL_LIST_FIELD_PREFIX = "##[]"
PRESENT_FIELD = "#present"
IGNORE_FIELD = "#ignore"
NULL_FIELD = "#null"
EMPTY_LIST_FIELD = "#[]"
STRING_FIELD = "#string"
NUMBER_FIELD = "#number"
BOOLEAN_FIELD = "#boolean"
OBJECT_FIELD = "#object"
ARRAY_FIELD = "#array"
NOTNULL_FIELD = "#notnull"
REGEX_FIELD = "#regex "

def validate_json_schema(response_data: dict, schema: dict) -> tuple[bool, str]:
    errors = []

    def _validate_field(response_value, schema_value, field_path=""):
        is_optional = False
        original_schema_value = schema_value

        if isinstance(schema_value, str) and schema_value.startswith(OPTIONAL_FIELD_PREFIX):
            is_optional = True
            schema_value = schema_value[len(OPTIONAL_FIELD_PREFIX):]
        
        if is_optional and response_value is None:
            return
        
        if schema_value == PRESENT_FIELD:
            if response_value is None:
                errors.append(f"Validation Error: Field '{field_path}' is missing but expected to be present.")
            return
        
        if schema_value == IGNORE_FIELD:
            return
        
        if not is_optional and response_value is None and schema_value != NULL_FIELD and not isinstance(schema_value, (list,dict)) and not isinstance(schema_value, str) and schema_value.startswith(EMPTY_LIST_FIELD):
            errors.append(f"Validation Error: Expected a value, but field '{field_path}' is missing.")
            return
        
        if isinstance(schema_value, str):
            if schema_value.startswith(EMPTY_LIST_FIELD):
                if not isinstance(response_value, list) or len(response_value) != 0:
                    errors.append(f"Validation Error at '{field_path}' expected an array, got {type(response_value).__name__}.")
                return

                schema_obj_name = original_schema_value.replace(OPTIONAL_LIST_FIELD_PREFIX, "").replace(EMPTY_LIST_FIELD, "").strip()

                if not schema_obj_name:
                    errors.append(f"Validation Error at '{field_path}': schema object name missing {OPTIONAL_LIST_FIELD_PREFIX} or {EMPTY_LIST_FIELD} token.definition is empty.")
                    return
                
                referenced_schema = schema.get(schema_obj_name)
                if referenced_schema is None:
                    errors.append(f"Validation Error at '{field_path}': schema definition for '{schema_obj_name}' not found.")
                    return
                
                for index, item in enumerate(response_value):
                    _validate_field(item, referenced_schema, f"{field_path}[{index}]")
                return
            
            elif schema_value == STRING_FIELD:
                if not isinstance(response_value, str):
                    errors.append(f"Validation Error at '{field_path}': expected string, got {type(response_value).__name__}.")
            elif schema_value == NUMBER_FIELD:
                if not isinstance(response_value, (int, float)):
                    errors.append(f"Validation Error at '{field_path}': expected number, got {type(response_value).__name__}.")
            elif schema_value == BOOLEAN_FIELD:
                if not isinstance(response_value, bool):
                    errors.append(f"Validation Error at '{field_path}': expected boolean, got {type(response_value).__name__}.")
            elif schema_value == OBJECT_FIELD:
                if not isinstance(response_value, dict):
                    errors.append(f"Validation Error at '{field_path}': expected object, got {type(response_value).__name__}.")
            elif schema_value == ARRAY_FIELD:
                if not isinstance(response_value, list):
                    errors.append(f"Validation Error at '{field_path}': expected array, got {type(response_value).__name__}.")
            elif schema_value == NOTNULL_FIELD:
                if response_value is None:
                    errors.append(f"Validation Error at '{field_path}': expected not null value.")
            elif schema_value == NULL_FIELD:
                if response_value is not None:
                    errors.append(f"Validation Error at '{field_path}': expected null value. got {type(response_value).__name__} with value '{response_value}'.")
            elif isinstance(schema_value, str) and schema_value.startswith(REGEX_FIELD):
                pattern = schema_value[len(REGEX_FIELD):]
                if not isinstance(response_value, str):
                    errors.append(f"Validation Error at '{field_path}': expected string to match regex '{pattern}', got {type(response_value).__name__}.")
                elif not re.match(pattern, response_value):
                    errors.append(f"Validation Error at '{field_path}': value '{response_value}' does not match regex '{pattern}'.")
            else:
                if response_value != schema_value:
                    errors.append(f"Validation Error at '{field_path}': expected value '{schema_value}', got '{response_value}'.")
        elif isinstance(schema_value, dict):
            if not isinstance(response_value, dict):
                errors.append(f"Validation Error at '{field_path}': expected object, got {type(response_value).__name__}.")
                return
            
            response_keys = set(response_value.keys())
            schema_keys = set(schema_value.keys())
            extra_keys = response_keys - schema_keys
            for key in extra_keys:
                pass
            for key, val in schema_value.items():
                _validate_field(response_value.get(key), val, f"{field_path}.{key}")
        elif isinstance(schema_value, list):
            if len(schema_value) == 1 and isinstance(schema_value[0], (dict, list, str)):
                item_schema = schema_value[0]
                if not isinstance(response_value, list):
                    errors.append(f"Validation Error at '{field_path}': expected array, got {type(response_value).__name__}.")
                    return
                for index, item in enumerate(response_value):
                    _validate_field(item, item_schema, f"{field_path}[{index}]")
            else:
                if not isinstance(response_value, list):
                    errors.append(f"Validation Error at '{field_path}': expected array, got {type(response_value).__name__}.")
                    return
                if len(response_value) != len(schema_value):
                    errors.append(f"Validation Error at '{field_path}': expected array of length {len(schema_value)}, got {len(response_value)}.")
                    return
                for index, (resp_item, schema_item) in enumerate(zip(response_value, schema_value)):
                    _validate_field(resp_item, schema_item, f"{field_path}[{index}]")
        else:
            if response_value != schema_value:
                errors.append(f"Validation Error at '{field_path}': expected value '{schema_value}', got '{response_value}'.")
    
    _validate_field(response_data, schema)
    if errors:
        return False, "\n".join(errors)
    return True, "Validation successful."


def get_schema_response(rsp_content: str, country: str) -> dict:
    item_nested = rsp_content.split(".")
    keys = item_nested[-1]
    filename = item_nested[0]
    file_path = get_abs_file_path(f"{filename}.json", os.path.join(RESOURCES, country))
    expected_json = read_json_file(file_path)
    for keys in item_nested[1:]:
        expected_json = expected_json.get(keys, {})
    return expected_json