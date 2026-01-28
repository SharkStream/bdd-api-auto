from types import SimpleNamespace
from utils.client import HTTPClient, ClientConfig
from helpers.constants import REPORTS, ENV_CONFIG_JSON, ENDPOINTS_CONFIG_JSON, USERS_CONFIG_JSON


config = ClientConfig(
    base_url=None,
    timeout=30,
    rate_limit_delay=0.5,  # 500ms delay between requests
    max_retries=3,
    verify_ssl=False
)


def before_all(context):
    context.ENV = context.config.userdata.get("env", "sit")
    context.COUNTRY = context.config.userdata.get("country", "cn")
    context.RESOURCES = REPORTS
    context.URLS = getattr(ENV_CONFIG_JSON, context.ENV)
    context.USERS = getattr(USERS_CONFIG_JSON, context.COUNTRY)
    context.ENDPOINTS = getattr(ENDPOINTS_CONFIG_JSON, "endpoints")
    context.CONTEXT = getattr(ENDPOINTS_CONFIG_JSON, "context")
    context.BASE_URL = context.URLS.BASE_URL
    config.base_url = context.BASE_URL
    context.client = HTTPClient(config)
    context.store = {}


def after_all(context):
    pass

def before_feature(context, feature):
    context.feature.store = {}


def before_scenario(context, scenario):
    context.kwargs = {}
    context.response = None
    context.request = SimpleNamespace()
    context.upload_file = None
    context.scenario.store = {}


def after_scenario(context, scenario):
    if context.upload_file:
        context.upload_file.close()


def after_step(context, step):
    pass
