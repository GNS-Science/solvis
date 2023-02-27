import geopandas as gpd
import pandas as pd
from shapely import get_coordinates
from shapely.geometry import LineString, Point

from solvis.geometry import create_surface, dip_direction


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
    def __init__(
        self, fault_regime: str, fault_sections: pd.DataFrame, fault_sections_with_rates: pd.DataFrame
    ) -> None:
        self._fault_regime = fault_regime  # TODO make this an ENUM ?
        self._fault_sections = fault_sections
        self._fault_sections_with_rates = fault_sections_with_rates

    def fault_surfaces(self) -> gpd.GeoDataFrame:
        """
        Calculate the geometry of the solution fault surfaces projected onto the earth surface.

        :param refine_dip_dir: option to override the dip_directon supplied, only applies to CRUSTAL
        :return: a gpd.GeoDataFrame
        """
        if self._fault_regime == 'SUBDUCTION':
            return self._fault_sections.set_geometry(
                [create_subduction_section_surface(section) for i, section in self._fault_sections.iterrows()]
            )
        if self._fault_regime == 'CRUSTAL':
            return self._fault_sections.set_geometry(
                [create_crustal_section_surface(section) for i, section in self._fault_sections.iterrows()]
            )

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        """
        Calculate the geometry of the rupture fault surfaces projected onto the earth surface.

        :param rupture_id: ID of the rupture
        :return: a gpd.GeoDataFrame
        """
        df0 = self._fault_sections_with_rates
        rupt = df0[df0["Rupture Index"] == rupture_id]
        if self._fault_regime == 'SUBDUCTION':
            return rupt.set_geometry([create_subduction_section_surface(section) for i, section in rupt.iterrows()])
        if self._fault_regime == 'CRUSTAL':
            return rupt.set_geometry([create_crustal_section_surface(section) for i, section in rupt.iterrows()])
