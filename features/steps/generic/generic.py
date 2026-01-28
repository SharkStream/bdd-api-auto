import re
import json
import parse
from behave import *
from utils.schema_validation import validate_json_schema, get_schema_response
from utils.str_handle import get_keys_value, value_handler, resolve_data, get_context_value_by_key
from utils.file_handle import get_abs_file_path
from utils.decorator import resolve_vars


@parse.with_pattern(r".+")
def parse_any(text):
    return text

use_step_matcher("cfparse")
register_type(Any=parse_any)
register_type(Str=str)

position_pattern = re.compile(r"\$\{(.*?)\}")
ids_pattern = re.compile(r"\$\{(.*?)\}")

@Given('headers "{headers}"')
def step_headers(context, headers):
    headers = json.loads(headers)
    context.client.session.headers.update(headers)

@Given('params "{params}"')
def step_params(context, params):
    setattr(context.request, "params", json.loads(params))

@Given('request "{payload}"')
def step_request_payload(context, payload):
    setattr(context.request, "data", json.loads(payload))

@Given('json "{json}"')
def step_json_payload(context, json):
    setattr(context.request, "json", json.loads(json))

@Given('multipart file "{filepath}"')
@resolve_vars
def step_multipart_file(context, filepath):
    file_path = get_abs_file_path(filepath)
    context.upload_file = open(file_path, "rb")
    setattr(context.request, "files", {"file": context.upload_file})

@When('method "{method}"')
def step_request_method(context, method):
    context.request.method = method.upper()
    request = resolve_data(context, context.request.__dict__)
    context.request = request
    context.response = context.client.request(**request)

@Then('status "{status:d}"')
def step_response_status(context, status):
    assert context.response.status_code == status, (
        f"Expected status {status}, got {context.response.status_code}"
        f"URL: {context.request.url}, Response: {context.response.text}"
    )

@Then('match response == "{response}"')
def step_match_response(context, response):
    expected_response = get_schema_response(response, context.COUNTRY)
    status, err_msg = validate_json_schema(context.response.json(), expected_response)
    assert status == True, err_msg

use_step_matcher("re")
@Then(r'(?:(?P<scope>\w+)\s)?set\s+"(?P<arg>[^"]+)"\s*=\s*"(?P<value>[^"]+)"')
def step_set_variable(context, scope, arg, value):
    value = value.strip()
    actual_value = None
    if value.startswith("$."):
        actual_value = get_keys_value(value.replace("$.", ""), context.response.json())
    elif value.startswith("$"):
        actual_value = get_context_value_by_key(context, value)
    else:
        actual_value = value
    if scope == "global":
        context.store[arg] = actual_value
    elif scope == "feature":
        context.feature.store[arg] = actual_value
    else:
        context.scenario.store[arg] = actual_value

@Given(r'url\s+"(?P<endpoint>[^"]+)"(?:\s*\+\s*(?P<value>.+))?')
def step_set_url(context, endpoint, value=None):
    endpoint_value = [getattr(context.ENDPOINTS, endpoint, endpoint)]
    if value is None:
        context.request.endpoint = "/".join(endpoint_value)
        return
    value = value.replace("\"", "").replace("'", "").strip()
    if "+" in value:
        parts = [part.strip() for part in value.split("+")]
        values = [value_handler(value, context) for value in parts]
        endpoint_value.extend(values)
    elif value is not None:
        resolved_value = value_handler(value.strip(), context)
        endpoint_value.append(resolved_value)
    context.request.endpoint = "/".join(endpoint_value)