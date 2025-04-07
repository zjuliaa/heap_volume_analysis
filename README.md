## Analiza objętości i powierzchni hałd LiDAR
**Opis**

Skrypt umożliwia przetwarzanie danych LiDAR w celu obliczenia objętości, powierzchni oraz pokrycia punktami LiDAR dla obszarów wyznaczonych przez poligony zawarte w pliku GeoJSON. Skrypt interpoluje dane z LiDAR na model terenu, a następnie wykonuje analizę dla wskazanych obszarów. Wyniki są zapisywane w postaci pliku CSV oraz GeoJSON.

**Wymagania**

Wymagane biblioteki w Python:

- geopandas
- numpy
- scipy
- rasterio
- pyproj
- shapely
- laspy
- pandas
- argparse

**Pliki wejściowe**

- GeoJSON z poligonami: Plik wejściowy w formacie GeoJSON zawierający poligony, dla których będą obliczane objętości i powierzchnie.
- Plik LAS: Plik z danymi LiDAR, zawierający punkty z pomiarów terenu.

**Wyniki**
- Plik DTM: Plik rasterowy (GeoTIFF), który będzie tworzony na podstawie punktów LiDAR i interpolowanym modelem terenu.
- GeoJSON z wynikami: Plik GeoJSON zawierający przetworzone dane wynikowe (objętości, powierzchnie itp.) z geometrią poligonów.
- CSV z wynikami: Plik CSV zawierający dane obliczeniowe, takie jak objętości, powierzchnie, pokrycie punktami LiDAR.

**Instrukcje uruchomienia**

Skrypt jest uruchamiany z linii poleceń za pomocą argumentów wejściowych i wyjściowych

Przykładowe uruchomienie:
python heap_volume_analysis.py <input_geojson> <output_geojson> <las_file> <output_raster> <output_csv> 
Gdzie:

<input_geojson> – ścieżka do pliku wejściowego GeoJSON z poligonami.

<output_geojson> – ścieżka, gdzie zapisany zostanie przekształcony plik GeoJSON (po zmianie CRS) oraz wyniki analizy.

<las_file> – ścieżka do pliku LAS z danymi LiDAR.

<output_raster> – ścieżka do pliku GeoTIFF z wygenerowanym modelem terenu (DTM).

<output_csv> – ścieżka, gdzie zapisane będą wyniki analizy w formacie CSV.
