# scripts

## build_pmtiles.py

Une los límites del MGN 2025 con los catálogos xlsx por código DANE y genera los PMTiles en `site/tiles/`. Antes de correrlo hay que tener los datos en `data/` (ver [data/README.md](../data/README.md)).

### Requisitos

- Python 3 con `geopandas`, `pyogrio`, `openpyxl`, `pandas`
- [tippecanoe](https://github.com/felt/tippecanoe) 2.17 o mayor

### Uso

Desde la raíz del proyecto:

```bash
python3 scripts/build_pmtiles.py
```

### Salida (`site/tiles/`)

| archivo | capa | zoom | campos |
|---|---|---|---|
| `pais.pmtiles` | `pais` | 0–10 | `cod_pais`, `iso2`, `nombre` |
| `departamentos.pmtiles` | `departamentos` | 0–12 | `cod_pais`, `cod_dpto`, `nombre`, `descr` |
| `municipios.pmtiles` | `municipios` | 0–14 | `cod_pais`, `cod_dpto`, `cod_mpio`, `nombre`, `descr`, `dpto`, `tipo` |

- `labels.geojson` tiene un punto por departamento y municipio (`nivel`, `codigo`, `label`, `area`) para las etiquetas del mapa. `label` es el nombre del DANE, con tildes.
- `nombre` es el nombre oficial del DANE y `descr` es el nombre que aparece en PeopleSoft.
- `tipo` puede ser `MUNICIPIO`, `ÁREA NO MUNICIPALIZADA` o `ISLA`.
- `data/tiles/match_report.csv` lista los códigos que no cruzan entre el xlsx y el MGN.

### Notas sobre los datos

- El xlsx usa el código `27086` para Belén de Bajirá. En el DANE es `27493`, y el script hace el cambio.
- Se ignoran "Ucayali" (código 26, es de Perú), los códigos 655xx (aduanas y aeropuerto) y la fila de embajada.
- 7 códigos del xlsx ya no existen en el MGN: Mapiripana (hoy es parte de Barrancominas), Morichal, Villa Fátima, Acaricuara, Santa Rita, San José de Ocune y Ulala.
