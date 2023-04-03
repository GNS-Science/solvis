import logging
import math
from functools import partial
from typing import Union

import numpy as np
from pyproj import Transformer
from shapely import get_coordinates
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

try:
    import pyvista as pv
except ImportError:
    print("WARNING: geometry.section_distance() uses the optional dependency pyvista.")


EARTH_RADIUS_MEAN = 6371.0072

log = logging.getLogger(__name__)


def reverse_geom(geom: BaseGeometry):
    """
    Reverse the order of the points of the geometry
    :param geom: geometry
    :return: a copy of the geometry with the order of the points reversed
    """

    def _reverse(x, y):
        return x[::-1], y[::-1]

    return transform(_reverse, geom)


def translate_horizontally(azimuth: float, distance: float, lon: float, lat: float):
    """
    Takes a lat/lon location as the origin and creates a new location at the specified distance and azimuth on a sphere.
    Written so that it can be curried and used with shapely.ops.transform.
    From Java: org.opensha.commons.geo.LocationUtils.location()
    :param azimuth: a horizontal angle in degrees
    :param distance: distance in km
    :param lon: longitude in degrees. Note that longitude comes before latitude
    :param lat: latitude in degrees
    :return: a tuple lon, lat of the new location
    """
    azimuth = math.radians(azimuth)
    lat = math.radians(lat)
    lon = math.radians(lon)
    sin_lat1 = math.sin(lat)
    cos_lat1 = math.cos(lat)
    ad = distance / EARTH_RADIUS_MEAN
    sin_d = math.sin(ad)
    cos_d = math.cos(ad)
    lat2 = math.asin(sin_lat1 * cos_d + cos_lat1 * sin_d * math.cos(azimuth))
    lon2 = lon + math.atan2(math.sin(azimuth) * sin_d * cos_lat1, cos_d - sin_lat1 * math.sin(lat2))
    return math.degrees(lon2), math.degrees(lat2)


def create_surface(
    trace: LineString, dip_dir: float, dip_deg: float, upper_depth: float, lower_depth: float
) -> Union[LineString, Polygon]:
    """
    Creates a projection of the fault surface onto the geodetic sphere.
    :param trace: the fault trace
    :param dip_dir: the azimuth of the dip
    :param dip_deg: the dip
    :param upper_depth: the height of the upper edge of the fault in km
    :param lower_depth: the height of the lower edge of the fault in km
    :return: a Polygon
    """
    if dip_deg == 90:
        return trace
        # return LineString([x for x in trace.coords])

    trace = LineString(get_coordinates(trace))
    depth = lower_depth - upper_depth
    width = depth / math.tan(math.radians(dip_deg))
    transformation = partial(translate_horizontally, dip_dir, width)

    bottom_edge = reverse_geom(transform(transformation, trace))
    return Polygon([x for x in trace.coords] + [x for x in bottom_edge.coords])


def bearing(point_a: Point, point_b: Point) -> float:
    """
    Computes the bearing in degrees from the point A(a1,a2) to
    the point B(b1,b2). Point(lat, lon))

    Note that A and B are given in decimal.degrees

    :param point_a: the first point
    :param point_b: the second point
    """
    """
    ref:  https://www.igismap.com/formula-to-find-bearing-or-heading-angle-between-two-points-latitude-longitude/

    Formula to find Bearing, when two different points latitude, longitude is given:

    Bearing from point A to B, can be calculated as,

    β = atan2(X,Y),

    where, X and Y are two quantities and can be calculated as:

    X = cos θb * sin ∆L

    Y = cos θa * sin θb – sin θa * cos θb * cos ∆L

    ∆L is ( Longitude B – Longitude A)

    ## sanity check here: https://www.igismap.com/map-tool/bearing-angle
    """

    if point_a == point_b:
        raise ValueError("cannot compute bearing, points A & B are identical")

    # convert to radians ...
    lat_a = point_a.x * math.pi / 180.0
    lon_a = point_a.y * math.pi / 180.0
    lat_b = point_b.x * math.pi / 180.0
    lon_b = point_b.y * math.pi / 180.0
    delta_lon = lon_b - lon_a

    x = math.cos(lat_b) * math.sin(delta_lon)
    y = math.cos(lat_a) * math.sin(lat_b) - math.sin(lat_a) * math.cos(lat_b) * math.cos(delta_lon)

    theta = math.atan2(x, y)
    bearing = theta * 180.0 / math.pi  # from radians
    # print(f'bearing {bearing}')
    return bearing + 360 if bearing < 0 else bearing


