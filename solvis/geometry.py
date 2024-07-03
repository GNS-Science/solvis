"""
Functions for working with Shapely geometries.

These functions require [Shapely](https://shapely.readthedocs.io/en/stable/index.html) to be installed.
"""

import logging
import math
from functools import partial
from typing import Tuple, Union

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


def reverse_geom(geom: BaseGeometry) -> BaseGeometry:
    """
    Reverse the order of the points of a geometry object.

    Parameters:
        geom: A geometry object

    Returns:
        A copy of the geometry with the order of the points reversed
    """

    def _reverse(x, y):
        return x[::-1], y[::-1]

    return transform(_reverse, geom)


def translate_horizontally(azimuth: float, distance: float, lon: float, lat: float) -> Tuple[float, float]:
    """
    Taking a `lat, lon` location as the origin, create a new location at the specified distance and azimuth on a sphere.

    Written so that it can be curried and used with
    [`shapely.ops.transform`](https://shapely.readthedocs.io/en/stable/manual.html#shapely.ops.transform).

    From Java:
    [`org.opensha.commons.geo.LocationUtils.location()`](https://github.com/opensha/opensha/blob/master/src/main/java/org/opensha/commons/geo/LocationUtils.java)

    Parameters:
        azimuth: a horizontal angle in degrees
        distance: distance in km
        lon: longitude in degrees. Note that longitude comes before latitude
        lat: latitude in degrees

    Returns:
        a `(lon, lat)` tuple of the new location
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
) -> Polygon:
    """
    Creates a projection of the fault surface onto the geodetic sphere.

    Parameters:
        trace: the fault trace
        dip_dir: the azimuth of the dip in degrees
        dip_deg: the dip (inclination) in degrees
        upper_depth: the height of the upper edge of the fault in kilometres
        lower_depth: the height of the lower edge of the fault in kilometres

    Returns:
        the projection for the fault surface

    Examples:
        ```py
        >>> from shapely.geometry import LineString
        >>> from solvis.geometry import create_surface
        >>> trace = LineString([[178.017654, -38.662334], [178.017654, -38.762334]])
        >>> upper, lower = 39.5, 53.5
        >>> dip = 28.667
        >>> create_surface(trace, 180.0, dip, upper, lower)
        <POLYGON ((178.018 -38.662, 178.018 -38.762, 178.018 -38.993, 178.018 -38.89...>
        ```
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
    Computes the bearing in degrees from one Point to another Point.

    Points are treated as `(lat, lon)` pairs of decimal degrees.

    Parameters:
        point_a: the first point
        point_b: the second point

    Returns:
        A bearing in degrees

    Raises:
        ValueError: If the points are identical, they cannot be compared.

    Examples:
        ```py
        >>> from shapely.geometry import Point
        >>> from solvis.geometry import bearing
        >>> loc_chc = Point(-43.53, 172.63)
        >>> loc_akl = Point(-41.3, 174.78)
        >>> bearing(loc_chc, loc_akl)
        36.17316361836124
        >>> bearing(loc_akl, loc_chc)
        214.72263050205407
        ```
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
"""An alias for the [`bearing`][solvis.geometry.bearing] function."""


def refine_dip_direction(point_a: Point, point_b: Point, original_dip_direction: float) -> float:
    """
    Compute the dip direction given two points along strike.

    Rather than obey the right-hand rule for dip direction, this function will return a dip
    oriented in the same direction as the `original_dip_direction`.

    This is useful when re-calculating the dip direction of OpenSHA fault subsections from the
    fault surface trace, but keeping the orientation (i.e. resolving the 180 degree ambiguity
    when not obeying the right-hand rule).

    Parameters:
        point_a: the first point
        point_b: the second point
        original_dip_direction: the original dip direction in decimal degrees

    Returns:
        The refined dip direction in decimal degrees
    """
    original_dip_direction = resolve_azimuth(original_dip_direction)

    # log.info(f"original dir_dir: {original_direction}")
    dip_dir = dip_direction(point_a, point_b)

    # log.info(f"calculated dip_dir: {dip_dir}")
    if abs(original_dip_direction - dip_dir) > 45:
        dip_dir -= 180
        # log.info(f"refined dip_dir is now {dip_dir}")
    return dip_dir + 360 if dip_dir < 0 else dip_dir


def resolve_azimuth(az: float) -> float:
    """
    Resolve an azimuth angle to be between -360° and 360°.

    Parameters:
        az: the azimuth angle in decimal degrees

    Returns:
        The resolved azimuth angle in decimal degrees
    """
    return math.copysign(az % 360.0, az)


def dip_direction(point_a: Point, point_b: Point) -> float:
    """
    Computes the dip direction for a strike from Point A to Point B.

    Parameters:
        point_a: the first point
        point_b: the second point

    Returns:
        the dip direction in degrees
    """
    dip_dir = strike(point_a, point_b) + 90
    return dip_dir + 360 if dip_dir < 0 else dip_dir


def circle_polygon(radius_m: float, lat: float, lon: float) -> Polygon:
    """
    Creates a circular `Polygon` at a given radius in metres around the `lat, lon` coordinate.

    Calculation based on:
    [https://gis.stackexchange.com/a/359748](https://gis.stackexchange.com/a/359748),<br/>
    updated with:
    [https://pyproj4.github.io/pyproj/stable/gotchas.html#upgrading-to-pyproj-2-from-pyproj-1](https://pyproj4.github.io/pyproj/stable/gotchas.html#upgrading-to-pyproj-2-from-pyproj-1)

    This process transforms from an azimuthal equidistant projection (AEQD) to WGS 84 geodetic
    coordinate system when calculating the circle.

    The number of points in the polygon is determined by
    [shapely.buffer](https://shapely.readthedocs.io/en/stable/reference/shapely.buffer.html) defaults.

    Parameters:
        radius_m: the radius in metres
        lat: the latitude in degrees azimuth of the dip
        lon: the longitude in degrees azimuth of the dip

    Returns:
        A `Polygon` encompassing the buffer zone around the `lat, lon` coordinate at the specified radius.

    Examples:
        200km circle around Gisborne:
        ```py
        >>> from solvis.geometry import circle_polygon
        >>> gis_extent = circle_polygon(2e5, -38.662334, 178.017654)
        >>> gis_extent
        <POLYGON ((180.321 -38.64, 180.315 -38.816, 180.288 -38.991, 180.238 -39.164...>
        >>> gis_extent.bounds
        (175.7146696515645, -40.46097721183747, 180.32063834843552, -36.86369078816255)
        >>> len(gis_extent.exterior.coords)
        65
        ```
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


def section_distance(
    transformer: Transformer,
    surface_geometry: Union[Polygon, LineString],
    upper_depth: float,
    lower_depth: float,
) -> float:
    """
    Calculate minimum distance from the transformer datum to a surface built from the surface projection of the fault.

    Parameters:
        transformer: typically from WGS84 to azimuthal
        surface_geometry: the surface projection of the fault plane (`Polygon` or `LineString`)
        upper_depth: the upper depth in km
        upper_depth: the lower depth in km

    Returns:
        distance in meters

    Raises:
        ValueError: The `surface_geometry` was of an unsupported type.
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

    closest_cells, closest_points = surface.find_closest_cell(
        origin.points,
        return_closest_point=True,
    )  # type: ignore[misc]
    d_exact = np.linalg.norm(origin.points - closest_points, axis=1)
    return d_exact[0] / 1000
