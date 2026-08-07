from datetime import date

import requests

URL = "https://www.datos.gov.co/resource/32sa-8pi3.json"
TIMEOUT_SEGUNDOS = 30
LIMITE_REGISTROS = 50_000

def fetch_trm(desde: date, hasta: date) -> str:
    """
    Pide los registros de TRM cuyo vigenciadesde cae en [desde, hasta].

    Devuelve el cuerpo de la respuesta sin parsear.
    Lanza requests.HTTPError si la API responde con un código de error.
    """
    respuesta = requests.get(
        URL,
        params={
            "$where": (
                f"vigenciadesde between '{desde.isoformat()}' "
                f"and '{hasta.isoformat()}'"
            ),
            "$order": "vigenciadesde ASC",
            "$limit": LIMITE_REGISTROS,
        },
        timeout=TIMEOUT_SEGUNDOS,
    )
    respuesta.raise_for_status()
    return respuesta.text