from __future__ import annotations

from collections import namedtuple
from typing import TYPE_CHECKING, Type, TypeVar

from dateutil.relativedelta import relativedelta
from django import template
from django.apps import apps as django_apps
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from edc_appointment.constants import (
    CANCELLED_APPT,
    COMPLETE_APPT,
    IN_PROGRESS_APPT,
    INCOMPLETE_APPT,
    NEW_APPT,
    SKIPPED_APPT,
)
from edc_appointment.models import Appointment
from edc_appointment.utils import (
    get_appointment_model_cls,
    get_unscheduled_appointment_url,
)
from edc_dashboard.utils import get_bootstrap_version
from edc_metadata import KEYED, REQUIRED
from edc_metadata.metadata_helper import MetadataHelper
from edc_utils import get_utcnow

from ..view_utils import (
    AppointmentButton,
    CrfButton,
    GotToFormsButton,
    PrnButton,
    RelatedVisitButton,
    RequisitionButton,
    SubjectConsentButton,
    TimepointStatusButton,
    render_history_and_query_buttons,
)

if TYPE_CHECKING:
    from edc_consent.model_mixins import ConsentModelMixin
    from edc_metadata.models import CrfMetadata
    from edc_registration.models import RegisteredSubject
    from edc_visit_schedule.models import VisitSchedule as VisitScheduleModel
    from edc_visit_schedule.schedule import Schedule
    from edc_visit_schedule.visit_schedule import VisitSchedule
    from edc_visit_tracking.model_mixins import VisitModelMixin

    VisitModel = TypeVar("VisitModel", bound=VisitModelMixin)
    ConsentModel = TypeVar("ConsentModel", bound=ConsentModelMixin)

__all__ = [
    "appointment_in_progress",
    "render_appointment_status_icon",
    "print_requisition_popover",
    "render_prn_button",
    "render_appointment_button",
    "render_crf_button_group",
    "render_gotoforms_button",
    "requisition_panel_actions",
    "render_crf_totals",
    "render_subject_consent_button",
    "render_unscheduled_appointment_button",
]

register = template.Library()


class SubjectDashboardExtrasError(Exception):
    pass


@register.inclusion_tag(
    f"edc_subject_dashboard/bootstrap{get_bootstrap_version()}/appointment_in_progress.html"
)
def appointment_in_progress(
    subject_identifier: str = None,
    visit_schedule: VisitSchedule = None,
    schedule: Schedule = None,
) -> dict[str, str]:
    """Returns the context with the visit code of the appointment in
    progress.
    """
    try:
        appointment = get_appointment_model_cls().objects.get(
            subject_identifier=subject_identifier,
            visit_schedule_name=visit_schedule.name,
            schedule_name=schedule.name,
            appt_status=IN_PROGRESS_APPT,
        )
    except ObjectDoesNotExist:
        visit_code = None
    except MultipleObjectsReturned:
        qs = get_appointment_model_cls().objects.filter(
            subject_identifier=subject_identifier,
            visit_schedule_name=visit_schedule.name,
            schedule_name=schedule.name,
            appt_status=IN_PROGRESS_APPT,
        )
        visit_code = ", ".join([obj.visit_code for obj in qs])
    else:
        visit_code = appointment.visit_code
    return dict(visit_code=visit_code)


@register.inclusion_tag(
    f"edc_subject_dashboard/bootstrap{get_bootstrap_version()}/"
    f"requisition_panel_actions.html",
    takes_context=True,
)
def requisition_panel_actions(context, requisitions=None):
    try:
        requisition_metadata = requisitions[0]
    except IndexError:
        context["verify_disabled"] = None
    else:
        app_label, model_name = requisition_metadata.model.split(".")
        context["verify_disabled"] = (
            None
            if context["user"].has_perm(f"{app_label}.change_{model_name}")
            else "disabled"
        )
    appointment = context.get("appointment")
    scanning = context.get("scanning")
    autofocus = "autofocus" if scanning else ""
    context["appointment"] = str(appointment.id)
    context["autofocus"] = autofocus
    return context


@register.inclusion_tag(
    f"edc_subject_dashboard/bootstrap{get_bootstrap_version()}/"
    f"print_requisition_popover.html",
    takes_context=True,
)
def print_requisition_popover(context):
    C = namedtuple("Consignee", "pk name")
    consignees = []
    for consignee in django_apps.get_model("edc_lab.Consignee").objects.all():
        consignees.append(C(str(consignee.pk), consignee.name))
    context["consignees"] = consignees
    return context


