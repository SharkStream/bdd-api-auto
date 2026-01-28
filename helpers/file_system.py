import os
from helpers.constants import REPORTS, WORKER_DIR, ALLURE_RESULTS_DIR
from utils.logger import log_info_emoji


def create_reports_structure():
    """
    Create the necessary directory structure for reports if they do not exist.
    """
    directories = [REPORTS, WORKER_DIR, ALLURE_RESULTS_DIR]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    if not hasattr(create_reports_structure, "_shown"):
        log_info_emoji("📁", f"Reports directory structure created")
        create_reports_structure._shown = True