strike = bearing  # alias for bearing function


def refine_dip_direction(point_a: Point, point_b: Point, original_direction: float) -> float:
    """
    Compute a dip direction that fits the orientation established by the original_direction.

    :param point_a: the first point
    :param point_b: the second point
    :param original_direction: the original direction in decimal degrees
    """
    # log.info(f"original dir_dir: {original_direction}")
    dip_dir = dip_direction(point_a, point_b)

    # log.info(f"calculated dip_dir: {dip_dir}")
    if abs(original_direction - dip_dir) > 45:
        dip_dir -= 180
        # log.info(f"refined dip_dir is now {dip_dir}")
    return dip_dir + 360 if dip_dir < 0 else dip_dir


def dip_direction(point_a: Point, point_b: Point) -> float:
    """
    Computes the dip_direction in degrees from the points A & B

    :param point_a: the first point
    :param point_b: the second point
    """
    dip_dir = strike(point_a, point_b) + 90
    return dip_dir + 360 if dip_dir < 0 else dip_dir


def circle_polygon(radius_m: int, lat: float, lon: float):
    """
    Creates a cirle polygon at a given radius in metres from the coordinates.

    based on https://gis.stackexchange.com/a/359748
    updated with https://pyproj4.github.io/pyproj/stable/gotchas.html#upgrading-to-pyproj-2-from-pyproj-1

    :param radius_m: the ridues in metres
    :param lat: the latitude in degrees  azimuth of the dip
    :param lon: the longitude in degrees  azimuth of the dip
    :return: a Polygon
    """

    local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(lat, lon)
    wgs84_projection = "+proj=longlat +datum=WGS84 +no_defs"

    transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)
    point_transformed = transformer.transform(lon, lat)

    buffer = Point(point_transformed).buffer(radius_m)

    # Get polygon with lat lon coordinates
    transformer2 = Transformer.from_crs(local_azimuthal_projection, wgs84_projection)
    lons, lats = transformer2.transform(*buffer.exterior.xy)

    # Add 360 to all negative longitudes
    points = []
    for i in range(len(lons)):
        lon = lons[i]
        if lon < 0:
            lon += 360
        points.append(Point(lon, lats[i]))

    return Polygon(points)


def section_distance(transformer, surface_geometry, upper_depth, lower_depth):
    """
    Calculate minimum distance from the transformer datum to a surface built from the surface projection of the fault.

    :param transformer:
    :param surface_geometry: the the surface projection of the fault plane
    :param upper_depth: the upper depth in km
    :param upper_depth: the lower depth in km
    :return: distance in meters
    """
    # print(f'trace coords: {surface_geometry.exterior.coords.xy}')
    if isinstance(surface_geometry, Polygon):
        trace = transformer.transform(*surface_geometry.exterior.coords.xy)
    elif isinstance(surface_geometry, LineString):
        trace = transformer.transform(*surface_geometry.coords.xy)
    else:
        raise ValueError(f'unable to handle geometry: {surface_geometry}')  # pragma: no cover

    # print(f'trace offsets: {trace} (in metres relative to datum)')
    origin = pv.PolyData([0.0, 0.0, 0.0])  # , force_float=False)
    surface = pv.PolyData(
        [
            [float(trace[0][0]), float(trace[1][0]), float(upper_depth * 1000)],  # OK
            [float(trace[0][1]), float(trace[1][1]), float(upper_depth * 1000)],  # OK
            [float(trace[0][0]), float(trace[1][0]), float(lower_depth * 1000)],  # nope, but ok for basic test
            [float(trace[0][1]), float(trace[1][1]), float(lower_depth * 1000)],  # nope
        ]
    )

    closest_cells, closest_points = surface.find_closest_cell(origin.points, return_closest_point=True)
    d_exact = np.linalg.norm(origin.points - closest_points, axis=1)
    return d_exact[0] / 1000
