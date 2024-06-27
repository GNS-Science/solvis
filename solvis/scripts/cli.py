"""Console script for solvis."""
# noqa
import logging
import os
import pathlib
import sys
import time

import click
import nzshm_model
from nshm_toshi_client.toshi_file import ToshiFile
from nzshm_common.location.location import location_by_id

from solvis import CompositeSolution, FaultSystemSolution, circle_polygon, export_geojson
from solvis.get_secret import get_secret
from solvis.inversion_solution.inversion_solution import BranchInversionSolution, InversionSolution

# Get API key from AWS secrets manager
API_URL = os.getenv('NZSHM22_TOSHI_API_URL', "http://127.0.0.1:5000/graphql")
try:
    if 'TEST' in API_URL.upper():
        API_KEY = get_secret("NZSHM22_TOSHI_API_SECRET_TEST", "us-east-1").get("NZSHM22_TOSHI_API_KEY_TEST")
    elif 'PROD' in API_URL.upper():
        API_KEY = get_secret("NZSHM22_TOSHI_API_SECRET_PROD", "us-east-1").get("NZSHM22_TOSHI_API_KEY_PROD")
    else:
        API_KEY = os.getenv('NZSHM22_TOSHI_API_KEY', "")
except AttributeError as err:
    print(f"unable to get secret from secretmanager: {err}")
    API_KEY = os.getenv('NZSHM22_TOSHI_API_KEY', "")
S3_URL = None
DEPLOYMENT_STAGE = os.getenv('DEPLOYMENT_STAGE', 'LOCAL').upper()
REGION = os.getenv('REGION', 'ap-southeast-2')  # SYDNEY


# from toshi_hazard_store.model import migrate_v3 as migrate
# from toshi_hazard_post.hazard_aggregation import AggregationConfig, process_aggregation
# from toshi_hazard_post.hazard_aggregation.aws_aggregation import distribute_aggregation, push_test_message

log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('nshm_toshi_client.toshi_client_base').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger('botocore').setLevel(logging.INFO)
# logging.getLogger('pynamodb').setLevel(logging.DEBUG)
logging.getLogger('fiona').setLevel(logging.INFO)
logging.getLogger('gql.transport.requests').setLevel(logging.WARN)
logging.getLogger('solvis').setLevel(logging.INFO)

formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
screen_handler = logging.StreamHandler(stream=sys.stdout)
screen_handler.setFormatter(formatter)
log.addHandler(screen_handler)

MODEL_ID_HELP = "An nzshm_model ID (default: NSHM_v1.0.4)"


class SourceSolution(ToshiFile):
    def get_source(self, fid):

        qry = '''
        query file ($id:ID!) {
            node(id: $id) {
                __typename
                ... on FileInterface {
                  file_name
                  file_size
                  meta {k v}
                }
                ... on ScaledInversionSolution {
                  meta{ k k}
                  source_solution {
                    meta {k v}
                  }
                }
            }
        }
        '''
        print(qry)
        input_variables = dict(id=fid)
        executed = self.run_query(qry, input_variables)
        return executed['node']


def rupt_set_from_meta(meta):
    for itm in meta:
        if itm['k'] == "rupture_set_file_id":
            return itm['v']


def fetch_toshi_files(work_folder, file_ids):
    headers = {"x-api-key": API_KEY}
    api = SourceSolution(API_URL, S3_URL, None, with_schema_validation=False, headers=headers)
    file_map = {}
    for fid in file_ids:
        click.echo(f'fetching {fid}')
        file_detail = api.get_source(fid)
        click.echo(file_detail)
        fname = pathlib.Path(work_folder, file_detail['file_name'])

        file_map[fid] = dict(filepath=fname, rupt_set_id=rupt_set_from_meta(file_detail['source_solution']['meta']))
        if fname.exists():
            click.echo(f'skipping {fname}')
            continue
        api.download_file(fid, work_folder)
    return file_map


