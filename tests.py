import unittest
from unittest.mock import patch, MagicMock, ANY
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
from dtm import *

class TestDTMFunctions(unittest.TestCase):
    @patch('geopandas.read_file')
    def test_transform_polygons(self, mock_read_file):
        """Test reprojecting polygons to a different CRS."""
        mock_gdf = MagicMock(spec=gpd.GeoDataFrame)
        mock_gdf.crs = "EPSG:4326"
        mock_gdf.to_crs.return_value = mock_gdf
        mock_read_file.return_value = mock_gdf
        result = transform_polygons('input.geojson', 'output.geojson', 'EPSG:2180')
        mock_gdf.to_crs.assert_called_with('EPSG:2180')
        self.assertEqual(result, mock_gdf)

    @patch('laspy.read')
    @patch('rasterio.open')
    def test_process_lidar_to_raster(self, mock_rasterio_open, mock_laspy_read):
        """Test LiDAR data processing and raster creation."""
        mock_las = MagicMock()
        mock_las.x = np.array([1, 2, 3, 4])
        mock_las.y = np.array([1, 3, 1, 3])
        mock_las.z = np.array([1, 2, 3, 4])
        mock_las.pred_class = np.array([0, 0, 0, 0])  
        mock_laspy_read.return_value = mock_las
        mock_raster = MagicMock()
        mock_rasterio_open.return_value.__enter__.return_value = mock_raster
        process_lidar_to_raster('input.las', 'output.tif')
        mock_rasterio_open.assert_called_with('output.tif', 'w', driver='GTiff', height=ANY,
        width=ANY, count=1, dtype=ANY, crs=ANY, transform=ANY)

    @patch('laspy.read')
    def test_extract_polygon_points(self, mock_laspy_read):
        """Test point extraction within a given polygon."""
        mock_las = MagicMock()
        mock_las.x = np.array([1, 2, 3])
        mock_las.y = np.array([1, 2, 3])
        mock_las.z = np.array([1, 2, 3])
        mock_las.pred_class = np.array([0, 0, 0]) 
        mock_laspy_read.return_value = mock_las
        polygon = Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]) 
        result = extract_polygon_points('input.las', polygon)
        self.assertEqual(result.shape[0], 3)  
        self.assertTrue(np.array_equal(result[:, 0], [1, 2, 3]))

    @patch('rasterio.open')
    def test_get_dtm_values(self, mock_rasterio_open):
        """Test extracting DTM values for given points."""
        mock_src = MagicMock()
        mock_src.sample.return_value = [(1.0), (2.0), (3.0)]  
        mock_rasterio_open.return_value.__enter__.return_value = mock_src
        points = np.array([[1, 1], [2, 2], [3, 3]])  
        dtm_values = get_dtm_values('dtm.tif', points)
        self.assertEqual(len(dtm_values), 3)  
        self.assertEqual(dtm_values[0], 1.0)

    @patch('geopandas.read_file')
    @patch('laspy.read')
    @patch('rasterio.open')
    def test_calculate_volume_and_area(self, mock_rasterio_open, mock_laspy_read, mock_gpd_read_file):
        """Test volume and area calculation for polygon with DTM and LiDAR data."""
        mock_gdf = MagicMock(spec=gpd.GeoDataFrame)
        mock_gdf.iterrows.return_value = iter([(0, {"geometry": Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]), "pred_ID": 1})])
        mock_gpd_read_file.return_value = mock_gdf
        mock_las = MagicMock()
        mock_las.x = np.array([1, 2, 1])
        mock_las.y = np.array([1, 1, 2])
        mock_las.z = np.array([5, 6, 7])
        mock_las.pred_class = np.array([0, 0, 0])
        mock_laspy_read.return_value = mock_las
        mock_src = MagicMock()
        mock_src.sample.return_value = [(1.0), (2.0), (3.0)]
        mock_rasterio_open.return_value.__enter__.return_value = mock_src
        calculate_volume_and_area('input.las', 'input.geojson', 'dtm.tif', 'output.csv')
        mock_gpd_read_file.assert_called_with('input.geojson')
        mock_rasterio_open.assert_called_with('dtm.tif')

if __name__ == '__main__':
    unittest.main()
