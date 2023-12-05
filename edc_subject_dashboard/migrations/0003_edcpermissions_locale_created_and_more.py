# Generated by Django 4.2.7 on 2023-12-01 14:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("edc_subject_dashboard", "0002_alter_edcpermissions_device_created_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="edcpermissions",
            name="locale_created",
            field=models.CharField(
                blank=True,
                help_text="Auto-updated by Modeladmin",
                max_length=10,
                null=True,
                verbose_name="Locale created",
            ),
        ),
        migrations.AddField(
            model_name="edcpermissions",
            name="locale_modified",
            field=models.CharField(
                blank=True,
                help_text="Auto-updated by Modeladmin",
                max_length=10,
                null=True,
                verbose_name="Locale modified",
            ),
        ),
    ]