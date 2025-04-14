"""A module providing geojson support functions."""
# flake8: noqa

import logging
from functools import lru_cache
from typing import Dict, Iterator, Optional, Tuple

import geopandas as gpd
import shapely
from nzshm_common.location import location_by_id

from solvis import geometry

log = logging.getLogger(__name__)


@lru_cache
def get_location_polygon(radius_km, lon, lat):
    return geometry.circle_polygon(radius_m=radius_km * 1000, lon=lon, lat=lat)


def location_features(locations: Tuple[str], radius_km: int, style: Optional[Dict]) -> Iterator[Dict]:

    style = style or dict(
        stroke_color="lightblue", stroke_width=1, stroke_opacity=1.0, fill_color='lightblue', fill_opacity=0.7
    )

    for loc in locations:
        log.debug(f'LOC {loc}')
        item = location_by_id(loc)
        # polygon = solvis.circle_polygon(radius_km * 1000, lat=item.get('latitude'), lon=item.get('longitude'))
        polygon = get_location_polygon(radius_km, lat=item.get('latitude'), lon=item.get('longitude'))
        feature = dict(
            id=loc,
            type="Feature",
            geometry=shapely.geometry.mapping(polygon),
            properties={
                "title": item.get('name'),
                "stroke-color": style.get('stroke_color'),
                "stroke-opacity": style.get('stroke_opacity'),
                "stroke-width": style.get('stroke_width'),
                "fill-color": style.get('fill_color'),
                "fill-opacity": style.get('fill_opacity'),
            },
        )
        yield feature


def location_features_geojson(locations: Tuple[str], radius_km: int, style: Optional[Dict] = None) -> Dict:
    return dict(type="FeatureCollection", features=list(location_features(locations, radius_km, style)))
