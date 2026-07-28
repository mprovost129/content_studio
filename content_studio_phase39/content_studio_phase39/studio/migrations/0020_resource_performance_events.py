from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("studio", "0019_resource_pdf_lead_magnets"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResourcePerformanceEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("event_type", models.CharField(choices=[("view", "Resource view"), ("pdf_unlock", "PDF unlock"), ("pdf_download", "PDF download")], db_index=True, max_length=20)),
                ("email", models.EmailField(blank=True, db_index=True, max_length=254)),
                ("source_url", models.CharField(blank=True, max_length=300)),
                ("referrer", models.CharField(blank=True, max_length=300)),
                ("user_agent", models.CharField(blank=True, max_length=300)),
                ("occurred_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("resource", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="performance_events", to="studio.learningresource")),
                ("subscriber", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="resource_performance_events", to="studio.newslettersubscriber")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="resource_performance_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-occurred_at",),
                "indexes": [models.Index(fields=["resource", "event_type", "occurred_at"], name="studio_reso_resourc_b114ed_idx"), models.Index(fields=["event_type", "occurred_at"], name="studio_reso_event_t_3f2165_idx")],
            },
        ),
    ]
