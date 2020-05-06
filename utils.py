import sys, os
import subprocess
import json
from typing import Union
from random import random
import web3
from web3 import Web3
from web3._utils.threads import Timeout
from solcx import compile_files
from eth_utils import decode_hex


MGMT_CONTRACT_DB_NAME = 'database.json'
MGMT_CONTRACT_SRC_PATH = r"./contracts/ManagementContract.sol"
MGMT_CONTRACT_NAME = "ManagementContract"
BATTERY_MGMT_CONTRACT_SRC_PATH = r"./contracts/BatteryManagement.sol"
BATTERY_MGMT_CONTRACT_NAME = "BatteryManagement"
REGISTRATION_REQUIRED_GAS = 50000


def _deploy_contract_and_wait(_w3: Web3, _actor: str, _contract_src_file: str, _contract_name: str, *args):
    """
    Deploy contract to the blockchain and wait it's inclusion to a block

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
    Deploy contract to the blockchain

    :param Web3 _w3: Web3 instance
    :param str _actor: The person transacting the contract
    :param str _contract_src_file: Path to contract source code
    :param str _cantract_name: Contract name
    :param list args: Contract's function arguments
    :return: Deployed contract
    :rtype: Contract
    """

    compiled = compile_contracts(_contract_src_file)
    contract = initialize_contract_factory(_w3, compiled, _contract_src_file + ":" + _contract_name)

    tx = {'from': _actor, 'gasPrice': get_actual_gas_price(_w3)}

    return contract.constructor(*args).transact(transaction=tx)


def _wait_for_validation(_w3: Web3, _tx_dict: dict, _tmout: int = 120) -> dict:
    """
    Wait contract's inclusion to a block

    :params Web3 _w3: Web3 instance
    :params dict _tx_dict: Transactions waiting for inclusion
    :params int: _tmout: Timeout for inclusion to a block in seconds
    :return: Receipts
    :rtype: dict
    """

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
    """
    Get actual gas price

    :param Web3 _w3: Web3 instance
    :return: Gas price
    :rtype: float
    """

    return _w3.toWei(1, 'gwei')


def write_data_base(_data: dict, _file_name: str) -> None:
    """
    Write dictionary to specific json file

    :param dict _data: Data to write
    :param str _file_name: Name of the file for writing
    :return: Nothing
    :rtype: None
    """

    with open(_file_name, 'w') as out:
        json.dump(_data, out)


def unlock_account(_w3: Web3, _account: str, _password: str) -> None:
    """
    Unlock account for transactions

    :param Web3 _w3: Web3 instance
    :param str _account: Account to unlock
    :param str _password: Password for the account
    :return: Nothing
    :rtype: None
    """
    _w3.geth.personal.unlockAccount(_account, _password, 300)


def create_new_account(_w3: Web3, _password: str, _file_name: str) -> str:
    """
    Create new account and write it to database

    :param Web3 _w3: Web3 instance
    :param str _password: Password for the new account
    :param str _file_name: Name of the database file for writing
    :return: Account address in blockchain
    :rtype: str 
    """

    if os.path.exists(_file_name):
        os.remove(_file_name)

    account = _w3.geth.personal.newAccount(_password)
    data = {"account": account, "password": _password}
    write_data_base(data, _file_name)

    return data['account']


def open_data_base(_file_name: str) -> Union[dict, None]:
    """
    Load data from the database

    :param str _file_name: Database file name
    :return: None if file does not exist or loaded from the file data
    :rtype: None/dict
    """

    if os.path.exists(_file_name):
        with open(_file_name) as file:
            return json.load(file)

    else:
        return None


def compile_contracts(_files: Union[str, list]):
    """
    Compile contract file/files

    :param str/list _files: Files to compile
    :return: Compiled files
    :rtype: dict
    """

    if isinstance(_files, str):
        contracts = compile_files([_files])

    if isinstance(_files, list):
        contracts = compile_files(_files)

    return contracts


def get_data_from_db(_file_name: str,_key: str) -> Union[str, None]:
    """
    Get data from database

    :params str _file_name: Name of the database file
    :params str _key: Key of dictionary
    :return: None if file does not exist or value of dictionary's key 
    :rtype: None/str
    """

    data = open_data_base(_file_name)
    
    if data is None:
        print("Cannot access account database")
        return None
    
    return data[_key]


