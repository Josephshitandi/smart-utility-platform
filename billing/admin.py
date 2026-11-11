from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Q
from unfold.admin import ModelAdmin

from meters.models import Meter, MeterReading

from .models import Bill, Tariff
from .services import create_bill


class BillCreationForm(forms.ModelForm):
    """
    Custom form for generating bills through the billing service.
    """

    meter_id = forms.ModelChoiceField(
        queryset=Meter.objects.filter(
            status=Meter.Status.ACTIVE
        ),
        label="Meter",
        help_text="Select an active meter.",
    )

    previous_reading_id = forms.ModelChoiceField(
        queryset=MeterReading.objects.none(),
        label="Previous Reading",
    )

    current_reading_id = forms.ModelChoiceField(
        queryset=MeterReading.objects.none(),
        label="Current Reading",
    )

    due_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="The due date cannot be before the billing period ends.",
    )

    class Meta:
        model = Bill
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        meter_id = None

        if self.is_bound:
            meter_id = self.data.get(
                self.add_prefix("meter_id")
            )
        else:
            meter_id = self.initial.get("meter_id")

        if meter_id:
            try:
                meter = Meter.objects.get(
                    pk=meter_id,
                    status=Meter.Status.ACTIVE,
                )

                readings = MeterReading.objects.filter(
                    meter=meter
                ).order_by("-reading_date")

                self.fields[
                    "previous_reading_id"
                ].queryset = readings

                self.fields[
                    "current_reading_id"
                ].queryset = readings

            except (Meter.DoesNotExist, ValueError, TypeError):
                pass


@admin.register(Tariff)
class TariffAdmin(ModelAdmin):

    list_display = (
        "id",
        "name",
        "meter_type",
        "rate_per_unit",
        "fixed_charge",
        "effective_from",
        "effective_to",
        "is_active",
        "created_by",
    )

    list_filter = (
        "meter_type",
        "is_active",
        "effective_from",
    )

    search_fields = (
        "name",
        "created_by__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(Bill)
class BillAdmin(ModelAdmin):

    list_display = (
        "id",
        "meter",
        "tariff",
        "billing_period_start",
        "billing_period_end",
        "units_consumed",
        "amount",
        "due_date",
        "status",
        "created_by",
    )

    list_filter = (
        "status",
        "billing_period_start",
        "billing_period_end",
        "due_date",
    )

    search_fields = (
        "meter__meter_number",
        "created_by__email",
    )

    readonly_fields = (
        "meter",
        "tariff",
        "previous_reading",
        "current_reading",
        "billing_period_start",
        "billing_period_end",
        "units_consumed",
        "rate_per_unit",
        "fixed_charge",
        "subtotal",
        "amount",
        "due_date",
        "status",
        "created_by",
        "created_at",
        "updated_at",
    )

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs["form"] = BillCreationForm

        return super().get_form(request, obj, **kwargs)

    def get_fields(self, request, obj=None):
        if obj is None:
            return (
                "meter_id",
                "previous_reading_id",
                "current_reading_id",
                "due_date",
            )

        return self.readonly_fields

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return False

        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if change:
            return

        created_bill = create_bill(
            meter_id=form.cleaned_data["meter_id"].pk,
            previous_reading_id=form.cleaned_data[
                "previous_reading_id"
            ].pk,
            current_reading_id=form.cleaned_data[
                "current_reading_id"
            ].pk,
            due_date=form.cleaned_data["due_date"],
            created_by=request.user,
        )

        obj.pk = created_bill.pk
        obj.refresh_from_db()