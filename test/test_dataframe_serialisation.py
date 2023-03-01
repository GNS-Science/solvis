#!python3

import os
import pathlib
import unittest
import zipfile

import pandas as pd


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
