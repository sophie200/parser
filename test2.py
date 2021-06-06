# Generated by Django 2.2.11 on 2020-07-24 17:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0120_galaxy_credentials'),
    ]

    operations = [
        migrations.AddIndex(
            model_name="event", index=models.Index(fields=["elements_hash"], name="posthog_eve_element_48becd_idx"),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["timestamp", "team_id", "event"], name="posthog_eve_timesta_1f6a8c_idx",),
        ),
        migrations.RemoveIndex(model_name="product", name="posthog_eve_timesta_1f6a8c_idx")
    ]