@register.inclusion_tag(
    f"edc_subject_dashboard/bootstrap{get_bootstrap_version()}/appointment_status.html"
)
def render_appointment_status_icon(appt_status: str = None) -> dict[str, str]:
    return dict(
        appt_status=appt_status,
        NEW_APPT=NEW_APPT,
        IN_PROGRESS_APPT=IN_PROGRESS_APPT,
        INCOMPLETE_APPT=INCOMPLETE_APPT,
        COMPLETE_APPT=COMPLETE_APPT,
        CANCELLED_APPT=CANCELLED_APPT,
        SKIPPED_APPT=SKIPPED_APPT,
    )


@register.inclusion_tag(
    f"edc_subject_dashboard/bootstrap{get_bootstrap_version()}/dashboard/crf_totals.html",
)
def render_crf_totals(appointment: Appointment = None) -> dict[str, bool | int]:
    helper = MetadataHelper(appointment)
    skipped: bool = False
    show_totals: bool = False
    late: bool = False
    complete: bool = False
    num_keyed: int = 0
    num_total: int = 0
    if appointment.appt_status == SKIPPED_APPT:
        skipped = True
    elif appointment.appt_status == NEW_APPT and appointment.appt_datetime <= get_utcnow():
        late = True
    else:
        crf_keyed = helper.get_crf_metadata_by(entry_status=KEYED).count()
        requisition_keyed = helper.get_requisition_metadata_by(entry_status=KEYED).count()
        crf_total = helper.get_crf_metadata_by(entry_status=[REQUIRED, KEYED]).count()
        requisition_total = helper.get_requisition_metadata_by(
            entry_status=[REQUIRED, KEYED]
        ).count()
        num_keyed = crf_keyed + requisition_keyed
        num_total = crf_total + requisition_total
        if appointment.related_visit:
            show_totals = False if num_keyed != 0 and num_keyed == num_total else True
        complete = num_keyed != 0 and num_keyed == num_total
    return dict(
        show_totals=show_totals,
        skipped=skipped,
        complete=complete,
        late=late,
        keyed=num_keyed,
        total=num_total,
    )


@register.inclusion_tag(
    f"edc_subject_dashboard/bootstrap{get_bootstrap_version()}/"
    "buttons/crf_button_group.html",
    takes_context=True,
)
def render_crf_button_group(
    context,
    model_obj: CrfMetadata = None,
    appointment: Appointment = None,
    registered_subject: RegisteredSubject = None,
    visit_schedule: VisitScheduleModel = None,
):
    """Prepare context data to render CRF, History, and Query
    dashboard buttons.

    For example, in the template:
        Where `crf` is an instance of CRFMetadata

        {% crf_button_group "subject_dashboard_url" crf
           appointment registered_subject
           visit_schedule_model_obj %}
    """
    # if still using deprecated ModelWrapper, get model instance
    # from model_wrapper
    appointment = getattr(appointment, "object", appointment)
    crf_btn = CrfButton(
        metadata_model_obj=model_obj,
        appointment=appointment,
        user=context["user"],
        current_site=context["request"].site,
    )
    history_btn, query_btn = render_history_and_query_buttons(
        context, model_obj, appointment, registered_subject, visit_schedule
    )
    return dict(buttons=[crf_btn, history_btn, query_btn])


@register.inclusion_tag(
    f"edc_subject_dashboard/bootstrap{get_bootstrap_version()}/"
    "buttons/crf_button_group.html",
    takes_context=True,
)
def render_requisition_button_group(
    context,
    model_obj: CrfMetadata = None,
    appointment: Appointment = None,
    registered_subject: RegisteredSubject = None,
    visit_schedule: VisitScheduleModel = None,
):
    # if still using deprecated ModelWrapper, get model instance
    # from model_wrapper
    appointment = getattr(appointment, "object", appointment)
    requisition_btn = RequisitionButton(
        metadata_model_obj=model_obj,
        appointment=appointment,
        user=context["user"],
        current_site=context["request"].site,
    )
    history_btn, query_btn = render_history_and_query_buttons(
        context, model_obj, appointment, registered_subject, visit_schedule
    )
    return dict(buttons=[requisition_btn, history_btn, query_btn])


@register.inclusion_tag(
    f"edc_subject_dashboard/bootstrap{get_bootstrap_version()}/buttons/prn_button.html",
    takes_context=True,
)
def render_prn_button(context, model_obj, model_name: str) -> dict:
    # TODO: is this used?
    model_cls = django_apps.get_model(model_name)
    btn = PrnButton(
        model_obj=model_obj,
        model_cls=model_cls,
        subject_identifier=context.get("subject_identifier"),
        next_url_name=context.get("next_url_name"),
        user=context["request"].user,
        current_site=context["request"].site,
        request=context["request"],
    )
    return dict(btn=btn)


