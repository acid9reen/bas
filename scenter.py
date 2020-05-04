import sys, os
import subprocess
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


def get_battery_info(_path: str) -> dict:
    """
    Get battery info(v, r, s, charges, time)

    :param str _path: Path to battery's firmware
    :return: Battery's info
    :rtype: dict
    """

    try:
        subprocess.run(["python", f"{_path}", "--get"])
    except:
        sys.exit("Battery does not exist")

    return utils.open_data_base(f"{_path[:-3]}_data.json")


def verify_battery(_w3: Web3, _path: str):
    """
    Verify battery firmware

    :param Web3 _w3: Web3 instance
    :param str _path: Path to firmware
    :return:
    :rtype:
    """

    verified = False
    battery_info = get_battery_info(_path)

    battery_mgmt_addr = utils.get_battery_managment_contract_addr(_w3)
    battery_mgmt_contract = utils.init_battery_management_contract(_w3, battery_mgmt_addr)

    # TODO implement verifyBattery in battery management contract
    verified, vendor_address = battery_mgmt_contract.functions.verifyBattery(battery_info['v'], _w3.toBytes(hexstr=battery_info['r']),
                                                             _w3.toBytes(hexstr=battery_info['s']), battery_info['charges'],
                                                             battery_info['time']).call()

    mgmt_contract = utils.init_management_contract(_w3)
    vendor_id = _w3.toHex(mgmt_contract.functions.vendorId(vendor_address).call())
    vendor_name = (mgmt_contract.functions.vendorNames(vendor_id).call()).decode()

    return verified, battery_info['charges'], vendor_id, vendor_name


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
        data = verify_battery(w3, args.verify)
        print(f"Verified: {data[0]}")
        print(f"Total charges: {data[1]}")
        print(f"Vendor id: {data[2]}")
        print(f"Vendor name: {data[3]}")

    else:
        sys.exit("No parameters provided")


if __name__ == "__main__":
    main()
