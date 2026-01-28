import os.path
from utils.common import read_json_file
from utils.str_handle import wrap_namespace

PRO_DIR = os.getcwd()

RESOURCES = os.path.join(PRO_DIR, 'resources')
CONFIG_YAML = os.path.join(RESOURCES, 'config.yaml')

REPORTS = os.path.join(PRO_DIR, 'reports')
WORKER_DIR = os.path.join(REPORTS, 'workers')
ALLURE_RESULTS_DIR = os.path.join(REPORTS, 'allure-results')


# Env Config
ENV_CONFIG_JSON = wrap_namespace(read_json_file(os.path.join(RESOURCES, "generic", 'env.json')))
ENDPOINTS_CONFIG_JSON = wrap_namespace(read_json_file(os.path.join(RESOURCES, "generic", 'endpoints.json')))
USERS_CONFIG_JSON = wrap_namespace(read_json_file(os.path.join(RESOURCES, "generic", 'login.json')))