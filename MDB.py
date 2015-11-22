from pylibftdi import Device
import time
import os
from binascii import hexlify, unhexlify

class MDB(object):
  def __init__(self, deviceid):
    self.__deviceid = deviceid
    self.__scaling = 0
    self.__coins = {}
    self.__deposited = 0

  def _ftdisend(self, data, mode):
    data_parity = self._parityOf(int(hexlify(data), 16))

    if data_parity == -1:
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
    try:
        self.__device = Device(self.__deviceid)
        self.__device.ftdi_fn.ftdi_set_line_property(8, 1, parity)
        self.__device.baudrate = 9600
        self.__device.write(data)
        self.__device.flush()
    except pylibftdi.FtdiError:
        print "FtdiError"
        self._ftdisend(data, mode)

  def _parityOf(self, int_type):
      parity = 0
      while (int_type):
          parity = ~parity
          int_type = int_type & (int_type - 1)
      return(parity)

  def _read(self):
    returndata = []
    for i in self.__device.read(100):
      returndata.append(i)

    return returndata

  def _send(self, data):
    mode = 1

    for element in data:
      self._ftdisend(element, mode)
      mode = 0

    self._ftdisend(self._calcchk(data), 0)

    time.sleep(0.1)
    return self._read()

  def _calcchk(self, data):
    sum = 0
    for byte in data:
        sum += int(hexlify(byte), 16)
    return unhexlify('{:02x}'.format(sum % 256))

  def _getbits(self, byte):
    return bin(int(hexlify(byte), 16))[2:].zfill(8)

