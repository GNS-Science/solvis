import unittest
import os
import pathlib

# from pyproj import Transformer
import pyvista as pv
import numpy as np

# from nzshm_common.location.location import location_by_id
# from solvis import InversionSolution

class TestPyvistaDistances(unittest.TestCase):
    def test_basic_0_rake_90(self):

            mesh0 = pv.PolyData([0,0,0])

            p0 = [0, 1, 0] # 1st top-trace point
            p1 = [0, 2, 0] # 2nd top-trace point
            p2 = [1, 1, 10] # 1st botton trace point
            p3 = [1, 2, 10] # 2nd bottom trace point

            mesh1 = pv.PolyData([p0, p1, p2, p3])
            closest_cells, closest_points = mesh1.find_closest_cell(mesh0.points, return_closest_point=True)
            d_exact = np.linalg.norm(mesh0.points - closest_points, axis=1)

            print(closest_cells)
            print(closest_points)
            print(d_exact)
            assert closest_cells == [0]
            assert d_exact[0] == 1

    def test_basic_1_further_at_depth(self):
            mesh0 = pv.PolyData([0,0,0])

            p0 = [0, 2, 0] # 1st top-trace point
            p1 = [0, 3, 0] # 2nd top-trace point
            p2 = [2, 2, 10] # 1st botton trace point
            p3 = [2, 3, 10] # 2nd bottom trace point

            mesh1 = pv.PolyData([p0, p1, p2, p3])
            closest_cells, closest_points = mesh1.find_closest_cell(mesh0.points, return_closest_point=True)
            d_exact = np.linalg.norm(mesh0.points - closest_points, axis=1)

            print(closest_cells)
            print(closest_points)
            print(d_exact)
            assert closest_cells == [0]
            assert d_exact[0] == 2.0


    def test_basic_2_closer_at_depth(self):
            mesh0 = pv.PolyData([0,0,0])

            p0 = [10, 2, 0] # 1st top-trace point
            p1 = [10, 3, 0] # 2nd top-trace point
            p2 = [0, 2, 5] # 1st botton trace point
            p3 = [0, 3, 5] # 2nd bottom trace point

            mesh1 = pv.PolyData([p0, p1, p2, p3])
            closest_cells, closest_points = mesh1.find_closest_cell(mesh0.points, return_closest_point=True)
            d_exact = np.linalg.norm(mesh0.points - closest_points, axis=1)

            print(closest_cells)
            print(closest_points)
            print(d_exact)
            assert closest_cells == [2]
            assert d_exact[0] > 5




    # def test_basic_2(self):
    #         p0 = g3d.Point(10, 1, 0) # 1st top-trace point
    #         p1 = g3d.Point(10, 10, 0) # 2nd top-trace point
    #         p2 = g3d.Point(5, 1, 10) # closer at depth
    #         plane = g3d.Plane(p0, p1, p2)
    #         assert plane.distance(g3d.origin()) < 10.0

    # @unittest.skip('this shows us it ain\'t gonna work using a plane')
    # def test_basic_3(self):
    #         p0 = g3d.Point(10, 1, 0) # 1st top-trace point
    #         p1 = g3d.Point(10, 10, 0) # 2nd top-trace point
    #         p2 = g3d.Point(15, 1, 10) # further at depth = closer above ground == no good
    #         plane = g3d.Plane(p0, p1, p2)
    #         assert plane.distance(g3d.origin()) > 10.0

    # @unittest.skip('this does\'t help/work')
    # def test_can_we_get_intersection_of_rect_and_plane(self):
    #         p0 = g3d.Point(10, 1, 0) # 1st top-trace point
    #         p1 = g3d.Point(10, 10, 0) # 2nd top-trace point
    #         p2 = g3d.Point(10.000333, 1, 10) # further at depth = closer above ground == no good

    #         plane = g3d.Plane(p0, p1, p2)
    #         rect = g3d.Parallelogram(p0, g3d.Vector(p0, p1), g3d.Vector(p0, p2))

    #         plane_rect = plane.intersection(rect)
    #         print( plane_rect)

    #         print(plane.distance(g3d.origin()))
    #         print(g3d.origin().distance(plane))
    #         assert 0




def main():
    #This posp up a matplotlib window showing nothimg :(
        r = g3d.Renderer(backend='matplotlib')
        p0 = g3d.Point(0,0,0)
        p1 = g3d.Point(0,1,0)
        p2 = g3d.Point(0,0,1)
        p = g3d.Plane(p0, p1, p2)
        r.add((p, 'b', 1))

        b = g3d.Circle(g3d.origin(),g3d.y_unit_vector(),10,20)
        a = g3d.Circle(g3d.origin(),g3d.x_unit_vector(),10,20)
        c = g3d.Circle(g3d.origin(),g3d.z_unit_vector(),10,20)
        r.add((a,'g',3), 10)
        r.add((b,'b',3), 10)
        r.add((c,'r',3), 10)

        r.show()


if __name__ == '__main__':
    main()