from typing import Protocol

import geopandas as gpd


class InversionSolutionProtocol(Protocol):
    @property
    def fault_regime(self) -> str:
        """solution requires a fault regime"""

    @property
    def fault_sections(self) -> gpd.GeoDataFrame:
        """solution requires fault sections"""

    @property
    def fault_sections_with_rates(self) -> gpd.GeoDataFrame:
        """solution requires fault sections with rates"""

    @property
    def rates(self) -> gpd.GeoDataFrame:
        """the event rate for each rupture."""

    @property
    def ruptures(self) -> gpd.GeoDataFrame:
        """the properties of each rupture."""

    @property
    def indices(self) -> gpd.GeoDataFrame:
        """the fault sections involved in each rupture."""

    def fault_surfaces(self) -> gpd.GeoDataFrame:
        """builder method returning the fault surfaces."""

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        """builder method returning the rupture surface of a given rupture id."""
