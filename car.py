import sys, os
import subprocess
import datetime as dt
from random import randint
import argparse
import web3
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_utils import decode_hex

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

    actor = data['account']
    tx = {'from': actor, 'gasPrice': utils.get_actual_gas_price(_w3)}

    mgmt_contract = utils.init_management_contract(_w3)

    utils.unlock_account(_w3, actor, data['password'])


    registration_required_gas = 50000
    gas_price = utils.get_actual_gas_price(_w3)

    if registration_required_gas * gas_price > _w3.eth.getBalance(actor):
        return 'No enough funds to send transaction'


    try:
        tx_hash = mgmt_contract.functions.registerCar().transact(tx)
    except ValueError:
        sys.exit("Already registered")

    receipt = web3.eth.wait_for_transaction_receipt(_w3, tx_hash, 120, 0.1)

    if receipt.status == 1:
        return "Registered successfully"
    
    else:
        return "Registration failed"


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
        '--new', type=str, required=False,
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

    parser.add_argument(
        '--initiate_replacement', nargs=2, required=False,
        help='Initiate deal <car_battery> <sc_battery>'
    )

    return parser


def ask_for_replacement(car_battery_id: str, sc_battery_id: str, car_address: str) -> None:
    """
    Ask service center for replacement approval

    :param str car_battery_id: Car's battery
    :param str sc_battery_id: Service center's battery
    :param str car_address: Car's blockchain address
    :return: Nothing
    :rtype: None 
    """

    if os.path.exists(f"scenter.py"):
        subprocess.run(
            [
                "python", 
                "scenter.py", 
                "--approve_replacement",
                f"{car_battery_id}",
                f"{sc_battery_id}",
                f"{car_address}",
            ]
        )
    else:
        sys.exit("The asked service center does not exists")


def get_sc_address() -> str:
    command = "python scenter.py --get_address".split(' ')
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    return result.stdout[:-1]


def transfer_battery_to_sc(w3: Web3, car_battery_id: str, sc_address: str):
    """

    """

    result = utils.change_owner(w3, car_battery_id, sc_address, ACCOUNT_DB_NAME)

    if 'failed' in result:
        sys.exit("Something went wrong...")


def get_new_battery(car_account: str, car_battery_id: str, sc_battery_id) -> float:
    """
    Call battery replacement in service center

    :param str car_account: Car account
    :param str car_battery_id: Car's battery id
    :return: Work's cost
    :rtype: float
    """

    command = f"python scenter.py --transfer_battery_to_car {car_account} {car_battery_id} {sc_battery_id}".split(' ')
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    return float(result.stdout[:-1])


def initiate_replacement(w3: Web3, car_battery_id: str, sc_battery_id: str) -> None:
    """
    Initiate battery replacement

    :param Web3 w3: Web3 instance
    :param str car_battery_id: Car's battery
    :param str sc_battery_id: Service center's battery
    :return: Nothing
    :rtype: None
    """

    sc_battery_id_path = f"firmware/{car_battery_id[:8]}.py"
    car_battery_id_path = f"firmware/{sc_battery_id[:8]}.py"

    data = utils.verify_battery(w3, sc_battery_id_path)

    if not data[0]:
        sys.exit("The battery is fake")

    data = utils.open_data_base(ACCOUNT_DB_NAME)
    actor = data['account']

    ask_for_replacement(car_battery_id, sc_battery_id, actor)

    message = utils.open_data_base('replacement.json')

    if message is None:
        sys.exit("Somethong went wrong...")
    
    if not message['approved']:
        sys.exit(message['error'])
    
    sc_address = get_sc_address()

    transfer_battery_to_sc(w3, car_battery_id, sc_address)
    
    return get_new_battery(actor, car_battery_id, sc_battery_id)


def main():
    w3 = Web3(Web3.HTTPProvider(URL))

    # configure provider to work with PoA chains
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    parser = create_parser()
    args = parser.parse_args()

    if args.new:
        print(utils.create_new_account(w3, args.new, ACCOUNT_DB_NAME))

    elif args.reg:
        print(register_car(w3))

    elif args.verify:
        data = utils.verify_battery(w3, args.verify)
        print(f"Verified: {data[0]}")
        print(f"Total charges: {data[1]}")
        print(f"Vendor id: {data[2]}")
        print(f"Vendor name: {data[3]}")
    
    elif args.initiate_replacement:
        print("Cost of work:")
        print(f"{initiate_replacement(w3, args.initiate_replacement[0], args.initiate_replacement[1])} eth")


if __name__ == "__main__":
    main()
    