import sys
from web3 import Web3
from web3.eth import wait_for_transaction_receipt
import argparse
import utils

URL = "http://127.0.0.1:8545"

w3 = Web3(Web3.HTTPProvider(URL))

ACCOUNT_DB_NAME = 'account.json'

GAS_PRICE = utils.get_actual_gas_price(w3)

contracts = {'token':  ('contracts/ERC20Token.sol', 'ERC20Token'),
             'wallet': ('contracts/ServiceProviderWallet.sol', 'ServiceProviderWallet'),
             'mgmt':   ('contracts/ManagementContract.sol', 'ManagementContract'),
             'battery':('contracts/BatteryManagement.sol', 'BatteryManagement')}


def _deploy_contract_and_wait(_actor, _contract_src_file, _contract_name, args=None):
    tx_hash = _deploy_contract(_actor, _contract_src_file, _contract_name, args)
    receipt = wait_for_transaction_receipt(w3, tx_hash, 120, 0.1)

    return receipt.contractAdress


def _deploy_contract(_actor, _contract_src_file, _contract_name, args=None):
    compiled = utils.compile_contracts(_contract_src_file)
    contract = utils.initialize_contract_factory(w3, compiled, _contract_src_file + ":" + _contract_name)

    tx = {'from': _actor, 'gasPrice': GAS_PRICE}

    return contract.deploy(transaction=tx, args=args)


def create_parser():
    parser = argparse.ArgumentParser(
        description = 'Battery authentication system tool'
    )

    parser.add_argument('--new', type=str, required=False,
        help='Add account for software development company'
    )

    parser.add_argument('--setup', type=float, required=False,
        help='Deploy contract(s) to the chain. Set fee (in ether)' 
             'for registration of one battery, which reflects'
             'vendor registration fee'
    )

    return parser


def setup(_service_fee):
    service_fee = w3.toWei(_service_fee, 'ether')

    data = utils.open_data_base(ACCOUNT_DB_NAME)

    if data is None:
        print("Can't access account database")
        return

    actor = data['account']

    utils.unlock_account(w3, actor, data['password'])

    txd = {}
    for i in ['token', 'wallet']:
        txd[i] = _deploy_contract(actor, contracts[i][0], contracts[i][1])


def main():
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
