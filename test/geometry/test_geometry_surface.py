from shapely.geometry import LineString

from solvis.geometry import create_surface, fault_surface_3d, fault_surface_projection


def test_legacy_create_surface():
    trace = LineString([[178.017654, -38.662334], [178.017654, -38.762334]])
    upper, lower = 39.5, 53.5
    dip = 28.667
    surface = create_surface(trace, 180.0, dip, upper, lower)

    print(surface)
    assert (
        str(surface) == "POLYGON ((178.017654 -38.662334, 178.017654 -38.762334, 178.017654 -38.992618750843654,"
        " 178.017654 -38.89261875084365, 178.017654 -38.662334))"
    )


def test_fault_surface_3d_has_3_dimensions():
    trace = LineString([[178.017654, -38.662334], [178.017654, -38.762334]])
    upper, lower = 39.5, 53.5
    dip = 28.667
    surface = fault_surface_3d(trace, 180.0, dip, upper, lower)

    print(surface)
    assert (
        str(surface) == "POLYGON Z ((178.017654 -38.662334 39.5, 178.017654 -38.762334 39.5,"
        " 178.017654 -38.992618750843654 53.5, 178.017654 -38.89261875084365 53.5, 178.017654 -38.662334 39.5))"
    )


def test_fault_surface_projection_vertical_is_linestring():
    trace = LineString([[178.017654, -38.662334], [178.017654, -38.762334]])
    upper, lower = 39.5, 53.5
    dip = 90
    surface = fault_surface_projection(trace, 180.0, dip, upper, lower)

    print(surface)
    assert str(surface) == "LINESTRING (178.017654 -38.662334, 178.017654 -38.762334)"


def test_fault_surface_projection_non_vertical_is_polygon():
    trace = LineString([[178.017654, -38.662334], [178.017654, -38.762334]])
    upper, lower = 39.5, 53.5
    dip = 28.667
    assert (
        str(fault_surface_projection(trace, 180.0, dip, upper, lower))
        == "POLYGON ((178.017654 -38.662334, 178.017654 -38.762334, 178.017654"
        " -38.992618750843654, 178.017654 -38.89261875084365, 178.017654 -38.662334))"
    )
