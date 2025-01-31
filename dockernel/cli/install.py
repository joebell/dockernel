import secrets
import platform
import docker
from typing import List
import argparse
from argparse import Namespace
from .main import subparsers, set_subcommand_func, add_common_arguments
from ..kernelspec import (Kernelspec, InterruptMode, user_kernelspec_store,
                          ensure_kernelspec_store_exists, kernelspec_dir,
                          install_kernelspec)


arguments = subparsers.add_parser(
    __name__.split('.')[-1],
    help="Install dockerized kernel image into Jupyter."
)
arguments.add_argument(
    '--name',
    help="Display name for the kernelspec. "
    "By default, container hostname is used.",
    default=None
)
arguments.add_argument(
    '--language', '-l',
    help="Language used by the kernel. "
    "Makes notebooks written in a given language "
    "run on different kernels, that use the same language, "
    "if this one is not found. "
    "By default, empty value is used.",
    default=''
)

# Add common arguments used by both install and start
add_common_arguments(arguments)


JUPYTER_CONNECTION_FILE_TEMPLATE = '{connection_file}'


def python_argv(system_type: str) -> List[str]:
    """Return proper command-line vector for python interpreter"""
    if system_type == "Linux" or system_type == "Darwin":
        # Don't take env here; just get the python that's on the path
        argv = ['python', '-m']
    elif system_type == "Windows":
        argv = ['python', '-m']
    else:
        raise ValueError(f'unknown system type: {system_type}')
    return argv


#def generate_kernelspec_argv(image_name: str, system_type: str) -> List[str]:
def generate_kernelspec_argv(args: Namespace, system_type: str) -> List[str]:
    dockernel_argv = ['dockernel', 'start']
    if args.env:
        for varname, value in args.env:
            dockernel_argv.append("-e")
            dockernel_argv.append(f"{varname}={value}")
    if args.volume:
        for source, destination, writemode in args.volume:
            dockernel_argv.append("-v")
            dockernel_argv.append(f"{source}:{destination}:{writemode}")
    if args.bind:
        for source, destination, writemode in args.bind:
            dockernel_argv.append("-b")
            dockernel_argv.append(f"{source}:{destination}:{writemode}")
    if args.gpus:
        dockernel_argv.append("--gpus")
        dockernel_argv.append(args.gpus)
    if args.user:
        dockernel_argv.append("--user")
        dockernel_argv.append(args.user)
    if args.group_add:
        dockernel_argv.append("--group-add")
        dockernel_argv.append(args.group_add)
    if args.network:
        dockernel_argv.append("--network")
        dockernel_argv.append(args.network)
    dockernel_argv.append(args.image_name)
    dockernel_argv.append(JUPYTER_CONNECTION_FILE_TEMPLATE)
    return python_argv(system_type) + dockernel_argv


def image_digest(docker_client: docker.client.DockerClient,
                 image_name: str) -> str:
    image = docker_client.images.get(image_name)
#    return image.attrs['ContainerConfig']['Hostname'] or secrets.token_hex(8)
    return image_name or secrets.token_hex(8)


def install(args: Namespace) -> int:
    system_type = platform.system()
    store_path = user_kernelspec_store(system_type)
    ensure_kernelspec_store_exists(store_path)

    argv = generate_kernelspec_argv(args, system_type)
    display_name = args.image_name if args.name is None else args.name
    language = args.language

    kernelspec = Kernelspec(argv, display_name, language,
                            interrupt_mode=InterruptMode.message)

    docker_client = docker.from_env()
    kernel_id = image_digest(docker_client, args.image_name)
    location = kernelspec_dir(store_path, kernel_id)
    install_kernelspec(location, kernelspec)

    # TODO: bare numbered exit statusses seem bad
    return 0


set_subcommand_func(parser=arguments, func=install)
