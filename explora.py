import requests

URL = "https://www.datos.gov.co/resource/32sa-8pi3.json"

r = requests.get(URL)
print("status:", r.status_code)
print("registros:", len(r.json()))