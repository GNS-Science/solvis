#!python3 test_inversion_solution.py
import solvis


class TestSolvisCrustal(object):
    def test_crustal_parent_fault_names(self, crustal_solution_fixture):
        names = solvis.parent_fault_names(crustal_solution_fixture)
        assert names[0] == 'Alpine Jacksons to Kaniere'
        assert names[-1] == "Vernon 4"


class TestSolvisSubductionInversionSolution(object):
    def test_puy_parent_fault_names(self, puysegur_small_fss_fixture):
        names = solvis.parent_fault_names(puysegur_small_fss_fixture)
        assert names[0] == 'Puysegur, 30km, 50% coupling'
        assert names[-1] == 'Puysegur, 30km, 50% coupling'
        assert len(names) == 1

    def test_hik_parent_fault_names(self, hikurangi_small_fss_fixture):
        names = solvis.parent_fault_names(hikurangi_small_fss_fixture)
        assert (
            names[0] == 'Hikurangi, Kermadec to Louisville ridge, 30km '
            '- with slip deficit smoothed near East Cape and locked near trench.'
        )
        assert (
            names[-1] == 'Hikurangi, Kermadec to Louisville ridge, 30km '
            '- with slip deficit smoothed near East Cape and locked near trench.'
        )
        assert len(names) == 1
