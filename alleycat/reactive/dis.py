import dis

from types import FrameType
from typing import Optional


def get_assigned_name(frame: FrameType) -> Optional[str]:
    inst = get_instruction(frame)

    if inst is not None and inst.opname == "STORE_NAME":
        return inst.argval

    return None


def get_instruction(frame: FrameType) -> Optional[dis.Instruction]:
    it = iter(dis.get_instructions(frame.f_code))

    for ins in it:
        if ins.offset == frame.f_lasti:
            break
    else:
        return None

    if ins.opname.startswith("CALL_"):
        try:
            return next(it)
        except StopIteration:
            pass

    return None
