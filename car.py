import sys, os
import datetime as dt
from random import randint
import argparse
import web3
from web3 import Web3
from web3.middleware import geth_poa_middleware

# Project modules
import utils

URL = "http://127.0.0.1:8545"
ACCOUNT_DB_NAME = 'car.json'
MGMT_CONTRACT_DB_NAME = utils.MGMT_CONTRACT_DB_NAME
CONFIG = utils.open_data_base(ACCOUNT_DB_NAME)
DATABASE = utils.open_data_base(MGMT_CONTRACT_DB_NAME)

if DATABASE is None:
    sys.exit("Setup hasn't been done")


def generate_private_key(_w3: Web3) -> str:
    """
    Generate private key for car account using current time and random int
    
    :param Web3 _w3: Web3 instance
    :return: Private Key
    :rtype: str
    """

    t = int(dt.datetime.utcnow().timestamp())
    k = randint(0, 2 ** 16)
    privateKey = _w3.toHex(_w3.sha3(((t + k).to_bytes(32, 'big'))))
    if privateKey[:2] == '0x':
        privateKey = privateKey[2:]

    return(privateKey)


def new_car_account(_w3: Web3) -> None:
    """
    Create new addres for car account
    
    :param Web3 _w3: Web3 instance
    """

    privateKey = generate_private_key(_w3)
    data = {"key": privateKey}
    utils.write_data_base(data, ACCOUNT_DB_NAME)
    print(_w3.eth.account.privateKeyToAccount(data['key']).address)


def get_car_account_from_db(_w3: Web3) -> None:
    """
    Get car account from database

    :param Web3 _w3: Web3 instance
    """

    print(_w3.eth.account.privateKeyToAccount(utils.get_data_from_db(ACCOUNT_DB_NAME, 'key')).address)


def create_parser() -> argparse.ArgumentParser:
    """
    Create cli argument parser

    :return: Parser
    :rtype: argparse.ArgumentParser
    """

    parser = argparse.ArgumentParser(
        description='Car management tool',
        epilog="""
                  It is expected that Web3 provider specified by WEB3_PROVIDER_URI
                  environment variable. E.g.
                  WEB3_PROVIDER_URI=file:///path/to/node/rpc-json/file.ipc
                  WEB3_PROVIDER_URI=http://192.168.1.2:8545
               """
    )

    parser.add_argument(
        '--new', action='store_true', required=False, #store_true: в основном используется для флагов. Вернет Вам значение, указанное в const
        help='Generate a new account for the particular AGV'
    )

    parser.add_argument(
        '--account', action='store_true', required=False,
        help='Get identificator (Ethereum address) of AGV from the private key stored in car.json'
    )
    
    return parser


def main():
    w3 = Web3(Web3.HTTPProvider(URL))

    # configure provider to work with PoA chains
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    parser = create_parser()
    args = parser.parse_args()

    if args.new:
        new_car_account(w3)
    elif args.account:
        get_car_account_from_db(w3)


if __name__ == "__main__":
    main()
