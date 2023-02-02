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

    Lets us take an example to calculate bearing between the two different points with the formula:

    ∆L is never explained. It's actually = ( Longitude B – Longitude A)

    """

    if point_a == point_b:
        raise ValueError("cannot compute bearing, points A & B are identical")

    # to radians ...
    lat_a = point_a.x * math.pi / 180.0
    lon_a = point_a.y * math.pi / 180.0
    lat_b = point_b.x * math.pi / 180.0
    lon_b = point_b.y * math.pi / 180.0
    delta_lon = lon_b - lon_a

    x = math.cos(lat_b) * math.sin(delta_lon)
    y = math.cos(lat_a) * math.sin(lat_b) - math.sin(lat_a) * math.cos(lat_b) * math.cos(delta_lon)

    theta = math.atan2(x, y)
    return theta * 180.0 / math.pi  # from radians


def bearing_naive(point_a: Point, point_b: Point) -> float:
    """
    Computes the bearing in degrees from the point A(a1,a2) to
    the point B(b1,b2).

    Note that A and B are given assuming a flat surface projection
    :param point_a: the first point
    :param point_b: the second point
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


# def strike(point_a: Point, point_b: Point) -> float:
#     return bearing( point_b, point_a) if point_a.y <= point_b.y else bearing( point_a, point_b)

strike = bearing


def dip_direction(point_a: Point, point_b: Point) -> float:
    """
    Computes the dip_direction in degrees from the points A & B

    Note that A and B are given assuming a flat surface projection

    :param point_a: the first point
    :param point_b: the second point
    """
    dip_dir = strike(point_a, point_b) + 90
    dip_dir = dip_dir + 360 if dip_dir < 0 else dip_dir
    return dip_dir


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
