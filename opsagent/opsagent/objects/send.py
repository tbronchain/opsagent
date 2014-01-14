'''
Madeira OpsAgent requests objects

@author: Thibault BRONCHAIN
'''


# Protocol defines import
import codes


# Handshake request
def handshake(init, errors):
    if type(init) is not dict: init={}
    return ({
            "code"             :   codes.HANDSHAKE,
            "instance_id"      :   init.get('instance_id'),
            "app_id"           :   init.get('app_id'),
            "protocol_version" :   codes.PROTOCOL_VERSION,
            "instance_token"   :   init.get('instance_token'),
            "init_errors"      :   None#(" ".join(errors) if errors else None),
            })


# Statelog request
def statelog(init, version, id, result, err_log, out_log):
    return ({
            "code"           :   codes.STATELOG,
            "instance_id"    :   init.get('instance_id'),
            "app_id"         :   init.get('app_id'),
            "recipe_version" :   version,
            "stateid"        :   id,
            "state_result"   :   result,
            "state_stderr"   :   err_log,
            "state_stdout"   :   out_log
            })