def init_management_contract(_w3: Web3):
    """
    Creates management contract object

    :param Web3 _w3: Web3 instance
    :return: Management contract
    :rtype: Contract instance
    """

    compiled = compile_contracts(MGMT_CONTRACT_SRC_PATH)
    mgmt_contract = initialize_contract_factory(_w3, compiled, MGMT_CONTRACT_SRC_PATH + ":" + MGMT_CONTRACT_NAME,
                                                      open_data_base(MGMT_CONTRACT_DB_NAME)["mgmt_contract"])
    
    return mgmt_contract


def initialize_contract_factory(_w3: Web3, _compiled_contracts, _key: str, _address: str = None):
    """
    Initialize contract

    :params Web3 _w3: Web3 instance
    :params _compiled_contracts: Compiled contracts
    :params str _key: Contract path + name
    :params str _address: Target address
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


def get_battery_managment_contract_addr(_w3: Web3) -> str:
    """
    :params Web3 _w3: Web3 instance
    :return: Contract's address
    :rtype: str
    """

    try:
        mgmt_contract = init_management_contract(_w3)
        addr = mgmt_contract.functions.getBatteryManagmentAddr().call()
    except:
        sys.exit("Failed")

    return addr


def init_battery_management_contract(_w3: Web3, addr: str):
    """
    Creates battery management contract object

    :param Web3 _w3: Web3 instance
    :param str addr: Battery management contract's address
    :return: Battery management contract
    :rtype: Contract instance
    """

    compiled = compile_contracts(BATTERY_MGMT_CONTRACT_SRC_PATH)
    battery_mgmt_contract = initialize_contract_factory(_w3, compiled, BATTERY_MGMT_CONTRACT_SRC_PATH + ":" + BATTERY_MGMT_CONTRACT_NAME,
                                                        addr)
    
    return battery_mgmt_contract


def create_script_from_tmpl(private_key, address: str):
    with open("batteryTemplate.py", 'r') as tmpl:
        lines = tmpl.readlines()
    
    lines[11] = f"private_key = '{private_key}'\n"

    with open(f"firmware/{address[2:10]}.py", 'w') as fw:
        fw.writelines(lines)


def get_battery_info(_path: str) -> dict:
    """
    Get battery info(v, r, s, charges, time)

    :param str _path: Path to battery's firmware
    :return: Battery's info
    :rtype: dict
    """

    if os.path.exists(f"{_path}"):
        subprocess.run(["python", f"{_path}", "--get"])
    else:
        sys.exit("Battery does not exist")

    return open_data_base(f"{_path[:-3]}_data.json")


def verify_battery(_w3: Web3, _path: str):
    """
    Verify battery firmware

    :param Web3 _w3: Web3 instance
    :param str _path: Path to firmware
    :return:
    :rtype:
    """

    verified = False
    battery_info = get_battery_info(_path)

    if battery_info is None:
        sys.exit("The battery does not exist")

    battery_mgmt_addr = get_battery_managment_contract_addr(_w3)
    battery_mgmt_contract = init_battery_management_contract(_w3, battery_mgmt_addr)

    verified, vendor_address = battery_mgmt_contract.functions.verifyBattery(battery_info['v'], _w3.toBytes(hexstr=battery_info['r']),
                                                             _w3.toBytes(hexstr=battery_info['s']), battery_info['charges'],
                                                             battery_info['time']).call()

    mgmt_contract = init_management_contract(_w3)
    vendor_id = _w3.toHex(mgmt_contract.functions.vendorId(vendor_address).call())
    vendor_name = (mgmt_contract.functions.vendorNames(vendor_id).call()).decode()

    return verified, battery_info['charges'], vendor_id, vendor_name


def change_owner(_w3: Web3, _battery_id: str, _new_owner: str, account_db_name: str) -> str:
    """
    Change the owner of battery

    :param Web3 _w3: Web3 instance
    :param str _battery_id: battery ID
    :param str _new_owner: New owner address
    :return: Status message
    :rtype: str    

    """

    data = open_data_base(account_db_name)
    actor = data['account']

    tx = {'from': actor, 'gasPrice': get_actual_gas_price(_w3)}

    battery_mgmt_contract_addr = get_battery_managment_contract_addr(_w3)
    battery_mgmt_contract = init_battery_management_contract(_w3, battery_mgmt_contract_addr)

    unlock_account(_w3, actor, data['password'])

    
    tx_hash = battery_mgmt_contract.functions.transfer(_new_owner, decode_hex(_battery_id)).transact(tx)
    receipt = web3.eth.wait_for_transaction_receipt(_w3, tx_hash, 120, 0.1)
    result = receipt.status

    if result == 1:
        return "Ownership change was successfull"
    else:
        return "Ownership change failed"

