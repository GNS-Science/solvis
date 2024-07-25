import pytest

from solvis.fault_system_solution_helper import (
    FaultSystemSolutionHelper,
    fault_participation_rate,
    section_participation_rate,
)

@pytest.fixture
def fss_helper(composite_fixture):
    fss = composite_fixture._solutions['CRU']
    yield FaultSystemSolutionHelper(fss)

def build_rupture_groups(solution):

	dfrs = solution.rupture_sections
	ruptures = dfrs['rupture'].unique().tolist()
	print(f"there are {len(ruptures)} unique ruptures")
	count =0
	sample_sections = None
	sample_rupt = None
	last_sections = None
	sample_ruptures = []

	for rupt_id in ruptures:
		sections = dfrs[dfrs.rupture==rupt_id]['section'].tolist()
		# first or reset
		if sample_rupt is None:
			sample_ruptures = []
			sample_rupt = rupt_id
			sample_sections = set(sections)
			sample_len = len(sections)
			continue

		if rupt_id is not sample_rupt:
			sample_ruptures.append(rupt_id)

		# otherwise compare overlap
		diff = len(set(sections).symmetric_difference(sample_sections))
		overlap = len(set(sections).intersection(sample_sections))

		if overlap:  # and there must be some non-zero score
			score = (sample_len - diff) / sample_len

		# print(f'rupt_id {rupt_id} score {score} overlap {overlap} sample_len: {sample_len} diff {diff}')
		if (score < 0.7) or not overlap: #(overlap < 0.8 * sample_len):
			yield {'rupture': sample_rupt, 'ruptures': sample_ruptures, 'sample_sections': sample_len}

			# signal reset
			sample_rupt = None
			count +=1

	print(f"built {count} rupture groups")


def test_build_rupture_groups(composite_fixture):
	fss = composite_fixture._solutions['CRU']

	for rep in build_rupture_groups(fss):
		print(rep)

	assert 0
