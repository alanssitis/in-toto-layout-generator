import argparse
import tomlkit
import yaml

from in_toto.models.layout import Layout
from in_toto.models.metadata import Metablock

from .config_layout import Config

import pprint


def parse_args():
    parser = argparse.ArgumentParser(
        prog="in-toto-layout-gen",
        description="Prototype CLI to generate in-toto layouts easily")

    parser.add_argument(
        'config',
        help='Configuration file outlining the in-toto layout.',
        type=argparse.FileType('r'))
    parser.add_argument('-k',
                        '--signing-key',
                        help='Private key used to sign the layout')
    parser.add_argument('-o',
                        '--output-layout',
                        default='root.layout',
                        help='Name of signed in-toto layout file.',
                        type=argparse.FileType('w'))

    return parser.parse_args()


def parse_config(config):
    extension = config.name.split('.')[-1]
    if extension == 'toml':
        return tomlkit.load(config).unwrap()
    elif extension in ('yaml', 'yml'):
        return yaml.safe_load(config)
    else:
        print(f'Could not guess the config type of "{config.name}"!')
        return None


def main():
    args = parse_args()
    raw_config = parse_config(args.config)
    if raw_config == None:
        return

    config = Config(**raw_config).dict()

    signing_key = config.pop("signing_key")
    if args.signing_key != None:
        signing_key = args.signing_key

    config.update({"_type": "layout"})
    config = {k: v for k, v in config.items() if v is not None}

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(config)

    layout = Layout.read(config)
    metadata = Metablock(signed=layout)

    metadata.sign(signing_key)
    metadata.dump(args.output_layout)
