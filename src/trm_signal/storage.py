from datetime import datetime
from pathlib import Path

RAW_DIR = Path("data/raw")

def guardar_crudo(contenido: str, momento: datetime | None = None) -> Path:
    """Guarda la respuesta cruda de la API sin modificarla.

    Devuelve la ruta donde quedó escrita.
    """
    momento = momento or datetime.now()
    carpeta = RAW_DIR / momento.strftime("%Y/%m/%d")
    carpeta.mkdir(parents=True, exist_ok=True)

    destino = carpeta / f"trm_{momento.strftime('%Y%m%dT%H%M%S')}.json"
    destino.write_text(contenido, encoding="utf-8")
    return destino

# format: data/raw/2026/07/29/trm_20260729T183012.json
