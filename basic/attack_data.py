import msgspec

from basic.http.request_sequence import RequestSequence
from basic.server_state import ServerState

class AttackData(msgspec.Struct, tag="attack_data", frozen=True):
    final_attack: RequestSequence

    # Server state after attack
    server_state: ServerState

    # Attack-depended States
    depended_state: ServerState