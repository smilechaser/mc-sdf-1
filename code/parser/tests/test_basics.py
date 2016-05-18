import os
import unittest
import yaml

from parser import (
    Parser,
    ParseGenerator,
    BadDocumentException,
    BadVersionException,
    UnsecureKeyException
)


class TestBasics(unittest.TestCase):

    DATA_FILE_PATH = 'data'
    DATA_FILE_NAME = 'basics.yaml'

    def setUp(self):

        self.data = None

        filename = os.path.join(
            os.path.dirname(__file__),
            self.DATA_FILE_PATH,
            self.DATA_FILE_NAME
        )

        with open(filename, 'r') as fin:

            self.data = yaml.load(fin)

    def test_bad_format(self):

        data = {}

        with self.assertRaises(BadDocumentException):
            Parser(data)

        data = {
            'mc-sdf-1': {}
        }

        with self.assertRaises(BadDocumentException):
            Parser(data)

        data['mc-sdf-1'] = {
            'version': 1.1
        }

        with self.assertRaises(BadVersionException):
            Parser(data)

    def test_parser(self):

        parser = Parser(self.data)

        # TODO this isn't really verifying anything...

        for cell in parser.cells:
            for context in cell.structure:
                for item in context.items:
                    pass

    def test_meta(self):

        parser = Parser(self.data)

        meta = parser.meta

        self.assertEqual(meta.author, 'smilechaser')
        self.assertEqual(meta.name, 'woolly piston commands')

        meta_dict = meta.dict_repr

        self.assertIn('author', meta_dict)
        self.assertEqual(meta_dict['author'], 'smilechaser')
        self.assertIn('name', meta_dict)
        self.assertIn('description', meta_dict)

        data = {
            'mc-sdf-1': {
                'version': 1.0,
                'meta': {
                    'author': 'me',
                    'description': '...',
                    'name': '...',
                    '__eq__': 'eeeeeeevil'
                }
            }
        }

        with self.assertRaises(UnsecureKeyException):
            parser = Parser(data)

    def test_generator(self):

        parser = Parser(self.data)
        gen = ParseGenerator(parser)

        last_context = None

        for context, item in gen.generate():

            if context != last_context:
                last_context = context
