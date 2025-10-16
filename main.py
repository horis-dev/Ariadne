import shutil
import threading
from loguru import logger
from rich import print
import click
from tqdm import tqdm

from fuzzer import Fuzzer
from loader import InitData, Loader

tqdm_lock = threading.Lock()
logger.remove()

def tqdm_sink(message):
    with tqdm_lock:
        tqdm.write(message, end="")

logger.add(
    # sys.stderr,
    tqdm_sink,
    level="DEBUG",
    colorize=True,
    enqueue=True
)

logger.add("logfile.log", level="DEBUG", mode="w")


@click.command()
@click.option('--config-path', '-c', help="Path to the configuration TOML file", required=True)
@click.option('--docker-compose-path', '-d', help="Path to docker-compose.yml file", required=True)
@click.option('--help', '-h', is_flag=True, help="Show this message and exit")
def main(config_path, docker_compose_path, help):
    """Webfuzz - A web application fuzzing tool"""
    
    shutil.rmtree("seeds", ignore_errors=True)
    # If any of the required parameters are missing, show help and exit
    ctx = click.get_current_context()
    if not config_path or not docker_compose_path or help:
        click.echo(ctx.get_help())
        ctx.exit()
        
    print("Starting Loading...")
    loader: Loader = Loader(config_path=config_path)
    project_data: InitData = loader.load()
    print("Finished Loading.")

    print("Initiating Fuzzer...")
    fuzzer = Fuzzer(project_data, docker_compose_path)
    print("Finished Initiating Fuzzer.")

    print("Starting Fuzzing...")
    fuzzer.fuzz()


if __name__ == '__main__':
    main()
