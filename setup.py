import sys
import web3
from web3 import Web3
from web3._utils.threads import Timeout
from web3.middleware import geth_poa_middleware
from random import random
import argparse
import utils

URL = "http://127.0.0.1:8545"

w3 = Web3(Web3.HTTPProvider(URL))

ACCOUNT_DB_NAME = 'account.json'
MGMT_CONTRACT_DB_NAME = 'database.json'

GAS_PRICE = utils.get_actual_gas_price(w3)

CONTRACTS = {'token':  ('contracts/ERC20Token.sol', 'ERC20Token'),
             'wallet': ('contracts/ServiceProviderWallet.sol', 'ServiceProviderWallet'),
             'mgmt':   ('contracts/ManagementContract.sol', 'ManagementContract'),
             'battery': ('contracts/BatteryManagement.sol', 'BatteryManagement')}

# configure provider to work with PoA chains
w3.middleware_onion.inject(geth_poa_middleware, layer=0)


def _deploy_contract_and_wait(_actor: str, _contract_src_file: str, _contract_name: str, args=None): # return type?
    tx_hash = _deploy_contract(_actor, _contract_src_file, _contract_name, args)
    receipt = web3.eth.wait_for_transaction_receipt(w3, tx_hash, 120, 0.1)

    return receipt.contractAdress


def _deploy_contract(_actor: str, _contract_src_file: str, _contract_name: str, args=None):
    """
    Function definition ???

    :param str _actor: The person transacting the contract
    :param str _contract_src_file: Path to contract source code
    :param str _cantract_name: Contract name

    :return: ?
    :rtype: ?

    """

    compiled = utils.compile_contracts(_contract_src_file)
    contract = utils.initialize_contract_factory(w3, compiled, _contract_src_file + ":" + _contract_name)

    tx = {'from': _actor, 'gasPrice': GAS_PRICE}

    return contract.constructor().transact(transaction=tx)


def create_parser() -> argparse.ArgumentParser:
    """
    Create cli argument parser

    :return: Parser
    :rtype: argparse.ArgumentParser
    """

    parser = argparse.ArgumentParser(
        description = 'Battery authentication system tool'
    )

    parser.add_argument(
        '--new', type=str, required=False,
        help='Add account for software development company'
    )

    parser.add_argument('--setup', type=float, required=False,
        help='Deploy contract(s) to the chain. Set fee (in ether)' 
              'for registration of one battery, which reflects'
              'vendor registration fee'
    )

    return parser


def _wait_for_validation(_w3: Web3, _tx_dict: dict, _tmout: int = 120) -> dict:
    receipts_list = {}
    
    for i in _tx_dict.keys():
        receipts_list[i] = [_tx_dict[i], None]
    
    confirmations = len(list(_tx_dict))

    with Timeout(_tmout) as tm:
        while(confirmations > 0):
            for i in _tx_dict.keys():
                if receipts_list[i][1] is None:
                    tx_reciept = _w3.eth.Eth.getTransactionReceipt(receipts_list[i][0])

                    if tx_reciept is not None:
                        receipts_list[i][1] = tx_reciept
                        confirmations -= 1
                
                tm.sleep(random())
    
    return receipts_list


def _create_mgmt_contract_db(_contract_address: str) -> None:
    data = {'mgmt_contract': _contract_address}
    utils.write_data_base(data, MGMT_CONTRACT_DB_NAME)


def setup(_service_fee:float) -> None:
    service_fee = w3.toWei(_service_fee, 'ether')

    data = utils.open_data_base(ACCOUNT_DB_NAME)

    if data is None:
        print("Can't access account database")
        return

    actor = data['account']

    utils.unlock_account(w3, actor, data['password'])

    tx_dict = {}

    for i in ['token', 'wallet']:
        tx_dict[i] = _deploy_contract(actor, CONTRACTS[i][0], CONTRACTS[i][1])

    # wait for deployment transactions validation
    receipt_dict = _wait_for_validation(web3, tx_dict)

    currency_token_contract_addr = receipt_dict['token'][1].contractAdress
    service_provider_wallet_addr = receipt_dict['wallet'][1].contractAdress

    if (receipt_dict['token'][1] is not None) and (receipt_dict['wallet'][1] is not None):
        currency_token_contract_addr = receipt_dict['token'][1].contractAdress
        service_provider_wallet_addr = receipt_dict['wallet'][1].contractAdress

        if service_provider_wallet_addr is not None:
            # deploy managment contract
            mgmt_contract_addr = _deploy_contract_and_wait(actor, CONTRACTS['mgmt'][0], CONTRACTS['mgmt'][1], 
                                                           [service_provider_wallet_addr, service_fee])
            
            if mgmt_contract_addr is not None:
                _create_mgmt_contract_db(mgmt_contract_addr)

                # deploy battery managment
                battery_mgmt_contract_addr = _deploy_contract_and_wait(actor, CONTRACTS['battery'][0], CONTRACTS['battery'][1],
                                                                       [mgmt_contract_addr, currency_token_contract_addr])
                
                if battery_mgmt_contract_addr is not None:
                    compiled_contract = utils.compile_contracts(CONTRACTS['mgmt'][0])
                    mgmt_contract = utils.initialize_contract_factory(web3, compiled_contract,
                                                                      CONTRACTS['mgmt'][0] + ':' + CONTRACTS['mgmt'][1],
                                                                      mgmt_contract_addr)

                    tx_hash = mgmt_contract.functions.setBatteryManagementContract(battery_mgmt_contract_addr).transact({'from': actor, 'gasPrice': GAS_PRICE})
                    receipt = web3.eth.wait_for_transaction_receipt(web3, tx_hash, 120, 0.1)

                    if receipt.status == 1:
                        print('Management contract:', mgmt_contract_addr, sep=' ')
                        print('Wallet contract:', service_provider_wallet_addr, sep=' ')
                        print('Currency contract:', currency_token_contract_addr, sep=' ')

                        return

    print('Contracts deployment and configuration failed')


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    if args.new:
        print(utils.create_new_account(w3, args.new, ACCOUNT_DB_NAME))
    elif args.setup:
        setup(args.setup)
    else:
        sys.exit("No parameters provided")


if __name__ == '__main__':
    main()
