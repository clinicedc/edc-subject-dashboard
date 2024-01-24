#!/usr/bin/env python
import logging
from pathlib import Path

from edc_constants.constants import IGNORE
from edc_test_utils import DefaultTestSettings, func_main
from edc_test_utils.default_installed_apps import DEFAULT_EDC_INSTALLED_APPS

app_name = "edc_subject_dashboard"
base_dir = Path(__file__).absolute().parent

project_settings = DefaultTestSettings(
    calling_file=__file__,
    BASE_DIR=base_dir,
    APP_NAME=app_name,
    ETC_DIR=str(base_dir / "edc_subject_dashboard" / "tests" / "etc"),
    SUBJECT_VISIT_MODEL="edc_visit_tracking.subjectvisit",
    EDC_AUTH_SKIP_SITE_AUTHS=True,
    EDC_AUTH_SKIP_AUTH_UPDATER=True,
    EDC_SITES_REGISTER_DEFAULT=False,
    EDC_NAVBAR_VERIFY_ON_LOAD=IGNORE,
    add_dashboard_middleware=True,
    add_lab_dashboard_middleware=True,
    ROOT_URLCONF="subject_dashboard_app.urls",
    INSTALLED_APPS=[
        *DEFAULT_EDC_INSTALLED_APPS,
        "subject_dashboard_app.apps.AppConfig",
    ],
).settings


def main():
    func_main(project_settings, *[f"{app_name}.tests"])


if __name__ == "__main__":
    logging.basicConfig()
    main()