# CoinChanger
  def reset(self):
    print "OUT: Reset"
    answer = self._send(data = ['\x08'])
    if (len(answer) == 1) and (answer[0] == '\x00'):
      print "IN : OK"
      #self.ack()
    else:
      print "IN: Fail"
      print answer

  def poll(self):
    print "OUT: Poll"
    answer = self._send(data = ['\x0B'])

    i = 0
    while i < len(answer):
      if answer[i] == '\x00':
        message = "ACK"
      elif answer[i] == '\xFF':
        message = "NACK"
      elif '\x01' <= answer[i] <= '\x0D':
        message = {
          '\x01': 'Escrow request - An escrow lever activation has been detected.',
          '\x02': 'Changer Payout Busy - The changer is busy activating payout devices',
          '\x03': 'No Credit - A coin was validated but did not get to the place in the system when credit is given',
          '\x04': 'Defective Tube Sensor - The changer hasdetected one of the tube sensors behaving abnormally',
          '\x05': 'Double Arrival - Two coins were detected too close together to validate either one',
          '\x06': 'Acceptor Unplugged - The changer has detected that the acceptor has been removed',
          '\x07': 'Tube Jam - A tube payout attempt has resulted in jammed condition',
          '\x08': 'ROM checksum error - The changers internal checksum does not match the calculated checksum',
          '\x09': 'Coin Routing Error - A coin has been validated, but did not follow the intended routing',
          '\x0A': 'Changer Busy - The changer is busy and can not answer a detailed command right now',
          '\x0B': 'Changer was Reset - The changer has detected an Reset condition and has returned to its power-on idle condition',
          '\x0C': 'Coin Jam - A coin(s) has jammed in the acceptance path',
          '\x0D': 'Possible Credited Coin Removal - There has been an attempt to remove a credited coin',
        }.get(answer[i])
        print "IN: " + message
      elif '\x20' <= answer[i] <= '\x3F':
        print "IN: Slugs deposited: " + str(int(self._getbits(answer[i])[3:], 2))
      elif '\x40' <= answer[i] <= '\x7F':
        bits = self._getbits(answer[i])

        if bits[2:4] == '00':
          routing = "Cash Box"
        elif bits[2:4] == '01':
          routing = "Tubes"
        elif bits[2:4] == '10':
          routing = "Not used"
        elif bits[2:4] == '11':
          routing = "Rejected"
        else:
          routing = "Unknown"

        cointype = int(bits[4:8], 2)
        coinsinroutingpath = str(int(self._getbits(answer[i+1]), 2))

        print "IN: Coin deposited: Type " + str(cointype) + ", sent to " + routing  + ". Now " + coinsinroutingpath + " coins there"
        self.__deposited += self.__coins[cointype] * self.__scaling
        i += 1
        break;
      elif '\x80' <= answer[i] <= '\xFE':
        bits = self._getbits(answer[i])
        
        number = str(int(bits[1:4], 2))
        cointype = str(int(bits[4:8], 2))
        coinsintube = str(int(self._getbits(answer[i+1]), 2))
        print "IN: Coins dispensed manually: " + number + " coins of type " + cointype  + ". Now " + coinsintube + " coins there"
        i += 1
        break;
      else: #\x0E -> \x1F
        print "IN: Unknown Poll Status reply" + hexlify(answer[i])
      i += 1
    self.ack()

  def setup(self):
    print "OUT: Setup"
    answer = self._send(data = ['\x09'])
    if len(answer) == 24:
      print "IN: Changer Feature Level: " + str(ord(answer[0])) + " (" + hex(ord(answer[0])) + ")"
      print "IN: Country/Currency-Code: " + hex(ord(answer[1])) + " " + hex(ord(answer[2]))
      print "IN: Coin Scaling Factor: " + str(ord(answer[3])) + " (" + hex(ord(answer[3])) + ")"
      self.__scaling = int(ord(answer[3]))
      print "IN: Decimal Places: " + str(ord(answer[4])) + " (" + hex(ord(answer[4])) + ")"
      canberoutedtotube = (self._getbits(answer[5]) + self._getbits(answer[6]))[::-1]
      for i in range(7, 23):
        print "IN: Coin Type: " + str(i-7) + ", Value: " + str(ord(answer[i])) + ", Can be routed to tube: " + canberoutedtotube[i-7]
        self.__coins[(i-7)] = int(ord(answer[i]))
      self.ack()
    else:
      print "IN: Fail - " + answer

  def expansionidentification(self):
    print "OUT: Expansion Identification"
    answer = self._send(data = ['\x0F', '\x00'])
    if len(answer) == 34:
      print "IN: Manufacturer Code: " + str(answer[0]) + str(answer[1]) + str(answer[2]) + " (" + hex(ord(answer[0])) + " " + hex(ord(answer[1])) + " " + hex(ord(answer[2])) + ")"
      print "IN: Serial Number: " + ''.join(answer[i] for i in range(3, 15)) + " (" + " ".join(hex(ord(answer[i])) for i in range(3, 15)) + ")"
      print "IN: Model #/Tuning Revision: " + ''.join(answer[i] for i in range(15, 27)) + " (" + " ".join(hex(ord(answer[i])) for i in range(15, 27)) + ")"
      print "IN: Software Version: " + hex(ord(answer[27])) + " " + hex(ord(answer[28]))
      optionalfeatures = (self._getbits(answer[29]) + self._getbits(answer[30]) + self._getbits(answer[31]) + self._getbits(answer[32]))[::-1]
      print "IN: Optional Feature: Alternative Payout method: " + optionalfeatures[0]
      print "IN: Optional Feature: Extended Diagnostic command supported: " + optionalfeatures[1]
      print "IN: Optional Feature: Controlled Manual Fill and Payout commands supported: " + optionalfeatures[2]
      print "IN: Optional Feature: File Transport Layer (FTL) supported: " + optionalfeatures[3]
      print "IN: Optional Features: Future extensions: " + optionalfeatures[4:]
      self.ack()
      features = []
      for i in range (29, 33):
        features.append(ord(answer[i]))
      return features
    else:
      print "IN: Fail - " + answer

  def expansionfeatureenable(self, features):
    print "OUT: Expansion Feature Enable"
    answer = self._send(data = ['\x0F', '\x01'] + features)
    if (len(answer) == 1) and (answer[0] == '\x00'):
      print "IN : OK"
      self.ack()
    else:
     print "IN: Fail - " + answer

  def expansiondiagnosticstatus(self):
    print "OUT: Expansion Diagnostic Status"
    answer = self._send(data = ['\x0F', '\x05'])
    if len(answer) == 3:
      print "IN: Main-Code: " + hex(ord(answer[0]))
      print "IN: Sub-Code: " + hex(ord(answer[1]))
      message = {
        '\x01': 'Powering up',
        '\x02': 'Powering down',
        '\x03': 'OK',
        '\x04': 'Keypad shifted',
        '\x05': '',
        '\x06': 'Inhibited by VMC',
        '\x10': '',
        '\x11': '',
        '\x12': '',
        '\x13': '',
        '\x14': '',
        '\x15': '',
        'unknown': 'Unknown Main-Code',
      }.get(answer[0], 'unknown')

      if ( (answer[0] == '\x05') and (answer[1] == '\x10') ):
        message = "Manual Fill / Payout active"

      if ( (answer[0] == '\x05') and (answer[1] == '\x20') ):
        message = "New Inventory Information Available"

      if answer[0] == '\x10':
        message = "General changer error: " + {
          '\x00': 'Non specific error',
          '\x01': 'Check sum error #1. A check sum error over a particular data range of configuration field detected.',
          '\x02': 'Check sum error #2. A check sum error over a secondary data range or configuration field detected.',
          '\x03': 'Low line voltage detected. The changer has disabled acceptance or payout due to a low voltage condition',
          'unknown': 'Unknown Sub-Code',
        }.get(answer[1], 'unknown')

      if answer[0] == '\x11':
        message = "Discriminator module error: " + {
          '\x00': 'Non specific discriminator error.',
          '\x10': 'Flight deck open.',
          '\x11': 'Escrow Return stuck open.',
          '\x30': 'Coin jam in sensor.',
          '\x41': 'Discrimination below specified standard.',
          '\x50': 'Validation sensor A out of range. The acceptor detects a problem with sensor A.',
          '\x51': 'Validation sensor B out of range. The acceptor detects a problem with sensor B.',
          '\x52': 'Validation sensor C out of range. The acceptor detects a problem with sensor C.',
          '\x53': 'Operating temperature exceeded. The acceptor detects the ambient temperature has exceeded the changer\'s operating range, thus possibly affecting the acceptance rate.',
          '\x54': 'Sizing optics failure. The acceptor detects an error in the sizing optics.',
          'unknown': 'Unknown Sub-Code',
      }.get(answer[1], 'unknown')

      if answer[0] == '\x12':
        message = "Accept gate module error: " + {
          '\x00': 'Non specific accept gate error',
          '\x30': 'Coins entered gate, but did not exit.',
          '\x31': 'Accept gate alarm active.',
          '\x40': 'Accept gate open, but no coin detected.',
          '\x50': 'Post gate sensor covered before gate opened.',
          'unknown': 'Unknown Sub-Code',
      }.get(answer[1], 'unknown')

      if answer[0] == '\x13':
        message = "Separator module error: " + {
          '\x00': 'Non specific separator error',
          '\x10': 'Sort sensor error. The acceptor detects an error in the sorting sensor',
          'unknown': 'Unknown Sub-Code',
      }.get(answer[1], 'unknown')

      if answer[0] == '\x14':
        message = "Dispenser module error: " + {
          '\x00': 'Non specific dispenser error.',
          'unknown': 'Unknown Sub-Code',
      }.get(answer[1], 'unknown')

      if answer[0] == '\x15':
        message = "Coin Cassette / tube module error: " + {
          '\x00': 'Non specific cassette error.',
          '\x02': 'Cassette removed.',
          '\x03': 'Cash box sensor error. The changer detects an error in a cash box sensor.',
          '\x04': 'Sunlight on tube sensors. The changer detects too much ambient light on one or more of the tube sensors.',
          'unknown': 'Unknown Sub-Code',
      }.get(answer[1], 'unknown')

      print "IN: Message: " + message
      self.ack()
    else:
      print "IN: Fail - " + answer

  def tubestatus(self):
    print "OUT: Tube Status"
    answer = self._send(data = ['\x0A'])
    if len(answer) == 19:
      print "IN: Tube Full Status: " + hex(ord(answer[0])) + " " + hex(ord(answer[1]))
      for i in range(2, 18):
        print "IN: Tube Status: " + str(i-2) + " --> " + str(ord(answer[i])) + " (" + hex(ord(answer[i])) + ")"
      self.ack()
    else:
      print "IN: Fail - " + answer

  def enableall(self, manual = False):
    if manual == True:
      self.cointype('\xFF', '\xFF', '\xFF', '\xFF')
    else:
      self.cointype('\xFF', '\xFF', '\x00', '\x00')

  def disableall(self, manual = False):
    if manual == True:
      self.cointype('\x00', '\x00', '\xFF', '\xFF')
    else:
      self.cointype('\x00', '\x00', '\x00', '\x00')

  def cointype(self, enable1, enable2, manual1, manual2):
    print "OUT: Coin type"
    answer = self._send(data = ['\x0C', enable1, enable2, manual1, manual2])
    if (len(answer) == 1) and (answer[0] == '\x00'):
      print "IN : OK"
      self.ack()
    else:
      print "IN: Fail - " + answer

  def ack(self):
    print "OUT: ACK"
    # ACK, NACK and RET don't take the mode-Bit
    self._ftdisend('\x00', 0)

  def payout(self, value):
    print "OUT: Payout"
    self._send(data = ['\x0F', '\x02', unhexlify('{:02x}'.format(int(value) / self.__scaling)) ])

  def payoutpoll(self):
    print "OUT: Payout Poll"
    self._send(data = ['\x0F', '\x04'])

  def payoutstatus(self):
    print "OUT: Payout Status"
    self._send(data = ['\x0F', '\x03'])

  def getdeposited(self):
    return self.__deposited

  def cleardeposited(self):
    self.__deposited = 0
