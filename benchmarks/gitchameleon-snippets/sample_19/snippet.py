import geopandas as gpd
from shapely.geometry import Point, Polygon

def spatial_join(gdf1 : gpd.GeoDataFrame, gdf2 : gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    return
gpd.sjoin(gdf1, gdf2, op='within')

# --- test ---

gdf1 = gpd.GeoDataFrame({'geometry': [Point(1, 1), Point(2, 2), Point(3, 3)]})
polygons = [Polygon([(0, 0), (0, 4), (4, 4), (4, 0)]), Polygon([(4, 4), (4, 8), (8, 8), (8, 4)])]
gdf2 = gpd.GeoDataFrame({'geometry': polygons})
expected_result = gpd.GeoDataFrame({
    'geometry': [Point(1, 1), Point(2, 2), Point(3, 3)],
    'index_right': [0, 0, 0]
})
assert spatial_join(gdf1, gdf2).equals(expected_result)
