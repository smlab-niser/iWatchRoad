"""Obsolete: base64 frame storage has been removed.

This command reported on, and cleared, rows whose `frame_image_base64` blob
duplicated an already-saved `frame_image` file. That column no longer exists,
so there is nothing to clean up.

Kept as a stub rather than deleted so that any operator runbook or cron entry
still referencing it fails loudly and explains itself instead of raising an
opaque "Unknown command" error.
"""
import argparse

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'OBSOLETE - base64 frame storage was removed; nothing to clean up.'

    def add_arguments(self, parser):
        # Accepted and ignored so existing invocations don't fail on argparse.
        parser.add_argument('--confirm', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--batch-size', type=int, default=100, help=argparse.SUPPRESS)

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            'This command is obsolete and does nothing.\n'
            'The `frame_image_base64` column was removed in migration '
            'potholes.0006. Frames are stored as JPEG files on disk via '
            '`potholes.frame_storage`; the database keeps only the path.\n'
            'See Plan/EVIDENCE_STORAGE.md.'
        ))
