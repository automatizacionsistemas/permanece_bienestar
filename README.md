# colombia-schools

Genera PMTiles de los límites de Colombia (país, departamentos y municipios) con los códigos DANE, para unirlos con los catálogos de PeopleSoft (`data/*.xlsx`).

## Generar datos

1. Datos fuente: [data/README.md](data/README.md)
2. Generar los tiles: [scripts/README.md](scripts/README.md)

## Sitio

`site/` tiene el mapa (`index.html`) y los tiles (`site/tiles/`). Cada push a `main` que toca `site/` lo publica en la rama `gh-pages` con [.github/workflows/deploy.yml](.github/workflows/deploy.yml).

- Sitio: https://rub21.github.io/colombia-schools/
- Demo: https://rub21.github.io/colombia-schools/demo.html (JSON editable con datos de ejemplo de `site/sample-data.json`)
- Tiles: `https://rub21.github.io/colombia-schools/tiles/municipios.pmtiles`

La primera vez hay que activar Pages en GitHub: Settings → Pages → Deploy from a branch → `gh-pages` / `/ (root)`.

### Insertar el mapa en PeopleSoft

El mapa se carga en un iframe y recibe los datos con `postMessage`. Cuando está listo envía `{type: "map-ready"}` y espera `{type: "map-data", title, values}`, donde `values` es `{"05001": 120, ...}` (código DANE del municipio → cantidad). El mapa tiene dos niveles, Departamentos y Municipios. Los departamentos se calculan sumando los municipios (los 2 primeros dígitos del código). Si los valores no se pueden sumar (promedios, tasas), envía también `departamentos: {"05": 3400, ...}`. [site/embed-example.html](site/embed-example.html) tiene el código completo; en PeopleSoft `data` es `%Bind(:1)`.

Para limitar quién puede enviar datos, agrega el dominio de PeopleSoft a `ALLOWED_ORIGINS` en `site/index.html`.

### Probar en local

PMTiles necesita range requests, y `python3 -m http.server` no los soporta.

```bash
npx http-server site -c-1
```

Abrir http://localhost:8080/embed-example.html
