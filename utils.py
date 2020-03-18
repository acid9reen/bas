import json
import os


def write_data_base(_data, _file):
    with open(_file, 'w') as out:
        json.dump(_data, out)


def create_new_account(_w3, _password, _file):
    if os.path.exists(_file):
        os.remove(_file)

    account = _w3.geth.personal.newAccount(_password)
    data = {"account": account, "password": _password}
    write_data_base(data, _file)

    return data['account']

