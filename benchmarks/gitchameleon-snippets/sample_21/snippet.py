import geopandas as gpd
from shapely.geometry import box

def perform_union(gdf: gpd.GeoDataFrame) -> gpd.GeoSeries:
    return
gdf.geometry.cascaded_union

# --- test ---

gdf = gpd.GeoDataFrame({'geometry': [box(0, 0, 2, 5), box(0, 0, 2, 1)]})
from shapely.geometry import Polygon
coords = [
    (2, 0),
    (0, 0),
    (0, 1),
    (0, 5),
    (2, 5),
    (2, 1),
    (2, 0)
]
expected_result = Polygon(coords)
assert perform_union(gdf) == expected_result
