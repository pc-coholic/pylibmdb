from pylibftdi import Device
import time
import os

class MDB(object):
  def __init__(self, device):
    self.__device = device

  def _ftdisend(self, data, mode, chk = 0):
    data_parity = sum([int(c) for c in bin(data)[2:]]) % 2

    if data_parity:
      if mode:
        #parity = serial.PARITY_EVEN
        parity = 2
      else:
        #parity = serial.PARITY_ODD
        parity = 1
    else:
      if mode:
        #parity = serial.PARITY_ODD
        parity = 1
      else:
        #parity = serial.PARITY_EVEN
        parity = 2

    with Device(self.__device) as dev:
      dev.ftdi_fn.ftdi_set_line_property(8, 1, parity)
      dev.baudrate = 9600
      dev.write(chr(data))
      if chk == 1:
        time.sleep(0.1)
        #FIXME chk-check
        return dev.read(100)

  def send(self, data):
    mode = 1

    for element in data:
      self._ftdisend(element, mode)
      mode = 0

    return self._ftdisend(self._calcchk(data), 0, 1)

  def _calcchk(self, data):
    chk = sum(data)
    chk = bin(chk)[-8:]
    return int(chk, 2)


