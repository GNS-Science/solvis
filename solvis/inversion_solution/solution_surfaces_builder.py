import logging
import time

import geopandas as gpd
from shapely import get_coordinates
from shapely.geometry import LineString, Point

from solvis.geometry import create_surface, dip_direction

from .typing import InversionSolutionProtocol

log = logging.getLogger(__name__)


def create_subduction_section_surface(section: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    def calc_dip_dir(section: gpd.GeoDataFrame) -> float:
        assert type(section.geometry) == LineString
        flat_geom = LineString(get_coordinates(section.geometry))

        point_a = Point(reversed(flat_geom.coords[0]))
        point_b = Point(reversed(flat_geom.coords[-1]))

        return dip_direction(point_a, point_b)

    return create_surface(
        section["geometry"], calc_dip_dir(section), section["DipDeg"], section["UpDepth"], section["LowDepth"]
    )


def create_crustal_section_surface(section: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    return create_surface(
        section["geometry"], section["DipDir"], section["DipDeg"], section["UpDepth"], section["LowDepth"]
    )


class SolutionSurfacesBuilder:
    def __init__(self, solution: InversionSolutionProtocol) -> None:
        self._solution = solution

    def fault_surfaces(self) -> gpd.GeoDataFrame:
        """
        Calculate the geometry of the solution fault surfaces projected onto the earth surface.

        Returns:
            a gpd.GeoDataFrame
        """
        tic = time.perf_counter()
        new_geometry_df = self._solution.fault_sections.copy()
        toc = time.perf_counter()
        log.debug('time to load fault_sections: %2.3f seconds' % (toc - tic))

        if self._solution.fault_regime == 'SUBDUCTION':
            return new_geometry_df.set_geometry(
                [create_subduction_section_surface(section) for i, section in new_geometry_df.iterrows()]
            )
        if self._solution.fault_regime == 'CRUSTAL':
            return new_geometry_df.set_geometry(
                [create_crustal_section_surface(section) for i, section in new_geometry_df.iterrows()]
            )

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        """
        Calculate the geometry of the rupture fault surfaces projected onto the earth surface.

        Parameters:
            rupture_id: ID of the rupture

        Returns:
            a gpd.GeoDataFrame
        """
        tic = time.perf_counter()
        df0 = self._solution.fault_sections_with_rupture_rates.copy()
        toc = time.perf_counter()
        log.debug('time to load fault_sections_with_rupture_rates: %2.3f seconds' % (toc - tic))
        rupt = df0[df0["Rupture Index"] == rupture_id]
        if self._solution.fault_regime == 'SUBDUCTION':
            return rupt.set_geometry([create_subduction_section_surface(section) for i, section in rupt.iterrows()])
        if self._solution.fault_regime == 'CRUSTAL':
            return rupt.set_geometry([create_crustal_section_surface(section) for i, section in rupt.iterrows()])
