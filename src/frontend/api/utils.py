import json


def validate_body(data, validation_dic):
    validation = (True, "")
    for key in validation_dic:
        if key in data.keys():
            continue
        else:
            validation = (False, {'success': False, 'msg': "No fuzzer %s parameter specified" % key})
            break
    return validation


def fix_json(data):
    data = json.loads(data)
    for key, value in data.items():
        if not isinstance(value, dict):
            continue
        subkey = next(iter(value))
        subvalue = value[subkey]
        if not subkey.startswith('$'):
            continue
        data[key] = subvalue
    return data
