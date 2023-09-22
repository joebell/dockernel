from typing import Callable
from argparse import ArgumentParser, Namespace


DESCRIPTION = "Adds docker image to Jupyter as a kernel"

arguments = ArgumentParser(description=DESCRIPTION)
# TODO: add required=True when 3.6 compat is dropped
subparsers = arguments.add_subparsers(help='One of the following:',
                                      metavar='subcommand')


def set_subcommand_func(parser: ArgumentParser,
                        func: Callable[[Namespace], int]) -> None:
    parser.set_defaults(func=func)


def run_subcommand(parsed_args: Namespace) -> int:
    # TODO: after 3.6 compat is dropped, the if block below becomes redundant
    if 'func' not in parsed_args:
        arguments.print_help()
        return 1
    return parsed_args.func(parsed_args)

# Add arguments common to both install and start
def add_common_arguments(arguments):

    arguments.add_argument(
        'image_name',
        help="Name of the docker image to use."
    )
    
    # Additional arguments for controlling container behavior
    def volume_arg(arg_string):
        try:
            parts = arg_string.split(":")
            if len(parts) == 2:
                source, destination = parts
                writemode = 'rw'  # Default to read-write
                return source, destination, writemode
            elif len(parts) == 3:
                source, destination, writemode = parts
                return source, destination, writemode
            else:
                raise ValueError
        except ValueError:
            raise argparse.ArgumentTypeError("Volume argument must be in the format 'source:destination[:writemode]'")

    def env_arg(arg_string):
        try:
            parts = arg_string.split("=")
            if len(parts) == 2:
                varname, value = parts
                return varname, value
            else:
                raise ValueError
        except ValueError:
            raise argparse.ArgumentTypeError("Environment variable arguments must be in the format 'variable=value'")
    
    arguments.add_argument(
        '--volume', '-v',
        metavar='source:destination', type=volume_arg, action='append',
        help="Mount a named-volume to the container. ",
        default=None
    )
    arguments.add_argument(
        '--bind', '-b',
        metavar='source:destination', type=volume_arg, action='append',
        help="Mount a bind-mount to the container. ",
        default=None
    )
    arguments.add_argument(
        '--gpus',
        help="GPU devices to add to the container. ",
        default=None
    )
    arguments.add_argument(
        '--user', '-u',
        help="User to run the container as. Use -1 to run as the current user.",
        default=None
    )
    arguments.add_argument(
        '--group-add',
        help="Groups to join. Use -1 to get all groups of the current user.",
        default=None
    )
    arguments.add_argument(
        '--env', '-e', type=env_arg, action='append',
        help="Set environment variables in the container. ",
        default=None
    )
    arguments.add_argument(
        '--network',
        help="Add the container to the network. ",
        default='bind',
    )
    return arguments

