import argparse
import re
import tomlkit
import yaml
from datetime import date, datetime, timezone, timedelta

from securesystemslib import (
    KEY_TYPE_ECDSA,
    KEY_TYPE_ED25519,
    KEY_TYPE_RSA,
    exceptions,
    interface,
)

from in_toto.models.layout import Layout
from in_toto.models.metadata import Metablock

from .config_layout import Config


def _parse_args():
    parser = argparse.ArgumentParser(
        prog="in-toto-layout-gen",
        description="Prototype CLI to generate in-toto layouts easily")

    parser.add_argument(
        'config',
        help='Configuration file outlining the in-toto layout.',
        type=argparse.FileType('r'))
    parser.add_argument('-s',
                        '--signer',
                        help='Private key used to sign the layout')
    parser.add_argument('-o',
                        '--output-layout',
                        default='root.layout',
                        help='Name of signed in-toto layout file.')

    return parser.parse_args()


def _parse_config(config):
    extension = config.name.split('.')[-1]

    if extension == 'toml':
        return tomlkit.load(config).unwrap()

    elif extension in ('yaml', 'yml'):
        return yaml.safe_load(config)

    else:
        raise Exception(f"Could not guess the config type of '{config.name}'!")


def _parse_expires(expires):
    if expires == None:
        return None

    elif isinstance(expires, datetime) or isinstance(expires, date):
        return expires.isoformat()

    elif match := re.fullmatch(r"^(\d+)(s|m|h|d|w)$", expires):
        now = datetime.now(timezone.utc)
        val, unit = match.groups()
        delta = timedelta()

        if unit == 's':
            delta = timedelta(seconds=int(val))
        elif unit == 'm':
            delta = timedelta(minutes=int(val))
        elif unit == 'h':
            delta = timedelta(hours=int(val))
        elif unit == 'd':
            delta = timedelta(days=int(val))
        elif unit == 'w':
            delta = timedelta(weeks=int(val))

        return (now + delta).isoformat(timespec='seconds').replace(
            '+00:00', 'Z')

    else:
        raise Exception(f"Could not parse layout expiration '{expires}'")


def _import_publickey_from_file(filepath, key_type):
    if key_type == KEY_TYPE_RSA:
        return interface.import_rsa_publickey_from_file(filepath)

    elif key_type == KEY_TYPE_ECDSA:
        return interface.import_ecdsa_publickey_from_file(filepath)

    elif key_type == KEY_TYPE_ED25519:
        return interface.import_ed25519_publickey_from_file(filepath)

    else:
        raise exceptions.FormatError(f"Unsupported key type '{key_type}'.")


def _update_step(step, keys):
    step["expected_materials"] = [
        mat.split(" ") for mat in step["expected_materials"]
    ]
    step["expected_products"] = [
        prod.split(" ") for prod in step["expected_products"]
    ]
    step["pubkeys"] = [keys[id]["keyid"] for id in step["pubkeys"]]
    step["expected_command"] = step["expected_command"].split(" ")
    return step


def _update_inspect(inspect):
    inspect["expected_materials"] = [
        mat.split(" ") for mat in inspect["expected_materials"]
    ]
    inspect["expected_products"] = [
        prod.split(" ") for prod in inspect["expected_products"]
    ]
    inspect["run"] = inspect["run"].split(" ")
    return inspect


def main():
    args = _parse_args()
    config = Config(**_parse_config(args.config)).dict()
    config["_type"] = "layout"

    config["expires"] = _parse_expires(config["expires"])

    signer_key = config.pop("signer")
    if args.signer != None:
        signer_key = args.signer
    if signer_key == None:
        raise Exception('Do not have a signing key')
    signer = interface.import_privatekey_from_file(signer_key["path"])

    keys = {
        k: _import_publickey_from_file(v["path"], v["key_type"])
        for k, v in config.pop("keys").items()
    }
    config["keys"] = {v["keyid"]: v for v in keys.values()}

    config["steps"] = [_update_step(s, keys) for s in config["steps"]]
    config["inspect"] = [_update_inspect(i) for i in config["inspect"]]

    config = {k: v for k, v in config.items() if v is not None}

    layout = Layout.read(config)
    metadata = Metablock(signed=layout)

    metadata.sign(signer)
    metadata.dump(args.output_layout)
