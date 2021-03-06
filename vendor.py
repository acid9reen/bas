import sys, os
import argparse
import web3
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.logs import DISCARD
from eth_utils import decode_hex

# Project modules
import utils
from TextColor.color import bcolors


URL = "http://127.0.0.1:8545"

ACCOUNT_DB_NAME = 'account.json'
MGMT_CONTRACT_DB_NAME = utils.MGMT_CONTRACT_DB_NAME
MGMT_CONTRACT_SRC_PATH = r"./contracts/ManagementContract.sol"
MGMT_CONTRACT_NAME = "ManagementContract"


CONFIG = utils.open_data_base(ACCOUNT_DB_NAME)
DATABASE = utils.open_data_base(MGMT_CONTRACT_DB_NAME)

# Create empty dict for database dump
if DATABASE is None:
    sys.exit(f"{bcolors.FAIL}Setup hasn't been done{bcolors.ENDC}")


def register_vendor(_w3: Web3, _name: str, _deposit: float):
    """
    Register new vendor

    :param Web3 _w3: Web3 instance
    :param str _name: Vendor's name
    :param float _deposit: Vendor's deposit in eth
    :return: Vendor id or error message
    :rtype: str
    """

    mgmt_contract = utils.init_management_contract(_w3)
    tx = TX_TEMPLATE

    if _w3.eth.getBalance(tx['from']) < _deposit:
        return "Failed. No enough funds to deposit."
    
    if _w3.eth.getBalance(tx['from']) + _deposit < get_fee(_w3) * 1000:
        return "Failed. Not enough funds to register"
    
    else:
        try:
            tx['value'] = _deposit
            tx_hash = mgmt_contract.functions.registerVendor(_name.encode()).transact(tx)
            receipt = web3.eth.wait_for_transaction_receipt(_w3, tx_hash, 120, 0.1)

            if receipt.status == 1:
                return mgmt_contract.events.Vendor().processReceipt(receipt, errors=DISCARD)[0]['args']['tokenId']

        except ValueError:
            return "Failed. The vendor name is not unique."


def register_battery(_w3: Web3, _count: int, _value: float=0):
    """
    Register battery

    :param Web3 _w3: Web3 instance
    :param int _count: Number of batteries
    :param float _value: Deposit in eth
    :return: Batteries ids or error message
    :rtype: str
    """

    tx = TX_TEMPLATE
    tx['value'] = _value
    bat_keys = []
    args = []
    
    for i in range(_count):
        priv_key = _w3.sha3(os.urandom(20))
        bat_keys.append((priv_key, _w3.eth.account.privateKeyToAccount(priv_key).address))

    for i in range(len(bat_keys)):
        args.append(_w3.toBytes(hexstr=bat_keys[i][1]))

    mgmt_contract = utils.init_management_contract(_w3)
    txHash = mgmt_contract.functions.registerBatteries(args).transact(tx)
    receipt = web3.eth.wait_for_transaction_receipt(_w3, txHash, 120, 0.1)
    result = receipt.status

    if result >= 1:
        for battery in bat_keys:
            utils.create_script_from_tmpl(hex(int.from_bytes(battery[0], byteorder='big')),
                                          battery[1])


        return [x[1] for x in bat_keys]
        
    else:
        sys.exit('Batteries registration failed')


def create_parser() -> argparse.ArgumentParser:
    """
    Create cli argument parser

    :return: Parser
    :rtype: argparse.ArgumentParser
    """

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

    parser.add_argument(
        '--reg', nargs=2, required=False,
        help='Register a vendor'
    )

    parser.add_argument(
        '--bat', nargs="+", required=False,
        help='Register batteries'
    )

    parser.add_argument(
        '--regfee', action='store_true', required=False,
        help='Show registration fee for vendor'
    )

    parser.add_argument(
        '--batfee', action='store_true', required=False,
        help='Show registration fee per battery'
    )

    parser.add_argument(
        '--deposit', action='store_true', required=False,
        help="Show vendor's deposit"
    )

    parser.add_argument(
        '--owner', nargs=2, required=False,
        help='Change battery owner'
    )

    return parser


def get_fee(_w3: Web3) -> float:
    """
    Get registration fee from managmentContract

    :param Web3_w3: Web3 instance
    :return: Service fee
    :rtype: float
    """

    mgmt_contract = utils.init_management_contract(_w3)

    fee = mgmt_contract.functions.getFee().call()

    return _w3.fromWei(fee, 'ether')


