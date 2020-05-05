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
        '--contract', nargs=4, required=False,
        help="Get replacement contract"
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


def create_deal(_w3: Web3, _bat_new: str, _bat_old: str, _car: str, _service_price: int):
    data = utils.open_data_base(ACCOUNT_DB_NAME)
    
    if data is None:
        sys.exit('Cannot access account database')
    
    actor = data['account']
    tx = {'from': actor, 'gasPrice': utils.get_actual_gas_price(_w3)}

    utils.unlock_account(_w3, actor, data['password'])
  
    
    if not os.path.exists(_bat_old):
        sys.exit('Cannot access service center\'s battery')

    car_battery_info = utils.get_battery_info(_bat_old)
    v_old = car_battery_info['v']
    r_old = car_battery_info['r']
    s_old = car_battery_info['s']
    charges_old = car_battery_info['charges']
    time_old = car_battery_info['time']

    if not os.path.exists(_bat_new):
        sys.exit('Cannot access car\'s battery')

    sc_battery_info = utils.get_battery_info(_bat_new)
    v_new = sc_battery_info['v']
    r_new = sc_battery_info['r']
    s_new = sc_battery_info['s']
    charges_new = sc_battery_info['charges']
    time_new = sc_battery_info['time']

    p = (charges_old * (1 << 160) + time_old * (1 << 128) + v_old * (1 << 96) 
         + charges_new * (1 << 64) + time_new * (1 << 32) + v_new)

    battery_mgmt_contract_address = utils.get_battery_managment_contract_addr(_w3)
    battery_mgmt_contract = utils.init_battery_management_contract(_w3, battery_mgmt_contract_address)
    
    try:
        tx_hash = battery_mgmt_contract.functions.initiateDeal(p, _w3.toBytes(hexstr=r_old),
                                                              _w3.toBytes(hexstr=s_old), _w3.toBytes(hexstr=r_new),
                                                              _w3.toBytes(hexstr=s_new),_car, _service_price).transact(tx)
        
        receipt = web3.eth.wait_for_transaction_receipt(_w3, tx_hash, 120, 0.1)

        if receipt.status == 0:
            sys.exit("Deal was not created.")

    except BaseException as error:
        
       # if error.args[0]['message'] == 'insufficient funds for gas * price + value':
        #    sys.exit('No enough funds to send transaction')

        sys.exit("Deal was not created.")
    
    logs = battery_mgmt_contract.events.NewDeal().processReceipt(receipt)[::-1]

    for log in logs:
        try:
            if log['args']['newDeal']:
                address_new_deal = log['args']['newDeal']
                print(f"Deal: {address_new_deal}")
                return
        except:
            return


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

    elif args.contract:
        bat_old = args.contract[0]
        bat_new = args.contract[1]
        car = args.contract[2]
        service_price = int(args.contract[3])
        create_deal(w3, bat_old, bat_new, car, service_price)

    else:
        sys.exit("No parameters provided")


if __name__ == "__main__":
    main()
