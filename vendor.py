import sys
import argparse
from web3 import Web3
import utils


URL = "http://127.0.0.1:8545"
w3 = Web3(Web3.HTTPProvider(URL))


ACCOUNT_DB_NAME = 'account.json'
MGMT_CONTRACT_DB_NAME = 'database.json'


CONFIG = utils.open_data_base(ACCOUNT_DB_NAME)
GAS_PRICE = utils.get_actual_gas_price(w3)

if CONFIG is not None:
    TX_TEMPLATE = {'from': CONFIG['account'], 'gasPrice': GAS_PRICE}


DATABASE = utils.open_data_base(MGMT_CONTRACT_DB_NAME)

if DATABASE is None:
    DATABASE = {}


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Battery vendor management tool',
        epilog="""
                  It is expected that Web3 provider specified by WEB3_PROVIDER_URI
                  environment variable. E.g.
                  WEB3_PROVIDER_URI=file:///path/to/node/rpc-json/file.ipc
                  WEB3_PROVIDER_URI=http://192.168.1.2:8545
               """
    )

    parser.add_argument(
        '--new', type=str, required=False,
        help='Add address to the account.json'
    )

    return parser


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    if args.new:
        print(utils.create_new_account(w3, args.new, ACCOUNT_DB_NAME))


if __name__ == "__main__":
    main()
