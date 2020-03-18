from web3 import Web3
import argparse
from utils import create_new_account

URL = "http://127.0.0.1:8545"

w3 = Web3(Web3.HTTPProvider(URL))

ACCOUNT_DB_NAME = 'account.json'


def create_parser():
    parser = argparse.ArgumentParser(
        description = 'Battery authentication system tool'
    )

    parser.add_argument('--new', type=str, required=False,
        help='Add account for software development company'
    )

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.new:
        print(create_new_account(w3, args.new, ACCOUNT_DB_NAME))


if __name__ == '__main__':
    main()
