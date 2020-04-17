import os
import json
from solc import compile_files


def get_actual_gas_price(_w3):
    return _w3.toWei(1, 'gwei')


def write_data_base(_data, _file):
    with open(_file, 'w') as out:
        json.dump(_data, out)


def unlock_account(_w3, _account, _password):
    _w3.personal.unlockAccount(_account, _password, 60)


def create_new_account(_w3, _password, _file):
    if os.path.exists(_file):
        os.remove(_file)

    account = _w3.geth.personal.newAccount(_password)
    data = {"account": account, "password": _password}
    write_data_base(data, _file)

    return data['account']


def open_data_base(_file):
    if os.path.exists(_file):
        with open(_file) as file:
            return json.load(file)

    else:
        return None


def compile_contracts(_files):
    if isinstance(_files, str):
        contracts = compile_files([_files])

    if isinstance(_files, list):
        contracts = compile_files(_files)

    return contracts


def initialize_contract_factory(_w3, _compiled_contracts, _key, _address=None):
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
