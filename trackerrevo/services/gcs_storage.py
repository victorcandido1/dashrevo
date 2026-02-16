"""
Google Cloud Storage backend - persistência no GCP
Usado quando rodando no Cloud Run (storage efêmero)
"""
import json
import os

_GCS_CLIENT = None
_BUCKET_NAME = None


def _is_gcp():
    return bool(os.environ.get('K_SERVICE') or os.environ.get('GOOGLE_CLOUD_PROJECT'))


def _get_bucket():
    global _GCS_CLIENT, _BUCKET_NAME
    if not _is_gcp():
        return None
    bucket = os.environ.get('GCS_BUCKET', 'trackerrevo-cache')
    try:
        from google.cloud import storage
        if _GCS_CLIENT is None:
            _GCS_CLIENT = storage.Client()
        if _BUCKET_NAME is None:
            _BUCKET_NAME = bucket
        return _GCS_CLIENT.bucket(_BUCKET_NAME)
    except Exception:
        return None


def gcs_read_json(blob_path):
    """Lê JSON de um blob no GCS. Retorna None se não existir."""
    b = _get_bucket()
    if not b:
        return None
    try:
        blob = b.blob(blob_path)
        data = blob.download_as_string().decode('utf-8')
        return json.loads(data)
    except Exception:
        return None


def gcs_write_json(blob_path, data):
    """Escreve JSON em um blob no GCS."""
    b = _get_bucket()
    if not b:
        return False
    try:
        blob = b.blob(blob_path)
        blob.upload_from_string(
            json.dumps(data, indent=2, default=str),
            content_type='application/json'
        )
        return True
    except Exception:
        return False
