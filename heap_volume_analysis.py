import geopandas as gpd
import numpy as np
from scipy.interpolate import griddata
import rasterio
from rasterio.transform import from_origin
import pyproj
from shapely import vectorized
import laspy
import pandas as pd
import argparse

def transform_polygons(input_file: str, output_file: str, target_crs: str = "EPSG:2180"):
    """
    Transforms polygons from the input GeoJSON file to the specified CRS and saves the result.
    
    Args:
        input_file (str): Path to the input GeoJSON file.
        output_file (str): Path to save the transformed GeoJSON file.
        target_crs (str): Target CRS in EPSG code. Defaults to 'EPSG:2180'.
    """
    gdf = gpd.read_file(input_file)
    if gdf.crs is None:
        raise ValueError("Expected CRS for input file: EPSG:4326")
    gdf_transformed = gdf.to_crs(target_crs)
    gdf_transformed.to_file(output_file, driver="GeoJSON")
    print(f"Transformation completed. Results saved to {output_file}")
    return gdf


def process_lidar_to_raster(las_file: str, output_raster: str, grid_size: float = 0.1, resolution: float = 0.1):
    """
    Extracts terrain points from a LAS file, creates a terrain model by interpolating the points onto a grid, 
    and saves the model as a GeoTIFF file.
    
    Args:
        las_file (str): Path to the LAS file.
        output_raster (str): Path to save the raster file.
        grid_size (float): The resolution of the grid.
        resolution (float): Resolution of the raster grid.
    """
    las = laspy.read(las_file)
    if hasattr(las, 'pred_class'):
        terrain_mask = las.pred_class == 0
        x, y, z = las.x[terrain_mask], las.y[terrain_mask], las.z[terrain_mask]
        if len(x) == 0:
            raise ValueError("No terrain points found (pred_class == 0).")
    else:
        raise ValueError("Missing 'pred_class' in point cloud data.")
    if len(x) == 0 or len(y) == 0 or len(z) == 0:
        raise ValueError("No terrain points to model. Check LiDAR data.")
    print(f"Performing cubic interpolation...")
    x_min, x_max = np.min(x), np.max(x)
    y_min, y_max = np.min(y), np.max(y)
    grid_x, grid_y = np.meshgrid(np.arange(x_min, x_max, grid_size),
                                 np.arange(y_min, y_max, grid_size))
    grid_z = griddata((x, y), z, (grid_x, grid_y), method='cubic')
    x_min, x_max = np.min(grid_x), np.max(grid_x)
    y_min, y_max = np.min(grid_y), np.max(grid_y)
    transform = from_origin(x_min, y_max, resolution, resolution)
    crs = pyproj.CRS("EPSG:2180")
    grid_z = np.flipud(grid_z) 
    with rasterio.open(
        output_raster, 'w', driver='GTiff',
        height=grid_z.shape[0], width=grid_z.shape[1],
        count=1, dtype=grid_z.dtype,
        crs=crs.to_wkt(),
        transform=transform
    ) as dst:
        dst.write(grid_z, 1)

    print(f"Terrain model saved to {output_raster}")

def extract_polygon_points(las_file: str, polygon):
    """
    Extracts LiDAR points within a polygon from a LAS file.
    
    Args:
        las_file (str): Path to the LAS file.
        polygon (shapely.geometry.Polygon): Polygon geometry to filter points by.
    
    Returns:
        np.ndarray: Filtered LiDAR points (x, y, z).
    """
    las = laspy.read(las_file)
    x, y, z = las.x, las.y, las.z
    mask = vectorized.contains(polygon, x, y)
    filtered_points = np.vstack((x[mask], y[mask], z[mask])).T
    return filtered_points

def get_dtm_values(raster_file: str, points: np.ndarray):
    """
    Extracts DTM values for a set of points from a raster file.
    
    Args:
        raster_file (str): Path to the DTM raster file.
        points (np.ndarray): Array of points for which DTM values are to be extracted.
    
    Returns:
        np.ndarray: Array of DTM values corresponding to the points.
    """
    print("Getting DTM values ​​for points...")
    with rasterio.open(raster_file) as src:
        coords = [(pt[0], pt[1]) for pt in points]
        dtm_values = list(src.sample(coords))
        dtm_values = np.array(dtm_values).flatten()
    print("DTM values ​​have been downloaded.")
    return dtm_values

def load_geojson(geojson_path: str):
    """
    Loads a GeoJSON file into a GeoDataFrame.
    
    Args:
        geojson_path (str): Path to the GeoJSON file.
    
    Returns:
        geopandas.GeoDataFrame: Loaded GeoDataFrame.
    """
    gdf = gpd.read_file(geojson_path)
    print(f"Loaded GeoJSON file with columns: {gdf.columns}")
    return gdf

def calculate_volume_and_area(las_file: str, geojson_path: str, raster_file: str, output_csv: str):   
    """
    Calculates the volume, surface area, and coverage for polygons in a GeoJSON file 
    based on LiDAR points and DTM values.
    
    Args:
        las_file (str): Path to the LAS file containing LiDAR data.
        geojson_path (str): Path to the GeoJSON file containing polygons.
        raster_file (str): Path to the DTM raster file.
        output_csv (str): Path to save the CSV file with results.
        output_geojson (str): Path to save the GeoJSON file with results.
    """
    gdf = load_geojson(geojson_path)
    results = []
    for _, row in gdf.iterrows():
        polygon = row['geometry']
        pred_id = row['pred_ID']
        print(f"Processing heap ID: {pred_id}...")
        filtered_points = extract_polygon_points(las_file, polygon)
        if len(filtered_points) == 0:
            print(f"No LiDAR points found for heap ID: {pred_id}. Skipping...")
            continue
        dtm_values = get_dtm_values(raster_file, filtered_points)
        height_diff = filtered_points[:, 2] - dtm_values
        above_dtm_mask = height_diff > 0
        volume = np.sum(height_diff[above_dtm_mask])  
        total_area = len(filtered_points)             
        surface_area = np.sum(above_dtm_mask)         
        coverage = (surface_area / total_area) * 100 if total_area > 0 else 0
        results.append({
            "pred_ID": pred_id,
            "volume_m3": volume,
            "surface_3D_m2": total_area,
            "coverage_percent": coverage,
            "geometry": polygon
        })
        print(f"Heap ID: {pred_id}")
        print(f"Volume: {volume:.2f} m³")
        print(f"Surface Area: {total_area:.2f} m²")
        print(f"Point Coverage: {coverage:.2f}%")
        print("-" * 40)

    df = pd.DataFrame(results)
    df.drop(columns=["geometry"], inplace=True)
    df.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"Results saved to {output_csv}")
    gdf_results = gpd.GeoDataFrame(results, geometry="geometry", crs="EPSG:2180")
    gdf_results.to_file(geojson_path, driver="GeoJSON")
    print(f"Results saved to {geojson_path}")

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Process LiDAR data and calculate volumes and areas for polygons.")
    parser.add_argument('input_geojson', help="Path to the input GeoJSON file")
    parser.add_argument('output_geojson', help="Path to save the transformed GeoJSON file")
    parser.add_argument('las_file', help="Path to the LAS file")
    parser.add_argument('output_raster', help="Path to save the DTM raster file")
    parser.add_argument('output_csv', help="Path to save the CSV file with results")    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    transform_polygons(args.input_geojson, args.output_geojson)
    process_lidar_to_raster(args.las_file, args.output_raster, grid_size = 0.1, resolution = 0.1)
    calculate_volume_and_area(args.las_file, args.output_geojson, args.output_raster, args.output_csv)
