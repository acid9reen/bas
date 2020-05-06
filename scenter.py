import sys, os
import argparse
import web3
from web3 import Web3
from web3.middleware import geth_poa_middleware

# Project modules
import utils

URL = "http://127.0.0.1:8545"

MGMT_CONTRACT_DB_NAME = utils.MGMT_CONTRACT_DB_NAME
MGMT_CONTRACT_SRC_PATH = utils.MGMT_CONTRACT_SRC_PATH
MGMT_CONTRACT_NAME = utils.MGMT_CONTRACT_NAME
REGISTRATION_REQUIRED_GAS = utils.REGISTRATION_REQUIRED_GAS
ACCOUNT_DB_NAME = 'scenter.json'

def create_parser() -> argparse.ArgumentParser:
    """
    Create cli argument parser

    :return: Parser
    :rtype: argparse.ArgumentParser
    """

    parser = argparse.ArgumentParser(
        description='Service provider tool',
        epilog="""
               It is expected that Web3 provider specified by WEB3_PROVIDER_URI
               environment variable. E.g.
               WEB3_PROVIDER_URI=file:///path/to/node/rpc-json/file.ipc
               WEB3_PROVIDER_URI=http://192.168.1.2:8545
               """
    )

    parser.add_argument(
        '--new', type=str, required=False,
        help='Add new service scenter account'
    )

    parser.add_argument(
        '--reg', action='store_true', required=False,
        help='Register service scenter in the chain'
    )

    parser.add_argument(
        '--verify', type=str, required=False,
        help='Verify battery'
    )

    parser.add_argument(
        '--approve_replacement', nargs=3, required=False,
        help="Battery replacement <car_battery> <sc_battery> <car_address>"
    )

    parser.add_argument(
        '--get_address', action='store_true', required=False,
        help='Get address of service center'
    )

    parser.add_argument(
        '--transfer_battery_to_car', nargs=3, required=False,
        help='Transfer battery to the car <car_account> <car_battery_id> <sc_battery_id>'
    )

    return parser


def register_scenter(_w3: Web3):
    """
    Register new service center

    :param Web3 _w3: Web3 instance
    :return: Registration status message
    :rtype: str
    """

    mgmt_contract = utils.init_management_contract(_w3)
    data = utils.open_data_base(ACCOUNT_DB_NAME)

    if data is None:
        sys.exit("Cannot access account database")
    
    actor = data['account']

    tx = {'from': actor, 'gasPrice': utils.get_actual_gas_price(_w3)}

    if REGISTRATION_REQUIRED_GAS * tx['gasPrice'] > _w3.eth.getBalance(actor):
        sys.exit("No enough funds to send transaction")
    
    utils.unlock_account(_w3, actor, data['password'])

    try:
        tx_hash = mgmt_contract.functions.registerServiceCenter().transact(tx)
    except ValueError:
        sys.exit("Already registered")

    receipt = web3.eth.wait_for_transaction_receipt(_w3, tx_hash, 120, 0.1)

    if receipt.status == 1:
        return "Registered successfully"
    
    else:
        return "Registration failed"


def approve_replacement(w3: Web3, car_battery_id: str, sc_battery_id: str, car_address: str) -> None:
    """

    """

    sc_battery_id_path = f"firmware/{car_battery_id[:8]}.py"
    car_battery_id_path = f"firmware/{sc_battery_id[:8]}.py"

    data = utils.verify_battery(w3, car_battery_id_path)
    message = {'approved': False}

    if data[0]:
        message['approved'] = True
    
    message['error'] = "Car's battery probably is fake"

    utils.write_data_base(message, 'replacement.json')
        

def get_addr() -> str:
    data = utils.open_data_base(ACCOUNT_DB_NAME)
    return data['account']


def get_work_cost(car_battery_id, sc_battery_id) -> float:
    return 0.005


def transfer_battery_to_car(w3: Web3, car_account: str, car_battery_id: str, sc_battery_id) -> float:
    utils.change_owner(w3, car_battery_id, car_account, ACCOUNT_DB_NAME)

    return get_work_cost(car_battery_id, sc_battery_id)


def main() -> None:
    w3 = Web3(Web3.HTTPProvider(URL))

    # configure provider to work with PoA chains
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    parser = create_parser()
    args = parser.parse_args()

    if args.new:
        print(utils.create_new_account(w3, args.new, ACCOUNT_DB_NAME))
   
    elif args.reg:
        print(register_scenter(w3))
    
    elif args.verify:
        data = utils.verify_battery(w3, args.verify)
        print(f"Verified: {data[0]}")
        print(f"Total charges: {data[1]}")
        print(f"Vendor id: {data[2]}")
        print(f"Vendor name: {data[3]}")

    elif args.approve_replacement:
        approve_replacement(w3, args.approve_replacement[0], args.approve_replacement[1], args.approve_replacement[2])
    
    elif args.get_address:
        print(get_addr())

    elif args.transfer_battery_to_car:
        print(transfer_battery_to_car(w3, args.transfer_battery_to_car[0], args.transfer_battery_to_car[1], args.transfer_battery_to_car[2]))

    else:
        sys.exit("No parameters provided")


if __name__ == "__main__":
    main()
