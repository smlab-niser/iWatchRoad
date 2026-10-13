"""Obsolete: base64 frame storage has been removed.

This command existed to migrate rows from the old `frame_image_base64`
TextField into `frame_image` files. That column no longer exists -- every
frame is now written straight to disk as a JPEG at ingest time
(`potholes.frame_storage`). Nothing is left to convert.

Kept as a stub rather than deleted so that any operator runbook or cron entry
still referencing it fails loudly and explains itself instead of raising an
opaque "Unknown command" error.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'OBSOLETE - base64 frame storage was removed; frames are files now.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            'This command is obsolete and does nothing.\n'
            'The `frame_image_base64` column was removed in migration '
            'potholes.0006. Frames are stored as JPEG files on disk via '
            '`potholes.frame_storage`; the database keeps only the path.\n'
            'See Plan/EVIDENCE_STORAGE.md.'
        ))
