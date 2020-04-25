import sys
import web3
import argparse
from typing import Union
from web3 import Web3
from web3.middleware import geth_poa_middleware

# Project modules
import utils

URL = "http://127.0.0.1:8545"

ACCOUNT_DB_NAME = 'account.json'
MGMT_CONTRACT_DB_NAME = utils.MGMT_CONTRACT_DB_NAME

CONTRACTS = {'token':  ('contracts/ERC20Token.sol', 'ERC20Token'),
             'wallet': ('contracts/ServiceProviderWallet.sol', 'ServiceProviderWallet'),
             'mgmt':   ('contracts/ManagementContract.sol', 'ManagementContract'),
             'battery': ('contracts/BatteryManagement.sol', 'BatteryManagement')}


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


def setup(_w3: Web3, _service_fee: float) -> Union[dict, None]:
    """
    Deploy and initialize Management, BatteryManagement,
    ServiceProviderWallet and CurrencyToken contracts to the blockchain

    :param Web3 _w3: Web3 instance
    :params float _service_fee: Set fee for battery registration
    :return: Pairs of contract names and their addresses if setup successfull and None if not
    :rtype: dict/None
    """

    service_fee = _w3.toWei(_service_fee, 'ether')

    data = utils.open_data_base(ACCOUNT_DB_NAME)

    if data is None:
        print("Can't access account database")
        return

    actor = data['account']

    utils.unlock_account(_w3, actor, data['password'])

    tx_dict = {}

    for i in ['token', 'wallet']:
        tx_dict[i] = utils._deploy_contract(_w3, actor, CONTRACTS[i][0], CONTRACTS[i][1])

    # wait for deployment transactions validation
    receipt_dict = utils._wait_for_validation(_w3, tx_dict)

    currency_token_contract_addr = receipt_dict['token'][1]['contractAddress']
    service_provider_wallet_addr = receipt_dict['wallet'][1]['contractAddress']

    if (receipt_dict['token'][1] is not None) and (receipt_dict['wallet'][1] is not None):
        currency_token_contract_addr = receipt_dict['token'][1]['contractAddress']
        service_provider_wallet_addr = receipt_dict['wallet'][1]['contractAddress']

        if service_provider_wallet_addr is not None:
            # deploy managment contract
            mgmt_contract_addr = utils._deploy_contract_and_wait(_w3, actor, CONTRACTS['mgmt'][0], CONTRACTS['mgmt'][1], 
                                                           service_provider_wallet_addr, service_fee)
            
            if mgmt_contract_addr is not None:
                utils._create_mgmt_contract_db(mgmt_contract_addr)

                # deploy battery managment
                battery_mgmt_contract_addr = utils._deploy_contract_and_wait(_w3, actor, CONTRACTS['battery'][0], CONTRACTS['battery'][1],
                                                                       mgmt_contract_addr, currency_token_contract_addr)
                
                if battery_mgmt_contract_addr is not None:
                    compiled_contract = utils.compile_contracts(CONTRACTS['mgmt'][0])
                    mgmt_contract = utils.initialize_contract_factory(_w3, compiled_contract,
                                                                      CONTRACTS['mgmt'][0] + ':' + CONTRACTS['mgmt'][1],
                                                                      mgmt_contract_addr)

                    tx_hash = mgmt_contract.functions.setBatteryManagementContract(battery_mgmt_contract_addr).transact({'from': actor, 'gasPrice': utils.get_actual_gas_price(_w3)})
                    receipt = web3.eth.wait_for_transaction_receipt(_w3, tx_hash, 120, 0.1)

                    if receipt.status == 1:
                        contract_addresses = {
                            'Management contract': mgmt_contract_addr,
                            'Wallet contract'    : service_provider_wallet_addr,
                            'Currency contract:' : currency_token_contract_addr
                        }

                        return contract_addresses

    return None


def main() -> None:
    """
    Create cli argument parser and deploy contracts via setup or
    create new developer account via utils.create_new_account function

    :return: Nothing
    :rtype: None
    """

    w3 = Web3(Web3.HTTPProvider(URL))

    # configure provider to work with PoA chains
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    parser = create_parser()
    args = parser.parse_args()

    if args.new:
        print(utils.create_new_account(w3, args.new, ACCOUNT_DB_NAME))
    elif args.setup:
        contract_addresses = setup(w3, args.setup)

        if contract_addresses is None:
            print('Contracts deployment and configuration failed')
        else:
            for key, value in contract_addresses.items():
                print(f"{key}: {value}")

    else:
        sys.exit("No parameters provided")


if __name__ == '__main__':
    main()
