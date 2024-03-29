import time

import smbus2
from enum import Enum
from typing import Tuple, List, Iterator


def set_bit_value(origin, bit, value) -> int:
    """改变 origin 中 bit 位置的值为 value，其他位保持不变
    Args:
        origin: 8 bit value
        bit: origin 中的位置
        value: 0, 1
    """
    if value == 0:
        origin &= ~(0b00000001 << bit)
    elif value == 1:
        origin |= 0b00000001 << bit
    return origin


class PinRowType(object):
    A = 0
    B = 1


def register_mode_const(obj):
    modes = (
        "IODIR",
        "IPOL",
        "GPINTEN",
        "DEFVAL",
        "INTCON",
        "IOCON",
        "GPPU",
        "INTF",
        "INTCAP",
        "GPIO",
        "OLAT")
    value = 0x00
    # 生成 PinRowType.A mod
    for mod in modes:
        setattr(obj, mod, value)
        value += 2
    return obj


@register_mode_const
class MCP23017Mode(object):
    """MCP23017Mode type const
    """


class AgentBus(object):
    def __init__(self, addr: int, bus=1):
        self.addr = addr
        self.__bus = smbus2.SMBus(bus)

    def write_byte_data(self, register, value):
        self.__bus.write_byte_data(self.addr, register, value)

    def read_byte_data(self, register):
        value = self.__bus.read_byte_data(self.addr, register)
        if value is None:
            raise ValueError("")
        return value

    def close(self):
        self.__bus.close()


class Pin(object):
    def __init__(self, pin: int, row: PinRowType, bus: AgentBus):
        """
        Args:
            pin: I/O 口索引 0-7
            row: 引脚所在的线排
            bus: I2C 代理总线
        """
        self.pin = pin
        self.row = row
        self.__bus = bus

    @property
    def value(self):
        return self.readValue()

    @value.setter
    def value(self, value: int):
        self.setValue(value)

    def on(self):
        self.value = 1

    def off(self):
        self.value = 0

    def setValue(self, value: int):
        _value = set_bit_value(self.allGPIOValues(), self.pin, value)
        self.__bus.write_byte_data(
            self.genMode(MCP23017Mode.GPIO),
            _value)

    def readValue(self) -> int:
        """
        Return: 0,1
        """
        allval = self.allGPIOValues()
        if (allval & 0b00000001 << self.pin) > 0:
            return 1
        else:
            return 0

    def setInOutPut(self, out: bool):
        mode = self.genMode(MCP23017Mode.IODIR)
        origin_value = self.__bus.read_byte_data(mode)
        if out:
            origin_value = set_bit_value(origin_value, self.pin, value=0)
        else:
            origin_value = set_bit_value(origin_value, self.pin, value=1)
        self.__bus.write_byte_data(mode, origin_value)

    def setOutput(self):
        self.setInOutPut(out=True)

    def setInput(self, pull=False):
        self.setInOutPut(out=False)
        if pull:
            mode = self.genMode(MCP23017Mode.GPPU)
            self.__bus.write_byte_data(
                mode,
                set_bit_value(
                    self.__bus.read_byte_data(mode),
                    self.pin,
                    value=1))

    def genMode(self, mode: MCP23017Mode) -> int:
        if self.row == PinRowType.B:
            mode += 1
        return mode

    def allGPIOValues(self):
        mode = self.genMode(MCP23017Mode.GPIO)
        return self.__bus.read_byte_data(mode)


class Pins(object):
    def __init__(self, row: PinRowType, bus: AgentBus):
        self.row = row
        self._bus = bus
        self.__values: List[Pin] = []

    def append(self, pin: int):
        if len(self.__values) < 8:
            self.__values.append(Pin(pin, self.row, self._bus))

    def __len__(self) -> int:
        return len(self.__values)

    def __getitem__(self, key: int) -> Pin:
        return self.__values[key]

    def __iter__(self) -> Iterator:
        return iter(self.__values)


class MCP23017(object):
    def __init__(self, addr: int):
        #   Addr(BIN)      Addr(hex)
        # XXX X  A2 A1 A0
        # 010 0  1  1  1      0x27
        # 010 0  1  1  0      0x26
        # 010 0  1  0  1      0x25
        # 010 0  1  0  0      0x24
        # 010 0  0  1  1      0x23
        # 010 0  0  1  0      0x22
        # 010 0  0  0  1      0x21
        # 010 0  0  0  0      0x20
        self.bus = AgentBus(addr)
        # A0-A7 ==> 0-7
        self.A = Pins(PinRowType.A, self.bus)
        # B0-B7 ==> 0-7
        self.B = Pins(PinRowType.B, self.bus)
        self.reset()
        self.registerPins()

    def reset(self):
        for addr in range(22):
            if addr in (0, 1):
                self.bus.write_byte_data(addr, 0xFF)
            else:
                self.bus.write_byte_data(addr, 0x00)

    def registerPins(self):
        for j in range(2):
            for i in range(8):
                if j == 0:
                    self.A.append(i)
                else:
                    self.B.append(i)

    def close(self):
        self.reset()
        self.bus.close()
        self.bus = None

    def __del__(self):
        if self.bus:
            self.close()
