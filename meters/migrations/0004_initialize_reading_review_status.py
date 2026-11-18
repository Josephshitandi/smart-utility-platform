
from django.db import migrations


def initialize_review_status(apps, schema_editor):
    MeterReading = apps.get_model("meters", "MeterReading")

    MeterReading.objects.filter(status="flagged").update(
        review_status="pending"
    )

    MeterReading.objects.filter(status="normal").update(
        review_status="not_required"
    )


def reverse_review_status(apps, schema_editor):
    MeterReading = apps.get_model("meters", "MeterReading")

    MeterReading.objects.all().update(
        review_status="not_required"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("meters", "0003_meterreading_review_notes_meterreading_review_status_and_more"),
    ]

    operations = [
        migrations.RunPython(
            initialize_review_status,
            reverse_review_status,
        ),
    ]
