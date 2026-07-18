import geopandas as gpd
def create_geoseries(x: list[int], y: list[int]) -> gpd.GeoSeries:
    return
gpd.GeoSeries.from_xy(x, y)

# --- test ---

from shapely.geometry import Point
x, y = [1, 2], [3, 4]
expected_result = gpd.GeoSeries([Point(1, 3), Point(2, 4)])
assert list(create_geoseries(x, y)) == list(expected_result)
