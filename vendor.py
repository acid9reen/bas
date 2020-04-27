import sys, os
import argparse
import web3
from web3 import Web3
from web3.middleware import geth_poa_middleware

# Project modules
import utils


URL = "http://127.0.0.1:8545"

ACCOUNT_DB_NAME = 'account.json'
MGMT_CONTRACT_DB_NAME = utils.MGMT_CONTRACT_DB_NAME
MGMT_CONTRACT_SRC_PATH = r"./contracts/ManagementCOntract.sol"
MGMT_CONTRACT_NAME = "ManagementCOntract"


CONFIG = utils.open_data_base(ACCOUNT_DB_NAME)
#GAS_PRICE = utils.get_actual_gas_price(w3)

#if CONFIG is not None:
#    TX_TEMPLATE = {'from': CONFIG['account'], 'gasPrice': GAS_PRICE}

DATABASE = utils.open_data_base(MGMT_CONTRACT_DB_NAME)

# Create empty dict for database dump
if DATABASE is None:
    sys.exit("Setup hasn't been done")


def init_management_contract(_w3: Web3):
    """
    Creates management contract object

    :param Web3 _w3: Web3 instance
    :return: Management contract
    :rtype: Contract instance
    """

    compiled = utils.compile_contracts(MGMT_CONTRACT_SRC_PATH)
    mgmt_contract = utils.initialize_contract_factory(_w3, compiled, MGMT_CONTRACT_SRC_PATH + ":" + MGMT_CONTRACT_NAME,
                                                      DATABASE["mgmt_contract"])
    
    return mgmt_contract


def register_vendor(_w3: Web3, _name: str, _deposit: float):
    """
    Register new vendor

    :param Web3 _w3: Web3 instance
    :param str _name: Vendor's name
    :param float _deposit: Vendor's deposit in eth
    :return: Vendor id or error message
    :rtype: str
    """

    mgmt_contract = init_management_contract(_w3)
    tx = TX_TEMPLATE

    if _w3.eth.getBalance(tx['from']) < _deposit:
        return "Failed. No enough funds to deposit."
    
    else:
        try:
            tx['value'] = _deposit
            tx_hash = mgmt_contract.functions.registerVendor(_name.encode()).transact(tx)
            receipt = web3.eth.wait_for_transaction_receipt(_w3, tx_hash, 120, 0.1)

            if receipt.status == 1:
                return mgmt_contract.events.Vendor().processReceipt(receipt)[0]['args']['tokenId']

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

    mgmt_contract = init_management_contract(_w3)
    txHash = mgmt_contract.functions.registerBatteries(args).transact(tx)
    receipt = web3.eth.wait_for_transaction_receipt(_w3, txHash, 120, 0.1)
    result = receipt.status

    if result >= 1:
        return bat_keys
        
    else:
        return 'Batteries registration failed'


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

    return parser


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


def main() -> None:
    w3 = Web3(Web3.HTTPProvider(URL))

    # configure provider to work with PoA chains
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    parser = create_parser()
    args = parser.parse_args()

    config = utils.open_data_base("account.json")

    if config is None:
        sys.exit("Can't access account database")

    actor = w3.toChecksumAddress(config[ACCOUNT_DB_NAME])
    gas_price =  utils.get_actual_gas_price(w3)
    
    global TX_TEMPLATE
    TX_TEMPLATE = {'from': actor, 'gasPrice': gas_price}

    if args.new:
        print(utils.create_new_account(w3, args.new, ACCOUNT_DB_NAME))

    elif args.reg:
        w3.geth.personal.unlockAccount(actor, config['password'], 300)

        result = register_vendor(web3, args.reg[0], w3.toWei(args.reg[1], 'ether'))

        if isinstance(result, bytes):
            print(f'Success.\nVendor ID: {del_hex_prefix(w3.toHex(result))}')
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
                print(bat_id)
        else:
            print(result)

    else:
        sys.exit("No parameters provided")


if __name__ == "__main__":
    main()
