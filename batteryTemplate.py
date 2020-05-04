import os, sys
import datetime as dt
import argparse
import json
from typing import Union
from sha3 import keccak_256
from py_ecc.secp256k1 import ecdsa_raw_sign

from eth_keys import keys
from eth_utils import decode_hex

private_key = "0xd016ad062dceb73f7587e25bdfc4d665f8eb6e4f37f2c2c526c25633a63d96ed"

def get_db_name():
    return os.path.basename(__file__)[:-3] + ".json"


def open_data_base(_file_name: str) -> Union[dict, None]:
    """
    Load data from the database

    :param str _file_name: Database file name
    :return: None if file does not exist or loaded from the file data
    :rtype: None/dict
    """

    if os.path.exists(_file_name):
        with open(_file_name) as file:
            return json.load(file)

    else:
        return None   
 

def write_data_base(_data: dict, _file_name: str) -> None:
    """
    Write dictionary to specific json file

    :param dict _data: Data to write
    :param str _file_name: Name of the file for writing
    :return: Nothing
    :rtype: None
    """

    with open(_file_name, 'w') as out:
        json.dump(_data, out)


def charge() -> int:
    """
    Increase battery's charge cycles

    :return: Charge cycles
    :rtype: int
    """
    
    db_name = get_db_name()
    data = open_data_base(f"firmware/{db_name}")

    if data is None:
        data = {'Charge cycles': 0}

    data['Charge cycles'] += 1
    write_data_base(data, f"firmware/{db_name}")

    return data['Charge cycles']


def get_battery_info() -> tuple:
    charges = open_data_base(f"firmware/{get_db_name()}")['Charge cycles']
    time = int(dt.datetime.utcnow().timestamp())
    _private_key = int(private_key, base=16).to_bytes(32, byteorder='big')

    message = (charges * (1 << 32) + time).to_bytes(32, byteorder='big')

    data = keccak_256(message).digest()
    battery_id = ecdsa_raw_sign(data, _private_key)

    v = battery_id[0]
    r = '0' * (64 -len(hex(battery_id[1])[2:])) + hex(battery_id[1])[2:]
    s = '0' * (64 -len(hex(battery_id[2])[2:])) + hex(battery_id[2])[2:]


    return tuple([charges, time, v, r, s])


def create_parser() -> argparse.ArgumentParser:
    """
    Create cli argument parser

    :return: Parser
    :rtype: argparse.ArgumentParser
    """

    parser = argparse.ArgumentParser(
        description = 'Battery authentication system tool'
    )

    parser.add_argument(
        '--charge', action='store_true', required=False,
        help="Charge battery"
    )

    parser.add_argument(
        '--get', action='store_true', required=False,
        help="Get battery info"
    )

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.charge:
        print(f"Total charge cycles: {charge()}")
    elif args.get:
        for info in get_battery_info():
            print(info)


if __name__ == "__main__":
    main()
