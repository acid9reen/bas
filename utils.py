import os
import json
from typing import Union
from random import random
import web3
from web3 import Web3
from web3._utils.threads import Timeout
from solcx import compile_files


MGMT_CONTRACT_DB_NAME = 'database.json'


def _deploy_contract_and_wait(_w3: Web3, _actor: str, _contract_src_file: str, _contract_name: str, *args):
    """
    Deploy contract to the blockchain

    :param str _actor:The person transacting the contract
    :param str _contract_src_file: Path to contract source code
    :param str _cantract_name: Contract name
    :param list args: Contract's function arguments
    :return: contract address
    :rtype: str
    """

    tx_hash = _deploy_contract(_w3, _actor, _contract_src_file, _contract_name, *args)
    receipt = web3.eth.wait_for_transaction_receipt(_w3, tx_hash, 120, 0.1)

    return receipt["contractAddress"]


def _deploy_contract(_w3: Web3, _actor: str, _contract_src_file: str, _contract_name: str, *args):
    """
    Function definition ???

    :param Web3 _w3: Web3 instance
    :param str _actor: The person transacting the contract
    :param str _contract_src_file: Path to contract source code
    :param str _cantract_name: Contract name
    :param list args: Contract's function arguments
    :return: ?
    :rtype: ?

    """

    compiled = compile_contracts(_contract_src_file)
    contract = initialize_contract_factory(_w3, compiled, _contract_src_file + ":" + _contract_name)

    tx = {'from': _actor, 'gasPrice': get_actual_gas_price(_w3)}

    return contract.constructor(*args).transact(transaction=tx)


def _wait_for_validation(_w3: Web3, _tx_dict: dict, _tmout: int = 120) -> dict:
    receipts_list = {}
    
    for i in _tx_dict.keys():
        receipts_list[i] = [_tx_dict[i], None]
    
    confirmations = len(list(_tx_dict))

    with Timeout(_tmout) as tm:
        while(confirmations > 0):
            for i in _tx_dict.keys():
                if receipts_list[i][1] is None:
                    tx_reciept = _w3.eth.getTransactionReceipt(receipts_list[i][0])

                    if tx_reciept is not None:
                        receipts_list[i][1] = tx_reciept
                        confirmations -= 1
                
                tm.sleep(random())
    
    return receipts_list


def _create_mgmt_contract_db(_contract_address: str) -> None:
    """
    Create json file with Management contract address

    :params str _contract_address: Managment contract address in blockchain
    :return: Nothing
    :rtype: None
    """

    data = {'mgmt_contract': _contract_address}
    write_data_base(data, MGMT_CONTRACT_DB_NAME)


def get_actual_gas_price(_w3: Web3) -> float:
    return _w3.toWei(1, 'gwei')


def write_data_base(_data: dict, _file_name: str) -> None:
    with open(_file_name, 'w') as out:
        json.dump(_data, out)


def unlock_account(_w3: Web3, _account: str, _password: str) -> None:
    _w3.geth.personal.unlockAccount(_account, _password, 60)


def create_new_account(_w3: Web3, _password: str, _file_name: str) -> str:
    if os.path.exists(_file_name):
        os.remove(_file_name)

    account = _w3.geth.personal.newAccount(_password)
    data = {"account": account, "password": _password}
    write_data_base(data, _file_name)

    return data['account']


def open_data_base(_file_name: str) -> Union[dict, None]:
    if os.path.exists(_file_name):
        with open(_file_name) as file:
            return json.load(file)

    else:
        return None


def compile_contracts(_files: Union[str, list]):  # return type?
    if isinstance(_files, str):
        contracts = compile_files([_files])

    if isinstance(_files, list):
        contracts = compile_files(_files)

    return contracts


def get_account_from_db(_file_name: str) -> Union[str, None]:
    data = open_data_base(_file_name)
    
    if data is None:
        return None
    
    return data["account"]


def initialize_contract_factory(_w3: Web3, _compiled_contracts, _key: str, _address: str = None):
    """
    Initialize contract

    :params Web3 _w3: Web3 instance
    :params _compiled_contracts: Compiled contracts
    :params str _key: Contract path + name
    :params str _address: Target adsress
    :return: Contract instance
    :rtype: Contract
    """
    
    if _address is None:
        contract = _w3.eth.contract(
            abi=_compiled_contracts[_key]['abi'],
            bytecode=_compiled_contracts[_key]['bin']
        )
    else:
        contract = _w3.eth.contract(
            abi=_compiled_contracts[_key]['abi'],
            address=_address
        )

    return contract
