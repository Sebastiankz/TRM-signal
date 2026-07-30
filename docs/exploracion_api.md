1. curl -s "https://www.datos.gov.co/resource/32sa-8pi3.json" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" -> 1000
2. curl -s "https://www.datos.gov.co/resource/32sa-8pi3.json?\$limit=50000" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" -> siempre devuelve 8315
3. curl -s 'https://www.datos.gov.co/resource/32sa-8pi3.json?$select=count(*)' -> 8315
4. curl -s "https://www.datos.gov.co/resource/32sa-8pi3.json?\$order=vigenciadesde%20ASC&\$limit=1"
   el valor más viejo es 643.42 en la fecha 1991-12-02
   el valor más reciente es 3205.87 en la fecha 2026-07-29
5.
