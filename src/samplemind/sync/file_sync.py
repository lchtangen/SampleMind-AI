"""Upload and download audio files to/from S3-compatible object storage.

Phase 13 — Cloud Sync.
Uses boto3 with a configurable endpoint_url to support R2, S3, and B2.
push_files() uploads new/changed WAV files, pull_files() downloads files
missing locally. Uses ETag comparison to skip unchanged files.
"""
# TODO: implement in Phase 13 — Cloud Sync
