'''
    build.py model_file x y z --host --port --password
'''

import argparse
from getpass import getpass
import os
import re
import sys
import yaml

# monkey-patch our minecraft-tools module in (since it isn't on PyPI)
sys.path.append('./minecraft-tools')

# while we're at it - patch in the parser too... :O
sys.path.append('../mcparser')

from api.rcon import RemoteConsole, AuthenticationError, ConnectionError
from mcparser import Parser, ParseGenerator

from materials import get_material_data


class MCBuilderException(Exception):
    '''Base Exception class for this module.'''
    pass


class BadPositionException(MCBuilderException):
    '''Represents an invalid/unrecognized position string.'''
    pass


class BadConfigException(MCBuilderException):
    '''Represents an error in the parsed config file.'''
    pass


class Position:
    '''Represents a starting position.'''

    x = 0
    y = 0
    z = 0

    STRING_REGEX = re.compile('(-?\d+) (-?\d+) (-?\d+)')

    @classmethod
    def generate(clz, data_string):

        obj = clz()

        match = clz.STRING_REGEX.match(data_string)

        if not match:

            raise BadPositionException(
                'Could not parse string "{}" '
                'into a position.'.format(data_string)
            )

        obj.x, obj.y, obj.z = [int(x) for x in match.groups()]

        return obj

    @property
    def data(self):

        return {
            'x': self.x,
            'y': self.y,
            'z': self.z
        }

    def __str__(self):

        return '{} {} {}'.format(self.x, self.y, self.z)


class Options:
    '''Program options and settings.'''

    host = None
    port = None
    password = None

    filename = None

    position = Position()

    KEY_VALUE_PAIR_REGEX = re.compile('^(.*)=(.*)', re.MULTILINE)

    @classmethod
    def generate(clz, args):
        '''Factory method to create a new Options object given a set
        of optparse args.'''

        obj = Options()

        # load settings by parsing the minecraft server.properties file
        if args.server_properties:

            obj.load_properties_file(args.server_properties)

        if not obj.host and args.host:

            obj.host = args.host

        if not obj.port and args.port:

            obj.port = int(args.port)

        if not obj.password and args.password_var:

            # attempt to get password from the specified environment var
            pw = os.environ.get(args.password_var)

            obj.password = pw if pw else None

        if not obj.password and args.password:
            obj.password = args.password

        obj.filename = args.filename

        if args.position:

            obj.position = Position.generate(args.position)

        return obj

    def load_properties_file(self, filename):
        '''Try to load the relevant property values (rcon password,
        rcon port) from the specified server.properties file.

        This will also double check that rcon is enabled.'''

        realpath = os.path.normcase(filename)

        if realpath.startswith('~'):
            realpath = os.path.expanduser(realpath)

        realpath = os.path.normpath(realpath)

        property_dict = {}

        with open(realpath, 'r') as fin:

            data = fin.read()

            key_values = self.KEY_VALUE_PAIR_REGEX.findall(data)

            property_dict = {x[0]: x[1] for x in key_values}

        self.port = int(property_dict.get('rcon.port', self.port))
        self.password = property_dict.get('rcon.password', self.password)

        enabled = bool(property_dict.get('enable-rcon', 'true'))

        if not enabled:

            raise BadConfigException(
                'ERROR: According to your server.properties file rcon is '
                'not enabled.')

    @property
    def data(self):

        return {
            'host': self.host,
            'port': self.port,
            'password': self.password,
            'filename': self.filename,
            'position': self.position.data
        }


def main():

    # parse our arguments
    parser = argparse.ArgumentParser(
        description='Build the specified mc-sdf-1 construct via RCON.'
    )
    parser.add_argument('filename')

    # allow user to specify "initial context coords" from command line
    # i.e. to be able to place structures anywhere in the world (support @name
    # syntax too)

    parser.add_argument('--position', action='store',
                        help='')

    # allow user to specify the server.properties file (so we
    # can get port and password)

    parser.add_argument('--server-properties', action='store',
                        help='')

    #
    # connection details
    #
    parser.add_argument('--host', action='store', default='localhost',
                        help='')
    parser.add_argument('--port', action='store', default=13137,
                        help='')
    parser.add_argument('--password', action='store',
                        help='')
    parser.add_argument('--password-var', action='store',
                        default='MC_SDF_PASSWORD',
                        help='')

    args = parser.parse_args()

    options = Options.generate(args)

    if not options.password:

        options.password = getpass('Password: ')

    # open the specified file

    data = None

    with open(options.filename, 'r') as fin:

        data = yaml.load(fin)

    parser = Parser(data)
    gen = ParseGenerator(parser)

    #
    # connect to server via rcon interface
    #

    rcon = None
    try:

        rcon = RemoteConsole(
            options.host,
            options.port,
            options.password
        )

        '''
        /setblock <x> <y> <z> <TileName> [dataValue]
            [oldBlockHandling] [dataTag]
        '''

        last_context = None

        # provide position context data to the generator

        gen.x_offset = options.position.x
        gen.y_offset = options.position.y
        gen.z_offset = options.position.z

        for context, item in gen.generate():

            if context != last_context:
                last_context = context

            material_data = get_material_data(
                last_context.material,
                last_context.facing
            )

            values = {
                'x': item.x,
                'y': item.y,
                'z': item.z,
                'material': material_data.material,
                'dataValue': material_data.dataValue
            }

            command = 'setblock {x} {y} {z} {material} {dataValue}'.format(
                **values
            )

            print(command)

            response, response_id = rcon.send(command)

            if response:
                print(response.decode())

    except AuthenticationError as exc:
        print('AuthenticationError: (details="{}")'.format(exc))
    except ConnectionError as exc:
        print('ConnectionError: Check that your server is running and you '
              'have specified the correct hostname and port.')
    finally:
        if rcon:
            rcon.disconnect()

if __name__ == '__main__':

    main()
