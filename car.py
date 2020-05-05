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
MGMT_CONTRACT_SRC_PATH = utils.MGMT_CONTRACT_SRC_PATH
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

    return (privateKey)


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


def register_car(_w3: Web3):
    """
    Register new car

    :param Web3 _w3: Web3 instance
    """

    data = utils.open_data_base(MGMT_CONTRACT_DB_NAME)

    if data is None:
        return 'Cannot access management contract database'
        
    data = CONFIG

    if data is None:
        return 'Cannot access account database'

    private_key = data['key']
    mgmt_contract = utils.init_management_contract(_w3)
    car_address = _w3.eth.account.privateKeyToAccount(private_key).address
    registration_required_gas = 50000
    gas_price = utils.get_actual_gas_price(_w3)

    if registration_required_gas * gas_price > _w3.eth.getBalance(car_address):
        return 'No enough funds to send transaction'

    nonce = _w3.eth.getTransactionCount(car_address)
    tx = {'gasPrice': gas_price, 'nonce': nonce}

    regTx = mgmt_contract.functions.registerCar().buildTransaction(tx)
    signTx = _w3.eth.account.signTransaction(regTx, private_key)
    txHash = _w3.eth.sendRawTransaction(signTx.rawTransaction)
    receipt = web3.eth.wait_for_transaction_receipt(_w3, txHash, 120, 0.1)

    if receipt.status == 1:
        return 'Registered succsessfully'        
    else:
        return 'Car registration failed'



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
        '--new', action='store_true', required=False,
        help='Generate a new account for the particular AGV'
    )

    parser.add_argument(
        '--account', action='store_true', required=False,
        help='Get identificator (Ethereum address) of AGV from the private key stored in car.json'
    )
    
    parser.add_argument(
        '--reg', action='store_true', required=False,
        help='Register the vehicle in the chain'
    )

    parser.add_argument(
        '--verify', type=str, required=False,
        help='Verify battery'
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
    elif args.reg:
        print(register_car(w3))

    elif args.verify:
        data = utils.verify_battery(w3, args.verify)
        print(f"Verified: {data[0]}")
        print(f"Total charges: {data[1]}")
        print(f"Vendor id: {data[2]}")
        print(f"Vendor name: {data[3]}")


if __name__ == "__main__":
    main()