def get_deposit(_w3: Web3):
    """
    Get account deposit

    :param Web3 _w3: Web3 instance
    :return: Vendor's deposit in ether
    :rtype: float
    """

    data = utils.open_data_base(ACCOUNT_DB_NAME)
    actor = data['account']

    mgmt_contract = utils.init_management_contract(_w3)

    try:
        deposit = mgmt_contract.functions.getDeposit().call({'from': actor})

        return _w3.fromWei(deposit, 'ether')

    except:
        sys.exit(f"{bcolors.FAIL}The vendor doesn't exist{bcolors.ENDC}")    


def del_hex_prefix(_str: str) -> str:
    """
    Delete 0x prefix

    :params str _str: String with 0x orefix to delete
    :return: String without 0x prefix
    :rtype: str
    """

    if _str[:2] == '0x': 
        return _str
    return _str


def change_owner(_w3: Web3, _battery_id: str, _new_owner: str) -> str:
    """
    Change the owner of battery

    :param Web3 _w3: Web3 instance
    :param str _battery_id: battery ID
    :param str _new_owner: New owner address
    :return: Status message
    :rtype: str    

    """

    data = utils.open_data_base(ACCOUNT_DB_NAME)
    actor = data['account']

    tx = {'from': actor, 'gasPrice': utils.get_actual_gas_price(_w3), 'gas': 2204 * 68 + 21000}

    battery_mgmt_contract_addr = utils.get_battery_managment_contract_addr(_w3)
    battery_mgmt_contract = utils.init_battery_management_contract(_w3, battery_mgmt_contract_addr)

    utils.unlock_account(_w3, actor, data['password'])

    tx_hash = battery_mgmt_contract.functions.transfer(_new_owner, decode_hex(_battery_id)).transact(tx)
    receipt = web3.eth.wait_for_transaction_receipt(_w3, tx_hash, 120, 0.1)
    result = receipt.status

    if result == 1:
        return f"{bcolors.OKGREEN}Ownership change was successfull{bcolors.ENDC}"
    else:
        return f"{bcolors.FAIL}Ownership change failed{bcolors.ENDC}"


def main() -> None:
    w3 = Web3(Web3.HTTPProvider(URL))

    # configure provider to work with PoA chains
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    parser = create_parser()
    args = parser.parse_args()

    config = utils.open_data_base("account.json")

    if config is None:
        sys.exit(f"{bcolors.FAIL}Can't access account database{bcolors.ENDC}")

    actor = w3.toChecksumAddress(config['account'])
    gas_price =  utils.get_actual_gas_price(w3)
  
    global TX_TEMPLATE
    TX_TEMPLATE = {'from': actor, 'gasPrice': gas_price}

    if args.new:
        print(utils.create_new_account(w3, args.new, ACCOUNT_DB_NAME))

    elif args.reg:
        w3.geth.personal.unlockAccount(actor, config['password'], 300)

        result = register_vendor(w3, args.reg[0], w3.toWei(float(args.reg[1]), 'ether')) 

        if isinstance(result, bytes):
            print(f'{bcolors.OKGREEN}Success{bcolors.ENDC}\nVendor ID: {bcolors.HEADER}{del_hex_prefix(w3.toHex(result))}{bcolors.ENDC}')
        else:
            sys.exit(result)
    
    elif args.bat:
        w3.geth.personal.unlockAccount(actor, config['password'], 300)

        if len(args.bat) == 1:
            result = register_battery(w3, int(args.bat[0]))
        else:
            result = register_battery(w3, int(args.bat[0]), Web3.toWei(float(args.bat[1])))

        if isinstance(result, list):
            for bat_id in result:
                print(f'Created battery with id: {bcolors.HEADER}{bat_id[2:]}{bcolors.ENDC}')

    elif args.regfee:
        print(f'Vendor registration fee: {bcolors.HEADER}{get_fee(w3) * 1000}{bcolors.ENDC} eth')
    
    elif args.batfee:
        print(f'Battery registration fee: {bcolors.HEADER}{get_fee(w3)}{bcolors.ENDC} eth')

    elif args.deposit:
        print(f"Vendor deposit: {bcolors.HEADER}{get_deposit(w3)}{bcolors.ENDC} eth")

    elif args.owner:
        print(change_owner(w3, args.owner[0], args.owner[1]))

    else:
        sys.exit(f"{bcolors.FAIL}No parameters provided{bcolors.ENDC}")


if __name__ == "__main__":
    main()
