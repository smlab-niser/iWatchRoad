"""Restore pothole frame images from the source CSV's base64 column.

Why this exists rather than `reimport_frame_images`: that command matches rows
with `Pothole.objects.filter(frame_number=...)`, but frame numbers are **not
unique** -- 1,611 rows share only 926 distinct frame numbers, and frame 311
alone appears 8 times. Matching on it attaches images to the wrong potholes.

`import_final_csv` created these rows keyed on
`(latitude, longitude, timestamp)`, so that is the identity used here.

The CSV keeps each frame as a base64 JPEG in `Frame_Data`; this decodes once
and writes a real file, so nothing base64-shaped is persisted.
See Plan/EVIDENCE_STORAGE.md.

Usage:
    python manage.py restore_frame_images --dry-run
    python manage.py restore_frame_images
    python manage.py restore_frame_images --limit 200
"""
import csv
import os
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from potholes.frame_storage import save_frame_base64
from potholes.models import Pothole

# Frame_Data fields are multi-megabyte base64 blobs.
csv.field_size_limit(50_000_000)

DATE_FORMATS = [
    "%m/%d/%Y %I:%M:%S %p",
    "%d/%m/%Y %I:%M:%S %p",
    "%Y-%m-%d %H:%M:%S",
]


class Command(BaseCommand):
    help = "Restore pothole frame images from the base64 column of the source CSV."

    def add_arguments(self, parser):
        parser.add_argument("--csv-file", default="pothole_gps_final.csv")
        parser.add_argument("--limit", type=int, default=0,
                            help="Stop after this many CSV rows (0 = all).")
        parser.add_argument("--dry-run", action="store_true",
                            help="Report what would happen; write nothing.")
        parser.add_argument("--overwrite", action="store_true",
                            help="Replace frames whose file already exists.")

    def handle(self, *args, **o):
        path = o["csv_file"]
        if not os.path.isabs(path):
            path = os.path.join(settings.BASE_DIR, path)
        if not os.path.exists(path):
            self.stdout.write(self.style.ERROR(f"CSV not found: {path}"))
            return

        dry = o["dry_run"]
        self.stdout.write(
            f"{'DRY RUN - ' if dry else ''}restoring frames from {path}")
        self.stdout.write(f"media root: {settings.MEDIA_ROOT}\n")

        rows = matched = restored = skipped_has_file = 0
        no_match = no_data = failed = 0

        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for row in csv.DictReader(fh):
                rows += 1
                if o["limit"] and rows > o["limit"]:
                    break

                b64 = (row.get("Frame_Data") or "").strip()
                if not b64:
                    no_data += 1
                    continue

                ts = self._timestamp(row)
                if ts is None:
                    no_match += 1
                    continue

                try:
                    lat = float(row.get("Latitude", ""))
                    lon = float(row.get("Longitude", ""))
                except (TypeError, ValueError):
                    no_match += 1
                    continue

                # Same identity key import_final_csv used to create these rows.
                pothole = Pothole.objects.filter(
                    latitude=str(lat), longitude=str(lon), timestamp=ts
                ).first()
                if pothole is None:
                    no_match += 1
                    continue

                matched += 1

                if pothole.frame_image and not o["overwrite"]:
                    full = os.path.join(settings.MEDIA_ROOT, pothole.frame_image.name)
                    if os.path.exists(full):
                        skipped_has_file += 1
                        continue

                if dry:
                    restored += 1
                else:
                    frame_no = pothole.frame_number
                    if frame_no is None:
                        try:
                            frame_no = int(row.get("Frame", "") or 0) or None
                        except ValueError:
                            frame_no = None
                    if save_frame_base64(pothole, b64, frame_no):
                        pothole.save(update_fields=["frame_image"])
                        restored += 1
                    else:
                        failed += 1

                if restored and restored % 100 == 0:
                    self.stdout.write(f"  ...{restored} frames restored")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"{'would restore' if dry else 'restored'}: {restored}"))
        self.stdout.write(f"  csv rows read:        {rows}")
        self.stdout.write(f"  matched a pothole:    {matched}")
        self.stdout.write(f"  skipped (file exists):{skipped_has_file}")
        self.stdout.write(f"  no matching pothole:  {no_match}")
        self.stdout.write(f"  row had no frame data:{no_data}")
        if failed:
            self.stdout.write(self.style.WARNING(f"  failed to decode/save: {failed}"))

    @staticmethod
    def _timestamp(row):
        date_s = (row.get("Date") or "").strip()
        time_s = (row.get("Time") or "").strip()
        if not date_s or not time_s:
            return None
        joined = f"{date_s} {time_s}"
        for fmt in DATE_FORMATS:
            try:
                naive = datetime.strptime(joined, fmt)
            except ValueError:
                continue
            # USE_TZ is on, and import_final_csv stored these as naive
            # datetimes -- Django interpreted them in TIME_ZONE. Attach the
            # same zone so the lookup resolves to the identical instant
            # (and Django stops warning about naive comparisons).
            if timezone.is_naive(naive):
                return timezone.make_aware(
                    naive, timezone.get_default_timezone())
            return naive
        return None
