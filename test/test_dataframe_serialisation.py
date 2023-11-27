#!python3

import os
import pathlib
import tempfile
import unittest
import zipfile

import pandas as pd

import solvis


class TestRates(unittest.TestCase):
    def test_read_rates_csv(self):
        folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        filename = pathlib.PurePath(folder, "fixtures/ModularAlpineVernonInversionSolution.zip")

        rates_df = pd.read_csv(zipfile.Path(str(filename), at='solution/rates.csv').open())

        print("old way")
        print(rates_df)
        print(rates_df.head())

        rates_df2 = pd.read_csv(zipfile.Path(str(filename), at='solution/rates.csv').open(), index_col="Rupture Index")
        print("new way")
        print(rates_df2)
        print(rates_df2.head())

        print("out")
        rate = 1e-6
        rr = rates_df
        out0 = rr[rr['Annual Rate'] > rate]["Rupture Index"].unique()
        print(out0)

        rr = rates_df2
        out1 = rr[rr['Annual Rate'] > rate].index
        assert out0.all() == out1.all()


class TestSerialisation(object):
    def test_write_to_archive_compatible(self, crustal_fixture, archives):

        folder = tempfile.TemporaryDirectory()
        # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        new_path = pathlib.Path(folder.name, 'test_compatible_archive.zip')

        # ref_solution = next(branch_solutions(fslt, archive=archives['CRU']))

        fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
        ref_solution = pathlib.PurePath(fixture_folder, archives['CRU'])

        # assert not new_path.exists()
        # write the file
        crustal_fixture.to_archive(str(new_path), ref_solution, compat=True)
        assert new_path.exists()

    def test_write_read_archive_compatible(self, crustal_fixture, archives):

        folder = tempfile.TemporaryDirectory()
        # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        new_path = pathlib.Path(folder.name, 'test_compatible_archive.zip')

        fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
        ref_solution = pathlib.PurePath(fixture_folder, archives['CRU'])

        crustal_fixture.to_archive(str(new_path), ref_solution, compat=True)
        read_sol = solvis.FaultSystemSolution.from_archive(new_path)

        print(read_sol.rupture_rates)
        print(crustal_fixture.rupture_rates)
        assert read_sol.rupture_rates.columns.all() == crustal_fixture.rupture_rates.columns.all()
        assert read_sol.rupture_rates.shape == crustal_fixture.rupture_rates.shape

    def test_write_read_archive_compatible_composite_rates(self, crustal_fixture, archives):

        folder = tempfile.TemporaryDirectory()
        # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        new_path = pathlib.Path(folder.name, 'test_compatible_archive.zip')

        fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
        ref_solution = pathlib.PurePath(fixture_folder, archives['CRU'])

        crustal_fixture.to_archive(str(new_path), ref_solution, compat=True)
        read_sol = solvis.FaultSystemSolution.from_archive(new_path)

        print(read_sol.composite_rates.info())
        print(read_sol.composite_rates.columns)
        print(read_sol.composite_rates)
        assert read_sol.composite_rates.columns.all() == crustal_fixture.composite_rates.columns.all()
        assert read_sol.composite_rates.shape == crustal_fixture.composite_rates.shape

    def test_write_read_archive_incompatible(self, crustal_fixture, archives):

        folder = tempfile.TemporaryDirectory()
        # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        new_path = pathlib.Path(folder.name, 'test_incompatible_archive.zip')

        fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
        ref_solution = pathlib.PurePath(fixture_folder, archives['CRU'])

        crustal_fixture.to_archive(str(new_path), ref_solution, compat=False)
        read_sol = solvis.FaultSystemSolution.from_archive(new_path)

        print(read_sol.rupture_rates)
        print(crustal_fixture.rupture_rates)
        assert read_sol.rupture_rates.columns.all() == crustal_fixture.rupture_rates.columns.all()
        # NO the composite solutions have different rate structure
        # assert read_sol.rupture_rates.shape == crustal_fixture.rupture_rates.shape
        assert read_sol.rupture_rates['Rupture Index'].all() == crustal_fixture.rupture_rates['Rupture Index'].all()