def build_fault_system_solution(work_folder, fault_system, model_version=nzshm_model.CURRENT_VERSION):
    current_model = nzshm_model.get_model_version(model_version)
    slt = current_model.source_logic_tree()
    branch = None
    for fslt in slt.fault_system_lts:
        if fslt.short_name == fault_system:
            branch = fslt
            break

    click.echo(f"branch {branch.short_name} {branch.long_name}")
    # click.echo(branch)

    file_ids = [FaultSystemSolution.get_branch_inversion_solution_id(b) for b in branch.branches]
    filemap = fetch_toshi_files(work_folder, file_ids)

    # prepare BranchSolutions
    click.echo("load branch solutions...")
    solutions = []
    for fslt_branch in branch.branches:
        solutions.append(
            BranchInversionSolution.new_branch_solution(
                InversionSolution.from_archive(filemap[fslt_branch.inversion_solution_id]['filepath']),
                branch=fslt_branch,
                fault_system=branch.short_name,
                rupture_set_id=filemap[fslt_branch.inversion_solution_id]['rupt_set_id'],
            )
        )

    # build time ....
    click.echo("build fault_system_solution ...")
    tic = time.perf_counter()
    fault_system_solution = FaultSystemSolution.from_branch_solutions(solutions)
    toc = time.perf_counter()
    click.echo(f"time to build fault_system_solution: {toc-tic} seconds")

    # ensure fast indices
    fault_system_solution.enable_fast_indices()

    # save the archive
    fname = pathlib.Path(work_folder, f"{fault_system}_fault_system_solution.zip")
    fault_system_solution.to_archive(str(fname), filemap[file_ids[0]]['filepath'])  # , compat=False)


def build_composite_all(work_folder, archive_name, model_version=nzshm_model.CURRENT_VERSION):
    current_model = nzshm_model.get_model_version(model_version)
    slt = current_model.source_logic_tree()

    def branch_solutions(fslt, filemap):
        for fslt_branch in fslt.branches:
            inversion_solution_id = FaultSystemSolution.get_branch_inversion_solution_id(fslt_branch)
            yield BranchInversionSolution.new_branch_solution(
                InversionSolution.from_archive(filemap[inversion_solution_id]['filepath']),
                branch=fslt_branch,
                fault_system=fslt.short_name,
                rupture_set_id=filemap[inversion_solution_id]['rupt_set_id'],
            )

    composite = CompositeSolution(slt)  # create the new composite solutoin
    tic = time.perf_counter()

    for fault_system_lt in slt.fault_system_lts:
        if fault_system_lt.short_name in ['CRU', 'PUY', 'HIK']:
            file_ids = [FaultSystemSolution.get_branch_inversion_solution_id(b) for b in fault_system_lt.branches]
            filemap = fetch_toshi_files(work_folder, file_ids)

            # prepare BranchSolutions
            click.echo(f"load branch solutions... {fault_system_lt.short_name}")
            fss = FaultSystemSolution.from_branch_solutions(branch_solutions(fault_system_lt, filemap))

            # ensure fast indices
            fss.enable_fast_indices()

            # write the fss-archive file
            ref_solution = filemap[file_ids[0]]['filepath']  # the file path to the reference solution
            new_path = pathlib.Path(work_folder, f'{fault_system_lt.short_name}_fault_system_archive.zip')
            fss.to_archive(str(new_path), ref_solution)  # , compat=True)
            assert new_path.exists()

            composite.add_fault_system_solution(fault_system_lt.short_name, fss)

    new_path = pathlib.Path(work_folder, archive_name)
    composite.to_archive(new_path)
    toc = time.perf_counter()
    click.echo(f'created composite solution file {new_path.name} in {toc-tic} seconds')
    # print( composite.rupture_rates )
    # print()
    # print(composite.rupture_surface("HIK", 1))


#  _ __ ___   __ _(_)_ __
# | '_ ` _ \ / _` | | '_ \
# | | | | | | (_| | | | | |
# |_| |_| |_|\__,_|_|_| |_|


