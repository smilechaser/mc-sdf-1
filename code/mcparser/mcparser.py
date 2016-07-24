'''
'''

from enum import Enum


class ParserException(RuntimeError):
    pass


class UnsecureKeyException(ParserException):
    pass


class InvalidKeyException(ParserException):
    pass


class BadDocumentException(ParserException):
    pass


class BadVersionException(ParserException):
    pass


class UnexpectedSuffixException(ParserException):
    pass


class Parser:

    BASE_NAME = 'mc-sdf-1'
    VERSION_NAME = 'version'
    VERSION = '1.0'

    def __init__(self, data):

        self.data = data

        # ensure we have a BASE_NAME property
        if self.BASE_NAME not in data:
            raise BadDocumentException(
                'Missing base name (expecting "{}")'.format(self.BASE_NAME)
            )

        # check the "version" property
        if self.VERSION_NAME not in data[self.BASE_NAME]:
            raise BadDocumentException('Missing version field.')

        version = str(data[self.BASE_NAME].get(self.VERSION_NAME))

        if version != self.VERSION:
            raise BadVersionException(
                'Expecting version "{}" but got "{}".'.format(
                    self.VERSION,
                    version
                )
            )

        self.meta

    @property
    def meta(self):

        return Meta(self.data[self.BASE_NAME].get('meta'))

    @property
    def cells(self):

        retval = []

        for cell in self.data[self.BASE_NAME].get('cells', []):

            cell_obj = Cell([x for x in cell.values()][0])
            retval.append(cell_obj)

        return retval


class Meta:

    FIELDS = (
        'author',
        'name',
        'description'
    )

    def __init__(self, data):

        for field in self.FIELDS:
            setattr(self, field, None)

        self.other = {}

        if data is None:
            return

        for field, value in data.items():

            if field in self.FIELDS:
                setattr(self, field, value)

            if field.startswith('_'):
                raise UnsecureKeyException('Field "{}".'.format(field))

            self.other[field] = value

    @property
    def dict_repr(self):

        retval = {k: getattr(self, k) for k in self.FIELDS}
        retval.update(self.other)
        return retval


class Cell:

    FIELDS = (
        'notes',
        'meta',
        'materials',
        'structure'
    )

    def __init__(self, data):

        self.data = data

        for field in self.FIELDS:
            setattr(self, field, None)

        for key in data:

            if key not in self.FIELDS:
                raise InvalidKeyException(
                    'The key "{}" is not recognized.'.format(key)
                )

            if key == 'structure':

                structure = []

                for context in data[key]:

                    if len(context) != 1:
                        # TODO need a better exception here
                        raise Exception('Expected context values.')

                    structure.append(Context(context['context']))

                    setattr(self, 'structure', structure)

            else:

                setattr(self, key, data[key])


class BlockOperation(Enum):

    Destroy = 1
    Keep = 2
    Replace = 3


class Facing(Enum):

    Other = 0

    North = 1
    East = 2
    South = 3
    West = 4

    Up = 5
    Down = 6

    @classmethod
    def resolve(clz, value):

        SHORTHAND_MAP = {
            'N': clz.North,
            'E': clz.East,
            'S': clz.South,
            'W': clz.West,
            'U': clz.Up,
            'D': clz.Down
        }

        try:
            return SHORTHAND_MAP[value]
        except KeyError:
            return clz[value]


class Context:

    values = {}              # block entity data
    meta = {}                # user-supplied key/value pairs
    operation = BlockOperation.Replace
    material = None           # material i.e. gravel, dirt, wool.red, wood.oak
    x = 0
    y = 0
    z = 0
    facing = None     # cardinal directions plus UP, DOWN, and OTHER

    # type (and implied order) of attribs that appear after x,y,z in
    # tuple format
    item_suffix = None

    items = []

    def __init__(self, data):

        self.values = data.get('values', {})
        self.meta = data.get('meta', {})

        self.operation = BlockOperation.Replace

        try:
            self.operation = BlockOperation[data.get('operation', 'Replace')]
        except KeyError:
            raise

        self.material = data.get('material')

        self.x = data.get('x', 0)
        self.y = data.get('y', 0)
        self.z = data.get('z', 0)

        self.facing = data.get('facing')

        self.item_suffix = ItemSuffix(data.get('item_suffix'))

        self.items = []

        # load items
        for item in data.get('items', []):

            if isinstance(item, str):
                self.add_item(item)
            else:
                self.items.append(Context(item['context']))

    def add_item(self, data):

        item = Item(self.item_suffix, data)
        self.items.append(item)


