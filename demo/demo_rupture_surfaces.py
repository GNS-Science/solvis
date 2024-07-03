#! python demo.py

import os
import json

from pathlib import PurePath

# from shapely.geometry import Polygon
import solvis

CRU_ARCHIVE = "test/fixtures/ModularAlpineVernonInversionSolution.zip"
HIK_ARCHIVE = "test/fixtures/AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip"
PUY_ARCHIVE = "test/fixtures/PuysegurInversionSolution-QXV0b21hdGlvblRhc2s6MTExMDA1.zip"

PWD = PurePath(os.path.realpath(__file__)).parent.parent


def puy_above_rate(solution, rate=2e-4):
    filename = PurePath(PWD, PUY_ARCHIVE)
    solution = solvis.InversionSolution().from_archive(str(filename))
    ids = solvis.rupt_ids_above_rate(solution, rate)
    return ids
    # print(ids)


def crustal_above_rate(solution, rate=2e-4):
    ids = solvis.rupt_ids_above_rate(solution, rate)
    return ids


def rupture_surfaces(solution, rupt_ids, **kwargs):
    for rupture_id in rupt_ids:
        surface = solution.rupture_surface(rupture_id)
        yield json.loads(surface.to_json(**kwargs))


if __name__ == "__main__":

    RATE = 2e-4
    # puy_above_rate(rate=RATE)

    filename = PurePath(PWD, CRU_ARCHIVE)
    solution = solvis.InversionSolution().from_archive(str(filename))
    # surfaces = list(rupture_surfaces(solution, crustal_above_rate(solution, rate=2e-6)))

    print(solution.fault_surfaces().to_json(indent=2))

    # # print(f"Demo 0")
    # # print("=========")
    # rupt_ids = solvis.rupt_ids_above_rate(solution, RATE)
    # surfaces = list(rupture_surfaces(solution, rupt_ids))
    # print(json.dumps(surfaces, indent=2))
    # # print("Done")
