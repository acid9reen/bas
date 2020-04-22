import os
import json
from typing import Union
from web3 import Web3
from solc import compile_files


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


def initialize_contract_factory(_w3: Web3, _compiled_contracts, _key: str, _address: str = None):  # return type?
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
