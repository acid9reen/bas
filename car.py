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


class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'


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

    return (_w3.eth.account.privateKeyToAccount(utils.get_data_from_db(ACCOUNT_DB_NAME, 'key')).address)


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
        return 'Registered successfully'        
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
    """
    Get address of the service center

    return: Service center's address
    rtype: str
    """

    command = "python scenter.py --get_address".split(' ')
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    return result.stdout[:-1]


def transfer_battery_to_sc(w3: Web3, car_battery_id: str, sc_address: str):
    """
    Transfer battery to service center

    :param Web3 w3: Web3 instance
    :param str car_battery_id: Car's battery id
    :param str sc_battery_id: Service centers's battery id

    return: Nothing
    rtype: None
    """

    data = utils.open_data_base(MGMT_CONTRACT_DB_NAME)

    if data is None:
        return 'Cannot access management contract database'
        
    data = utils.open_data_base(ACCOUNT_DB_NAME)

    if data is None:
        return 'Cannot access account database'

    private_key = data['key']
    battery_mgmt_contract_addr = utils.get_battery_managment_contract_addr(w3)
    battery_mgmt_contract = utils.init_battery_management_contract(w3, battery_mgmt_contract_addr)
    car_address = w3.eth.account.privateKeyToAccount(private_key).address
    gas_price = utils.get_actual_gas_price(w3)

    nonce = w3.eth.getTransactionCount(car_address)
    tx = {'gasPrice': gas_price, 'nonce': nonce, 'gas': 2204 * 68 + 21000}

    reg_tx = battery_mgmt_contract.functions.transfer(sc_address, decode_hex(car_battery_id)).buildTransaction(tx)
    sign_tx = w3.eth.account.signTransaction(reg_tx, private_key)
    tx_hash = w3.eth.sendRawTransaction(sign_tx.rawTransaction)
    receipt = web3.eth.wait_for_transaction_receipt(w3, tx_hash, 120, 0.1)

    if receipt.status != 1:
        sys.exit("The car does not own this battery!")


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

    print("Verifying battery...")

    data = utils.verify_battery(w3, sc_battery_id_path)

    if not data[0]:
        sys.exit("The battery is fake")

    sys.stdout.write("\033[F") #back to previous line
    sys.stdout.write("\033[K") #clear line

    print(f"Verifying battery...{bcolors.OKGREEN}Success{bcolors.ENDC}", u'\u2713')

    print("Asking service center for replacement...")

    ask_for_replacement(car_battery_id, sc_battery_id, get_car_account_from_db(w3))

    message = utils.open_data_base('replacement.json')

    if message is None:
        sys.exit("Somethong went wrong...")
    
    if not message['approved']:
        sys.exit(message['error'])
    
    sys.stdout.write("\033[F") #back to previous line
    sys.stdout.write("\033[K") #clear line

    print(f"Asking service center for replacement...{bcolors.OKGREEN}Approved{bcolors.ENDC}", u'\u2713')

    print("Getting address of the service center...")
    
    sc_address = get_sc_address()

    sys.stdout.write("\033[F") #back to previous line
    sys.stdout.write("\033[K") #clear line

    print(f"Getting address of the service center...{bcolors.OKGREEN}Success{bcolors.ENDC}", u'\u2713')

    print("Transferring battery to the service center...")

    transfer_battery_to_sc(w3, car_battery_id, sc_address)

    sys.stdout.write("\033[F") #back to previous line
    sys.stdout.write("\033[K") #clear line

    print(f"Transferring battery to the service center...{bcolors.OKGREEN}Success{bcolors.ENDC}", u'\u2713')

    print("Waiting for new battery installation...")

    result = get_new_battery(get_car_account_from_db(w3), car_battery_id, sc_battery_id)

    sys.stdout.write("\033[F") #back to previous line
    sys.stdout.write("\033[K") #clear line

    print(f"Battery was installed...{bcolors.OKGREEN}Success{bcolors.ENDC}", u'\u2713')
    
    return result


def main():
    w3 = Web3(Web3.HTTPProvider(URL))

    # configure provider to work with PoA chains
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    parser = create_parser()
    args = parser.parse_args()

    if args.new:
        new_car_account(w3)
    
    elif args.account:
        print(get_car_account_from_db(w3))

    elif args.reg:
        print(register_car(w3))

    elif args.verify:
        data = utils.verify_battery(w3, args.verify)
        print(f"Verified: {data[0]}")
        print(f"Total charges: {data[1]}")
        print(f"Vendor id: {data[2]}")
        print(f"Vendor name: {data[3]}")
    
    elif args.initiate_replacement:
        cost = initiate_replacement(w3, args.initiate_replacement[0], args.initiate_replacement[1])
        print(f"Cost of work: {cost} eth")


if __name__ == "__main__":
    main()
