from mcparser import Facing


class MaterialData:

    material = None
    dataValue = ''

WOOL_DICT = {

    'wool.white': 0,
    'wool.orange': 1,
    'wool.magenta': 2,
    'wool.light_blue': 3,
    'wool.yellow': 4,
    'wool.lime': 5,
    'wool.pink': 6,
    'wool.gray': 7,
    'wool.light_gray': 8,
    'wool.cyan': 9,
    'wool.purple': 10,
    'wool.blue': 11,
    'wool.brown': 12,
    'wool.green': 13,
    'wool.red': 14,
    'wool.black': 15
}

PISTON_FACING_DICT = {

    Facing.Down: 0,
    Facing.Up: 1,
    Facing.North: 2,
    Facing.South: 3,
    Facing.West: 4,
    Facing.East: 5
}


# TODO refactor this. ick.
def get_material_data(material, facing):

    md = MaterialData()

    if material.startswith('wool'):

        md.material = 'wool'
        md.dataValue = WOOL_DICT[material]

    else:

        md.material = material

        if material in ('piston', 'sticky_piston') and facing is not None:

            md.dataValue = PISTON_FACING_DICT[facing]

    return md