class Item:

    x = 0
    y = 0
    z = 0

    suffix_values = []

    def __init__(self, suffix, data):

        items = data.split(',', 3)

        self.x, self.y, self.z = [int(i) for i in items[0:3]]
        remainder = items[3:]

        if remainder:

            self.suffix_values = suffix.parse(remainder[0].strip())

    def __str__(self):
        return '<{}.{} object at 0x{:x} (x={}, y={}, z={}, facing={})>'.format(
            self.__module__,
            self.__class__.__name__,
            id(self),
            self.x,
            self.y,
            self.z,
            self.facing
        )


class ItemSuffix:

    FIELD_NAMES = (
        'facing',
        'material'
    )

    def __init__(self, data):

        self.fields = []

        if data is None:
            return

        for field in data:

            if field not in self.FIELD_NAMES:
                # TODO narrow this exception
                raise Exception('Item suffix "{}"'.format(field))

            self.fields.append(field)

    def parse(self, data):

        if data is None:
            return

        # catch the case where suffixes are supplied but haven't been
        # pre-declared in the context

        if not self.fields:
            raise UnexpectedSuffixException(
                'Not expecting any suffix values but got "{}".'.format(data)
            )

        retval = []

        target = data

        for field in self.fields:

            val, sep, target = target.partition(',')

            retval.append(val)

        if target:
            raise UnexpectedSuffixException(
                'Received additional unexpected data "{}".'.format(target)
            )

        return retval


class GeneratorContext:

    x = 0
    y = 0
    z = 0
    _facing = None
    material = None
    operation = None
    values = []

    item_suffix = None

    def construct(self, context):

        retval = GeneratorContext()

        retval.x = self.x + context.x
        retval.y = self.y + context.y
        retval.z = self.z + context.z

        retval.facing = context.facing

        retval.material = context.material

        retval.operation = context.operation

        retval.values = context.values

        retval.item_suffix = context.item_suffix

        return retval

    def clone(self):

        retval = GeneratorContext()

        retval.x = self.x
        retval.y = self.y
        retval.z = self.z

        retval.facing = self.facing

        retval.material = self.material

        retval.operation = self.operation

        retval.values = [x for x in self.values]

        retval.item_suffix = self.item_suffix

        return retval

    @property
    def facing(self):
        return self._facing

    @facing.setter
    def facing(self, val):

        if val is None:
            self._facing = None
            return

        self._facing = Facing.resolve(val)

    def to_dict(self):

        return {
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'facing': self.facing,
            'material': self.material,
            'operation': self.operation,
            'values': self.values
        }


class GeneratorItem:

    x = 0
    y = 0
    z = 0

    @classmethod
    def construct(clz, gencontext, item):

        new_item = clz()

        new_item.x = gencontext.x + item.x
        new_item.y = gencontext.y + item.y
        new_item.z = gencontext.z + item.z

        new_context = gencontext

        if item.suffix_values:

            new_context = gencontext.clone()

            for n, field_name in enumerate(new_context.item_suffix.fields):

                setattr(new_context, field_name, item.suffix_values[n])

        return new_context, new_item

    def to_dict(self):

        return {
            'x': self.x,
            'y': self.y,
            'z': self.z
        }


class ParseGenerator:

    def __init__(self, parser):

        self.parser = parser

        self.x_offset = 0
        self.y_offset = 0
        self.z_offset = 0

    def generate(self):

        gencons = []

        gc = GeneratorContext()

        gc.x = self.x_offset
        gc.y = self.y_offset
        gc.z = self.z_offset

        gencons.append(gc)

        for cell in self.parser.cells:

            for context in cell.structure:

                gencons.append(gencons[-1].construct(context))

                for item in context.items:

                    yield GeneratorItem.construct(gencons[-1], item)

                gencons.pop()
