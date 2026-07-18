import geopandas as gpd
from shapely.geometry import Point, Polygon, box

def spatial_query(gdf:gpd.GeoDataFrame, other:gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    combined_geometry = other.unary_union
    return
gdf.sindex.query(combined_geometry)

# --- test ---

gdf = gpd.GeoDataFrame({'geometry': [Point(1, 2)]})
other = gpd.GeoDataFrame({'geometry': [Point(1,1)]})
result = spatial_query(gdf, other)
expected_result = []
assert (result == expected_result).all()