@click.group()
@click.option('--fault_system', '-fs', default='PUY', type=click.Choice(['PUY', 'HIK', 'CRU', 'ALL']))
@click.option('--work_folder', '-w', default=lambda: os.getcwd())
@click.pass_context
def cli(ctx, work_folder, fault_system):
    """
    FaultSystemSolution tasks - build, analyse.

    Note:
    This script relies on access to the NSHM Toshi GraphQL API (nshm-toshi-api)
    for build operations. If you do not have this installed locally, the
    NZSHM22_TOSHI_API_URL environment variable must be set accordingly.
    """
    click.echo("FaultSystemSolution tasks - build, analyse.")
    click.echo(f"work folder: {work_folder}")
    click.echo(f"fault system: {fault_system}")

    ctx.ensure_object(dict)
    ctx.obj['work_folder'] = work_folder
    ctx.obj['fault_system'] = fault_system


@cli.command()
@click.option(
    '--archive_name',
    '-a',
    default="CompositeSolution.zip",
    help="An OpenSHA solution archive name (default: CompositeSolution.zip)",
)
@click.option('--model_id', '-m', default="NSHM_v1.0.4", help=MODEL_ID_HELP)
@click.pass_context
def build(ctx, archive_name, model_id):
    if ctx.obj['fault_system'] == 'ALL':
        solution = build_composite_all(ctx.obj['work_folder'], archive_name, model_id)
    else:
        solution = build_fault_system_solution(ctx.obj['work_folder'], ctx.obj['fault_system'], model_id)  # noqa: F841


@cli.command('ls')
@click.option(
    '--archive_name',
    '-a',
    default="NSHM_v1.0.4_CompositeSolution.zip",
    help="An OpenSHA solution archive name (NSHM_v1.0.4_CompositeSolution.zip)",
)
@click.option('--model_id', '-m', default="NSHM_v1.0.4", help=MODEL_ID_HELP)
@click.pass_context
def perf(ctx, archive_name, model_id):
    # click.echo(ctx.obj['work_folder'] , ctx.obj['fault_system'] )

    tic = time.perf_counter()
    # Load archive with SLT
    work_folder, fault_system = ctx.obj['work_folder'], ctx.obj['fault_system']  # noqa: F841
    current_model = nzshm_model.get_model_version(model_id)
    slt = current_model.source_logic_tree()

    comp = CompositeSolution.from_archive(pathlib.Path(work_folder, archive_name), slt)
    toc = time.perf_counter()
    click.echo(f'time to load archive: {toc-tic:2.3f} seconds')
    print(comp)

    tic = toc
    # LOC = location_by_id('WLG')
    rupture_surface_gdf = comp._solutions[ctx.obj['fault_system']].rupture_surface(2)
    toc = time.perf_counter()
    click.echo(f'time to load 1st rupture_surface_gdf: {toc-tic:2.3f} seconds')
    tic = toc

    rupture_surface_gdf = comp._solutions[ctx.obj['fault_system']].rupture_surface(4)  # noqa: F841
    toc = time.perf_counter()
    click.echo(f'time to load 2nd rupture_surface_gdf: {toc-tic:2.3f} seconds')
    tic = toc


@click.pass_context
def query(ctx):
    # click.echo(ctx.obj['work_folder'] , ctx.obj['fault_system'] )

    work_folder, fault_system = ctx.obj['work_folder'], ctx.obj['fault_system']

    fname = pathlib.Path(work_folder, f"{fault_system}_fault_system_solution.zip")
    sol = FaultSystemSolution.from_archive(fname)

    print(sol)
    print(sol.rupture_rates)
    tic = time.perf_counter()

    LOC = location_by_id('KBZ')
    polygon = circle_polygon(2e5, LOC['latitude'], LOC['longitude'])  # 50km circle around WLG
    ruptures = sol.get_ruptures_intersecting(polygon)  # noqa: F841
    loc_filtered = list(sol.ruptures.index)

    rr = sol.rate
    rate = 1e-5
    rate_filtered = rr[rr['rate_max'] > rate]["Rupture Index"].unique()

    combo = list(set(rate_filtered).intersection(set(loc_filtered)))
    print(combo)
    print(len(combo))

    for rupt in combo:
        export_geojson(sol.rupture_surface(rupt), f"{work_folder}/CRU_rupture_{rupt}.geojson", indent=2)

    toc = time.perf_counter()
    click.echo(f'time to get ruptures: {toc-tic} seconds')


if __name__ == "__main__":
    cli()  # pragma: no cover
