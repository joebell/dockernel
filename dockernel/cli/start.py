import json
from argparse import Namespace
from pathlib import Path

import docker

from .main import subparsers, set_subcommand_func

arguments = subparsers.add_parser(
    __name__.split('.')[-1],
    help="Start a dockernel."
)

# TODO: add a note about how to pull / build an image
# TODO: add a note about default images
arguments.add_argument(
    'image_name',
    help="Name of the docker image to use."
)

# TODO: make this one optional
# TODO: add a help note about it being put into environment variables
# TODO: add a note about how some kernels react when it is not given
arguments.add_argument(
    'connection_file',
    help="The connection file to use."
)


CONTAINER_CONNECTION_SPEC_PATH = '/kernel-connection-spec.json'
CONTAINER_CONNECTION_SPEC_ENV_VAR = 'DOCKERNEL_CONNECTION_FILE'


def set_connection_ip(connection_file: Path, ip: str = '0.0.0.0'):
    """ Set/update ip field in connection file """

    connection = json.loads(connection_file.read_text())
    connection['ip'] = ip
    connection_file.write_text(json.dumps(connection))

    return connection


def start(parsed_args: Namespace) -> int:
    containers = docker.from_env().containers
    image_name = parsed_args.image_name
    connection_file = Path(parsed_args.connection_file)

    connection = set_connection_ip(connection_file, '0.0.0.0')
    port_mapping = {connection[k]: connection[k] for k in connection if "_port" in k}

    # TODO: parametrize connection spec file bind path
    # 
    # This won't work for DooD configurations, need to specify the source file with a path that the host can view. 
#    connection_file_mount = docker.types.Mount(
#        target=CONTAINER_CONNECTION_SPEC_PATH,
#        source=str(connection_file.absolute()),
#        type='bind',
#        # XXX: some kernels still open connection spec in write mode
#        # (I'm looking at you, IPython), even though it's not being written
#        # into.
#        read_only=False
#    )
#    env_vars = {
#        CONTAINER_CONNECTION_SPEC_ENV_VAR: CONTAINER_CONNECTION_SPEC_PATH
#    }

# Here instead of bind-mounting the connection_file into the image, we'll volume mount it from the volume that the host has. This also provides access to all the home directories in the image
    print('Connection file: %s' % connection_file)
    connection_file_mount = docker.types.Mount(
        target='/home',
        source='notebook-homedirs',
        type='volume',
        # XXX: some kernels still open connection spec in write mode
        # (I'm looking at you, IPython), even though it's not being written
        # into.
        read_only=False
    )

    # The CONTAINER_CONNECTION_SPEC_PATH will need to be adjusted too, but it should have the same path in the outer docker as in the inner docker
    env_vars = {
        CONTAINER_CONNECTION_SPEC_ENV_VAR: str(connection_file.absolute())
    }

    # ADDED FOR GPU SUPPORT
    device_requests = [docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])]

    # TODO: parametrize possible mounts
    # TODO: log stdout and stderr
    # TODO: use detached=True?
    containers.run(
        image_name,
        auto_remove=True,
        environment=env_vars,
        mounts=[connection_file_mount],
        network_mode='bridge',
        ports=port_mapping,
        stdout=True,
        stderr=True,
        device_requests=device_requests
    )

    # TODO: bare numbered exit statusses seem bad
    return 0


set_subcommand_func(parser=arguments, func=start)
