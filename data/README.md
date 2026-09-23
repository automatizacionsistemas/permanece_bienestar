# data

Estos son los archivos que necesita `scripts/build_pmtiles.py`. Para replicar el proceso, esta carpeta debe quedar así:

```
data/
├── DEPARTAMENTOS.xlsx
├── MUNICIPIOS.xlsx
├── PAISES.xlsx
├── mgn2025/
│   ├── MGN_ADM_DPTO_POLITICO.shp (+ .dbf .shx .prj .cpg)
│   └── MGN_ADM_MPIO_GRAFICO.shp  (+ .dbf .shx .prj .cpg)
└── tiles/            # salida del script
```

## Catálogos xlsx (los entrega el cliente)

Son exportaciones de PeopleSoft y no se pueden descargar. Hay que pedirlas a quien encarga el trabajo.

| archivo | tabla PeopleSoft | contenido |
|---|---|---|
| `PAISES.xlsx` | `PS_COUNTRY_TBL` | países (ISO3, nombre, ISO2) |
| `DEPARTAMENTOS.xlsx` | `PS_STATE_TBL` | país, código de departamento, nombre |
| `MUNICIPIOS.xlsx` | `PS_ETY_CIUD_TBL` | país, departamento, código DANE de 5 dígitos, nombre |

Traen filas de otros países, pero el script solo usa las de `COL`.

## Límites DANE MGN 2025 (se descargan)

Es el Marco Geoestadístico Nacional del DANE, versión 2025, con los límites oficiales y los códigos DANE. El geoportal de DANE (`geoportal.dane.gov.co`) no respondía en septiembre de 2026, así que se descarga del hub de DANE en ArcGIS Online (usuario `adm_cdge_hub`):

- Departamentos: [MGN2025_DPTO_POLITICO](https://www.arcgis.com/home/item.html?id=932103e6ba7a42a8bb77d3ebfea30254) (12MB)
- Municipios: [MGN2025_MPIO_GRAFICO](https://www.arcgis.com/home/item.html?id=85160ce9897648ee8aa9bb0e7198a2d3) (72MB)

Desde la raíz del proyecto:

```bash
mkdir -p data/mgn2025 && cd data/mgn2025
curl -L -o dpto.zip "https://www.arcgis.com/sharing/rest/content/items/932103e6ba7a42a8bb77d3ebfea30254/data"
curl -L -o mpio.zip "https://www.arcgis.com/sharing/rest/content/items/85160ce9897648ee8aa9bb0e7198a2d3/data"
unzip -o dpto.zip && unzip -o mpio.zip && rm dpto.zip mpio.zip
cd ../..
```


