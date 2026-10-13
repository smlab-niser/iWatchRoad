"""Drop the deprecated base64 frame column and date-partition frame uploads.

The `frame_image_base64` column was already absent from the deployed
databases (dropped out-of-band); the model had drifted ahead of the schema,
which broke every INSERT into potholes_pothole. This migration makes the model
match reality.

Evidence frames are now always JPEG files on disk (`frame_image`), with only
the path stored in the database. See Plan/EVIDENCE_STORAGE.md.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('potholes', '0005_add_road_health_models'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pothole',
            name='frame_image_base64',
        ),
        migrations.AlterField(
            model_name='pothole',
            name='frame_image',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='pothole_frames/%Y/%m/%d/',
                help_text='Evidence frame (JPEG file on disk; DB stores the path only)',
            ),
        ),
    ]
