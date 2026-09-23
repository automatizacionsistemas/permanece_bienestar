"""Build PMTiles for Colombia admin levels (país, departamentos, municipios).

Geometry comes from DANE MGN 2025 (data/mgn2025), downloaded from the DANE
hub on ArcGIS Online (owner adm_cdge_hub):
  https://www.arcgis.com/sharing/rest/content/items/932103e6ba7a42a8bb77d3ebfea30254/data  (DPTO_POLITICO)
  https://www.arcgis.com/sharing/rest/content/items/85160ce9897648ee8aa9bb0e7198a2d3/data  (MPIO_GRAFICO) Codes and PeopleSoft names come
from the DEPARTAMENTOS and MUNICIPIOS xlsx. MGN carries DANE codes, so the
join is by code. MGN has no country layer; país is the union of departamentos.

Usage: python3 scripts/build_pmtiles.py
Output: site/tiles/*.pmtiles, site/tiles/labels.geojson and data/tiles/match_report.csv
"""
import re
import subprocess
import tempfile
from pathlib import Path

import geopandas as gpd
import openpyxl
import pandas as pd
import shapely

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MGN = DATA / "mgn2025"
OUT = DATA / "tiles"
TILES = ROOT / "site" / "tiles"  # published with the site

# xlsx code -> DANE code, where PeopleSoft uses an old code
CODE_REMAP = {
    "27086": "27493",  # Nuevo Belén de Bajirá
}

TIPPECANOE_BASE = [
    "tippecanoe", "--force",
    "--no-feature-limit", "--no-tile-size-limit",
    "--no-simplification-of-shared-nodes",
    "--no-tiny-polygon-reduction",
]


def read_rows(name):
    wb = openpyxl.load_workbook(DATA / f"{name}.xlsx", read_only=True)
    # row 0 is the query name, row 1 the header
    return list(wb.worksheets[0].iter_rows(values_only=True))[2:]


def load_catalogs():
    pais = {r[0]: {"nombre": r[1], "iso2": r[3]} for r in read_rows("PAISES") if r[0]}
    # 26 "Ucayali" is a Peru region miscoded as COL
    deptos = {
        r[1]: r[2] for r in read_rows("DEPARTAMENTOS")
        if r[0] == "COL" and r[1] != "26"
    }
    # keep real 5-digit DANE codes; drops 655xx sentinels, embassy row and junk rows
    mpios = {
        CODE_REMAP.get(r[2], r[2]): r[3]
        for r in read_rows("MUNICIPIOS")
        if r[0] == "COL" and re.fullmatch(r"\d{5}", str(r[2])) and not str(r[2]).startswith("655")
    }
    return pais, deptos, mpios


def drop_slivers(geom, max_area=1e-10):
    """Remove tiny holes left between departamentos after union.

    max_area is in degrees² (1e-10 is about 1 m²); the MGN 2025 slivers are under 1e-12.
    """
    parts = [p for p in getattr(geom, "geoms", [geom]) if p.geom_type == "Polygon"]
    return shapely.MultiPolygon([
        shapely.Polygon(p.exterior, [h for h in p.interiors if shapely.Polygon(h).area > max_area])
        for p in parts
    ])


def tippecanoe(gdf, layer, out, minzoom, maxzoom):
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"{layer}.geojsonl"
        gdf.to_crs(4326).to_file(src, driver="GeoJSONSeq")
        cmd = TIPPECANOE_BASE + [
            "-l", layer, "-Z", str(minzoom), "-z", str(maxzoom),
            "-o", str(out), str(src),
        ]
        subprocess.run(cmd, check=True)


def label_case(name):
    """'SAN ANDRÉS DE TUMACO' -> 'San Andrés de Tumaco'. DANE names keep their accents."""
    small = {"De", "Del", "La", "Las", "Los", "El", "Y"}
    words = name.title().split(" ")
    return " ".join(w.lower() if i and w in small else w for i, w in enumerate(words))


