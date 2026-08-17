"""Zona raw: persiste las respuestas de la API sin modificarlas."""

from datetime import datetime, timezone
from functools import lru_cache
import boto3

from trm_signal.config import S3_BUCKET

PREFIJO_RAW = "raw"

@lru_cache(maxsize=1)
def _cliente():
    """Cliente de S3, creado una sola vez y reutilizado."""
    return boto3.client("s3")


def _construir_key(momento: datetime) -> str:
    """Construye la clave S3 para un momento dado."""
    return (
        f"{PREFIJO_RAW}/{momento.strftime('%Y/%m/%d')}/"
        f"trm_{momento.strftime('%Y%m%dT%H%M%S')}.json"
    )

def _partir_uri(uri: str) -> tuple[str, str]:
    if not uri.startswith("s3://"):
        raise ValueError(f"URI de S3 inválida: {uri!r}")
    bucket, _, key = uri.removeprefix("s3://").partition("/")
    if not bucket or not key:
        raise ValueError(f"URI de S3 incompleta: {uri!r}")
    return bucket, key

def guardar_crudo(contenido: str, momento: datetime | None = None) -> str:
    """Sube la respuesta cruda a S3 sin modificarla.

    Devuelve la URI s3:// donde quedó guardada.
    """
    momento = momento or datetime.now(timezone.utc)
    key = _construir_key(momento)

    _cliente().put_object(
        Bucket=S3_BUCKET,
        Key=key, 
        Body=contenido.encode("utf-8"), 
        ContentType="application/json"
        )

    return f"s3://{S3_BUCKET}/{key}"

def descargar_crudo(uri: str) -> str:
    """Descarga un objeto de la zona raw y devuelve su contenido como texto."""
    bucket, key = _partir_uri(uri)
    obj = _cliente().get_object(Bucket=bucket, Key=key)
    return obj["Body"].read().decode("utf-8")