@register.inclusion_tag(
    f"edc_subject_dashboard/bootstrap{get_bootstrap_version()}/"
    "buttons/appointment_button.html",
    takes_context=True,
)
def render_appointment_button(context, appointment: Appointment = None):
    # if still using deprecated ModelWrapper, get model instance
    # from model_wrapper
    appointment = getattr(appointment, "object", appointment)
    appointment_btn = AppointmentButton(
        model_obj=appointment,
        user=context["user"],
        current_site=context["request"].site,
    )
    return {"btn": appointment_btn}


@register.inclusion_tag(
    f"edc_subject_dashboard/bootstrap{get_bootstrap_version()}/"
    "buttons/appointment_button.html",
    takes_context=True,
)
def render_related_visit_button(context, appointment: Appointment = None):
    # if still using deprecated ModelWrapper, get model instance
    # from model_wrapper
    appointment = getattr(appointment, "object", appointment)
    related_visit: VisitModel = appointment.related_visit
    related_visit_model_cls: Type[VisitModel] = appointment.related_visit_model_cls()
    btn = RelatedVisitButton(
        model_obj=related_visit,
        model_cls=related_visit_model_cls,
        appointment=appointment,
        user=context["user"],
        current_site=context["request"].site,
    )
    return {"btn": btn}


@register.inclusion_tag(
    f"edc_subject_dashboard/bootstrap{get_bootstrap_version()}/buttons/forms_button.html",
    takes_context=True,
)
def render_gotoforms_button(context, appointment: Appointment = None):
    # if still using deprecated ModelWrapper, get model instance
    # from model_wrapper
    appointment: Appointment = getattr(appointment, "object", appointment)
    related_visit: VisitModel = appointment.related_visit
    related_visit_model_cls: Type[VisitModel] = appointment.related_visit_model_cls()
    btn = GotToFormsButton(
        model_obj=related_visit,
        model_cls=related_visit_model_cls,
        appointment=appointment,
        user=context["user"],
        current_site=context["request"].site,
    )
    return {"btn": btn}


@register.inclusion_tag(
    f"edc_subject_dashboard/bootstrap{get_bootstrap_version()}/"
    "buttons/appointment_button.html",
    takes_context=True,
)
def render_timepoint_status_button(context, appointment: Appointment = None):
    btn = TimepointStatusButton(
        model_obj=appointment,
        user=context["user"],
        current_site=context["request"].site,
    )
    return {"btn": btn}


@register.inclusion_tag(
    f"edc_subject_dashboard/bootstrap{get_bootstrap_version()}/"
    "buttons/appointment_button.html",
    takes_context=True,
)
def render_subject_consent_button(
    context, consent: ConsentModel = None, appointment: Appointment = None
):
    btn = SubjectConsentButton(
        model_obj=consent,
        user=context["user"],
        current_site=context["request"].site,
        appointment=appointment,
    )
    return {"btn": btn}


@register.inclusion_tag(
    f"edc_subject_dashboard/bootstrap{get_bootstrap_version()}/"
    "buttons/unscheduled_appointment_button.html",
    takes_context=True,
)
def render_unscheduled_appointment_button(
    context, appointment: Appointment = None, view_appointment: bool = None
):
    show_button = False
    anchor_id: str | None = None
    url: str | None = None
    disabled = "disabled"
    title: str | None = None
    any_in_progress = appointment.__class__.objects.filter(
        appt_status=IN_PROGRESS_APPT,
        subject_identifier=appointment.subject_identifier,
        visit_schedule_name=appointment.visit_schedule_name,
        schedule_name=appointment.schedule_name,
    ).exists()
    if (
        not any_in_progress
        and appointment.appt_status in [INCOMPLETE_APPT, COMPLETE_APPT]
        and appointment
        and appointment.site.id == context["request"].site.id
        and appointment.relative_next
        and (
            appointment.appt_datetime.date() + relativedelta(days=1)
            != appointment.relative_next.appt_datetime.date()
        )
    ):
        show_button = True
        anchor_id = (
            f"unscheduled_appt_btn_{appointment.visit_code}_"
            f"{appointment.visit_code_sequence}"
        )
        if view_appointment and appointment.site.id == context["request"].site.id:
            url = get_unscheduled_appointment_url(appointment)
        disabled = "disabled" if not url else ""
        if view_appointment and appointment.site.id == context["request"].site.id:
            title = "" if disabled else "Edit appointment"
        else:
            title = "No permission to edit"
    return dict(
        show_button=show_button,
        anchor_id=anchor_id,
        appointment=appointment,
        view_appointment=view_appointment,
        url=url,
        disabled=disabled,
        title=title,
        INCOMPLETE_APPT=INCOMPLETE_APPT,
        COMPLETE_APPT=COMPLETE_APPT,
    )
