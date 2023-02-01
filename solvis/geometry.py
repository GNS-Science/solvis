import math
from functools import partial

from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

EARTH_RADIUS_MEAN = 6371.0072


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


def create_surface(trace: LineString, dip_dir: float, dip_deg: float, upper_depth: float, lower_depth: float):
    """
    Creates a projection of the fault surface onto the geodetic sphere.
    :param trace: the fault trace
    :param dip_dir: the azimuth of the dip
    :param dip_deg: the dip
    :param upper_depth: the height of the upper edge of the fault in km
    :param lower_depth: the height of the lower edge of the fault in km
    :return: a Polygon
    """
    depth = lower_depth - upper_depth
    width = depth / math.tan(math.radians(dip_deg))
    transformation = partial(translate_horizontally, dip_dir, width)
    bottom_edge = reverse_geom(transform(transformation, trace))
    return Polygon([x for x in trace.coords] + [x for x in bottom_edge.coords])


def bearing(point_a: Point, point_b: Point) -> float:
    """
    Computes the bearing in degrees from the point A(a1,a2) to
    the point B(b1,b2).

    Note that A and B are given assuming a flat surface projection
    """
    TWOPI = 6.2831853071795865
    RAD2DEG = 57.2957795130823209

    if point_a == point_b:
        raise ValueError("cannot compute bearing, points A & B are identical")

    # get the arc tangent (measured in radians) of y/x.
    theta: float = math.atan2(point_b.x - point_a.x, point_a.y - point_b.y)

    if theta < 0.0:
        theta += TWOPI
    return RAD2DEG * theta


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
