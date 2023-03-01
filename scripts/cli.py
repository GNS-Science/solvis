"""Console script for solvis."""
# noqa
import logging
import os
import sys

import click

# from toshi_hazard_store.model import migrate_v3 as migrate
# from toshi_hazard_post.hazard_aggregation import AggregationConfig, process_aggregation
# from toshi_hazard_post.hazard_aggregation.aws_aggregation import distribute_aggregation, push_test_message

log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('nshm_toshi_client.toshi_client_base').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger('botocore').setLevel(logging.INFO)
logging.getLogger('pynamodb').setLevel(logging.DEBUG)
# logging.getLogger('toshi_hazard_post').setLevel(logging.DEBUG)
# logging.getLogger('toshi_hazard_store').setLevel(logging.DEBUG)
logging.getLogger('gql.transport.requests').setLevel(logging.WARN)

formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
screen_handler = logging.StreamHandler(stream=sys.stdout)
screen_handler.setFormatter(formatter)
log.addHandler(screen_handler)


#  _ __ ___   __ _(_)_ __
# | '_ ` _ \ / _` | | '_ \
# | | | | | | (_| | | | | |
# |_| |_| |_|\__,_|_|_| |_|


@click.command()
@click.option(
    '--mode',
    '-m',
    default=lambda: os.environ.get("NZSHM22_THP_MODE", 'LOCAL'),
    type=click.Choice(['AWS', 'AWS_BATCH', 'LOCAL'], case_sensitive=True),
)
@click.option('--push-sns-test', '-pt', is_flag=True)
@click.option('--migrate-tables', '-M', is_flag=True)
@click.argument('config', type=click.Path(exists=True))  # help="path to a valid THP configuration file."
def main(config, mode, push_sns_test, migrate_tables):
    """Main entrypoint."""
    click.echo("CompositeSolution tasks - build, analyse.")
    click.echo(f"mode: {mode}")

    agconf = AggregationConfig(config)
    # click.echo(agconf)
    # log.info("Doit")

    if push_sns_test:
        push_test_message()
        return

    if mode == 'LOCAL':
        # process_aggregation(agconf, 'prefix')
        process_aggregation(agconf)
        return
    if 'AWS_BATCH' in mode:  # TODO: multiple vs30s
        if migrate_tables:
            click.echo("Ensuring that dynamodb tables are available in target region & stage.")
            migrate()
        distribute_aggregation(agconf, mode)
        return


if __name__ == "__main__":
    main()  # pragma: no cover
