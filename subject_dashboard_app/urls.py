from django.urls import include, path, re_path
from django.views.generic import RedirectView
from edc_dashboard.views import AdministrationView
from edc_protocol import Protocol
from edc_utils import paths_for_urlpatterns

from edc_subject_dashboard.views import SubjectDashboardView as BaseSubjectDashboardView


class SubjectDashboardView(BaseSubjectDashboardView):
    navbar_name = "edc_subject_dashboard"
    visit_model = "edc_visit_tracking.subjectvisit"


app_name = "subject_dashboard_app"

urlpatterns = [
    path("accounts/", include("edc_auth.urls_for_accounts", namespace="auth")),
    path("administration/", AdministrationView.as_view(), name="administration_url"),
    *paths_for_urlpatterns("edc_auth"),
    *paths_for_urlpatterns("edc_action_item"),
    *paths_for_urlpatterns("edc_consent"),
    *paths_for_urlpatterns("edc_adverse_event"),
    *paths_for_urlpatterns("edc_device"),
    *paths_for_urlpatterns("edc_dashboard"),
    *paths_for_urlpatterns("edc_label"),
    *paths_for_urlpatterns("edc_lab"),
    *paths_for_urlpatterns("edc_lab_dashboard"),
    *paths_for_urlpatterns("edc_dashboard"),
    *paths_for_urlpatterns("edc_subject_dashboard"),
    *paths_for_urlpatterns("edc_review_dashboard"),
    *paths_for_urlpatterns("edc_export"),
    *paths_for_urlpatterns("edc_data_manager"),
    *paths_for_urlpatterns("edc_visit_tracking"),
    *paths_for_urlpatterns("edc_protocol"),
    *paths_for_urlpatterns("edc_visit_schedule"),
    *SubjectDashboardView.urls(
        # namespace="subject_dashboard_app",
        label="subject_dashboard",
        identifier_pattern=Protocol().subject_identifier_pattern,
    ),
    path("i18n/", include("django.conf.urls.i18n")),
    re_path(".", RedirectView.as_view(url="/"), name="home_url"),
]
