import geopandas as gpd
from shapely.geometry import Point, Polygon

def spatial_query(gdf:gpd.GeoDataFrame, other:gpd.GeoSeries) -> gpd.GeoDataFrame:
    return
gdf.sindex.query_bulk(other)

# --- test ---

gdf = gpd.GeoDataFrame({'geometry': [Point(1, 1), Point(2, 2), Point(3, 3)]})
other = gpd.GeoSeries([Polygon([(0, 0), (0, 4), (4, 4), (4, 0)])])
result = spatial_query(gdf, other)
import numpy as np
expected_result = np.array([
    [0, 0, 0],
    [0, 1, 2]
])
assert (result == expected_result).all()
