import math
from functools import partial

from shapely.geometry import LineString, Polygon
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
