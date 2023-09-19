import json, os
from argparse import Namespace
from pathlib import Path

import docker

from .main import subparsers, set_subcommand_func, add_common_arguments

arguments = subparsers.add_parser(
    __name__.split('.')[-1],
    help="Start a dockernel."
)

# TODO: add a note about how to pull / build an image
# TODO: add a note about default images


add_common_arguments(arguments)

# TODO: make this one optional
# TODO: add a help note about it being put into environment variables
# TODO: add a note about how some kernels react when it is not given
arguments.add_argument(
    'connection_file',
    help="The connection file to use."
)

CONTAINER_CONNECTION_SPEC_ENV_VAR = 'DOCKERNEL_CONNECTION_FILE'

def set_connection_ip(connection_file: Path, ip: str = '0.0.0.0'):
    """ Set/update ip field in connection file """

    connection = json.loads(connection_file.read_text())
    connection['ip'] = ip
    connection_file.write_text(json.dumps(connection))

    return connection


def start(args: Namespace) -> int:
    containers = docker.from_env().containers
    image_name = args.image_name
    connection_file = Path(args.connection_file)

    # Start building kwargs for the run command
    kwargs = {
        'image': image_name,
        'auto_remove': True,
        'stdout': True,
        'stderr': True
    }

    # Set environment variables with the connection file and user specified values
    env_vars = {
        CONTAINER_CONNECTION_SPEC_ENV_VAR: str(connection_file.absolute())
    }
    if args.env:
        for varname, value in args.env:
            env_vars.update({varname: value})
    kwargs.update({'environment': env_vars})

    # Setup any volume mounts
    if args.volume:
        mounts = []
        for source, target, writemode in args.volume:
            if writemode == 'ro':
                read_only=True
            else:
                read_only=False
            mounts.append(docker.types.Mount(
                source=source,
                target=target,
                type='volume',
                read_only=read_only))
        kwargs.update({'mounts': mounts})

    # Setup the network mode, bind the ports if we're in bind-mode
    connection = set_connection_ip(connection_file, '0.0.0.0')
    port_mapping = {connection[k]: connection[k] for k in connection if "_port" in k}
    if args.network:
        if args.network == 'bind':
            kwargs.update({'ports': port_mapping})
        kwargs.update({'network': args.network})

    # Setup the run user
    if args.user:
        if args.user == "-1":
            uid = os.getuid()
        else:
            uid = args.user
        kwargs.update({'user': uid})

    # Setup the groups
    if args.group_add:
        if args.group_add == "-1":
            group_ids = os.getgroups()
        else:
            group_ids = args.group_add
        kwargs.update({'group_add': group_ids})

    # Request GPUs
    if args.gpus:
        if args.gpus == 'all':
            device_requests = [docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])]
        else:
            device_requests = [docker.types.DeviceRequest(device_ids=[args.gpus], capabilities=[['gpu']])]
        kwargs.update({'device_requests': device_requests})

    # TODO: log stdout and stderr
    # TODO: use detached=True?
    # Run the container
    containers.run(**kwargs)

    # TODO: bare numbered exit statusses seem bad
    return 0


set_subcommand_func(parser=arguments, func=start)