def write_labels(g1, g2, out):
    """One point per polygon for map labels. Tiled polygons repeat labels on every tile."""
    def points(gdf, nivel, code):
        name = gdf.nombre.map(label_case)
        # area in degrees², only used to show bigger places first
        return gpd.GeoDataFrame(
            {"nivel": nivel, "codigo": gdf[code], "label": name, "area": gdf.geometry.area.round(4)},
            geometry=gdf.geometry.representative_point(), crs=gdf.crs,
        )

    labels = pd.concat([points(g1, "departamento", "cod_dpto"), points(g2, "municipio", "cod_mpio")])
    labels = labels.to_crs(4326)
    labels.geometry = shapely.set_precision(labels.geometry.values, 1e-5)
    out.unlink(missing_ok=True)
    labels.to_file(out, driver="GeoJSON", COORDINATE_PRECISION=5)


def main():
    OUT.mkdir(exist_ok=True)
    TILES.mkdir(parents=True, exist_ok=True)
    pais, deptos, mpios = load_catalogs()

    g1 = gpd.read_file(MGN / "MGN_ADM_DPTO_POLITICO.shp")
    g2 = gpd.read_file(MGN / "MGN_ADM_MPIO_GRAFICO.shp")

    g1 = g1.rename(columns={"dpto_ccdgo": "cod_dpto", "dpto_cnmbr": "nombre"})
    g1["cod_pais"] = "COL"
    g1["descr"] = g1.cod_dpto.map(deptos)
    g1 = g1[["cod_pais", "cod_dpto", "nombre", "descr", "geometry"]]

    g2 = g2.rename(columns={
        "dpto_ccdgo": "cod_dpto", "mpio_cdpmp": "cod_mpio",
        "mpio_cnmbr": "nombre", "dpto_cnmbr": "dpto", "mpio_tipo": "tipo",
    })
    g2["cod_pais"] = "COL"
    g2["descr"] = g2.cod_mpio.map(mpios)
    g2 = g2[["cod_pais", "cod_dpto", "cod_mpio", "nombre", "descr", "dpto", "tipo", "geometry"]]

    g0 = gpd.GeoDataFrame(
        {"cod_pais": ["COL"], "iso2": [pais["COL"]["iso2"]], "nombre": [pais["COL"]["nombre"]]},
        geometry=[drop_slivers(g1.union_all())], crs=g1.crs,
    )

    mgn_dptos, mgn_mpios = set(g1.cod_dpto), set(g2.cod_mpio)
    report = pd.DataFrame(
        [{"nivel": "departamento", "lado": "xlsx_sin_poligono", "codigo": k, "nombre": v}
         for k, v in deptos.items() if k not in mgn_dptos]
        + [{"nivel": "departamento", "lado": "mgn_sin_xlsx", "codigo": r.cod_dpto, "nombre": r.nombre}
           for r in g1[g1.descr.isna()].itertuples()]
        + [{"nivel": "municipio", "lado": "xlsx_sin_poligono", "codigo": k, "nombre": v}
           for k, v in sorted(mpios.items()) if k not in mgn_mpios]
        + [{"nivel": "municipio", "lado": "mgn_sin_xlsx", "codigo": r.cod_mpio, "nombre": r.nombre}
           for r in g2[g2.descr.isna()].itertuples()],
        columns=["nivel", "lado", "codigo", "nombre"],
    )
    report.to_csv(OUT / "match_report.csv", index=False)

    print(f"departamentos: {g1.descr.notna().sum()}/{len(g1)} con código en xlsx")
    print(f"municipios: {g2.descr.notna().sum()}/{len(g2)} con código en xlsx; "
          f"{len(mpios.keys() - mgn_mpios)}/{len(mpios)} códigos xlsx sin polígono")

    write_labels(g1, g2, TILES / "labels.geojson")
    tippecanoe(g0, "pais", TILES / "pais.pmtiles", 0, 10)
    tippecanoe(g1, "departamentos", TILES / "departamentos.pmtiles", 0, 12)
    tippecanoe(g2, "municipios", TILES / "municipios.pmtiles", 0, 14)


if __name__ == "__main__":
    main()
