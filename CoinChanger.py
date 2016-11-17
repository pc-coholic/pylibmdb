class CoinChanger(object):
  def __init__(self):
    pass

  def reset(self):
    print "OUT: Reset"
    answer = self._send(data = [0x08])
    if (len(answer) == 1) and (hex(ord(answer)) == '0x0'):
      print "IN : OK"
      self.ack()
    else:
      print "IN: Fail - " + hex(ord(answer))

  def poll(self):
    print "OUT: Poll"
    answer = self._send(data = [0x0B])
    #FIXME
    for i in answer:
      print hex(ord(i))
    self.ack()

  def setup(self):
    print "OUT: Setup"
    answer = self._send(data = [0x09])
    if len(answer) == 24:
      print "IN: Changer Feature Level: " + str(ord(answer[0])) + " (" + hex(ord(answer[0])) + ")"
      print "IN: Country/Currency-Code: " + hex(ord(answer[1])) + " " + hex(ord(answer[2]))
      print "IN: Coin Scaling Factor: " + str(ord(answer[3])) + " (" + hex(ord(answer[3])) + ")"
      print "IN: Decimal Places: " + str(ord(answer[4])) + " (" + hex(ord(answer[4])) + ")"
      print "IN: Coin Type Routing: " + hex(ord(answer[5])) + " " + hex(ord(answer[6])) #FIXME
      for i in range(7, 23):
        print "IN: Coin Type Credit: " + str(i-7) + " --> " + str(ord(answer[i])) + " (" + hex(ord(answer[i])) + ")"
      self.ack()
    else:
      print "IN: Fail - " + hex(ord(answer))

  def expansionidentification(self):
    print "OUT: Expansion Identification"
    answer = self._send(data = [0x0F, 0x00])
    if len(answer) == 34:
      print "IN: Manufacturer Code: " + str(answer[0]) + str(answer[1]) + str(answer[2]) + " (" + hex(ord(answer[0])) + " " + hex(ord(answer[1])) + " " + hex(ord(answer[2])) + ")"
      print "IN: Serial Number: " + ''.join(answer[i] for i in range(3, 15)) + " (" + " ".join(hex(ord(answer[i])) for i in range(3, 15)) + ")"
      print "IN: Model #/Tuning Revision: " + ''.join(answer[i] for i in range(15, 27)) + " (" + " ".join(hex(ord(answer[i])) for i in range(15, 27)) + ")"
      print "IN: Software Version: " + hex(ord(answer[27])) + " " + hex(ord(answer[28]))
      print "IN: Optional Features: " + hex(ord(answer[29])) + " " + hex(ord(answer[30])) + " " + hex(ord(answer[31])) + " " + hex(ord(answer[32])) #FIXME
      self.ack()
      features = []
      for i in range (29, 33):
        features.append(ord(answer[i]))
      return features
    else:
      print "IN: Fail - " + hex(ord(answer))

  def expansionfeatureenable(self, features):
    print "OUT: Expansion Feature Enable"
    answer = self._send(data = [0x0F, 0x01] + features)
    if (len(answer) == 1) and (hex(ord(answer)) == '0x0'):
      print "IN : OK"
      self.ack()
    else:
     print "IN: Fail - " + hex(ord(answer))

  def expansiondiagnosticstatus(self):
    print "OUT: Expansion Diagnostic Status"
    answer = self._send(data = [0x0F, 0x05])
    if len(answer) == 3:
      print "IN: Main-Code: " + hex(ord(answer[0]))
      print "IN: Sub-Code: " + hex(ord(answer[1]))
      message = {
        '0x1': 'Powering up',
        '0x2': 'Powering down',
        '0x3': 'OK',
        '0x4': 'Keypad shifted',
        '0x5': '',
        '0x6': 'Inhibited by VMC',
        '0x10': '',
        '0x11': '',
        '0x12': '',
        '0x13': '',
        '0x14': '',
        '0x15': '',
        'unknown': 'Unknown Main-Code',
      }.get(hex(ord(answer[0])), 'unknown')

      if ( (hex(ord(answer[0])) == '0x5') and (hex(ord(answer[1])) == '0x10') ):
        message = "Manual Fill / Payout active"

      if ( (hex(ord(answer[0])) == '0x5') and (hex(ord(answer[1])) == '0x20') ):
        message = "New Inventory Information Available"

      if hex(ord(answer[0])) == '0x10':
        message = "General changer error: " + {
          '0x0': 'Non specific error',
          '0x1': 'Check sum error #1. A check sum error over a particular data range of configuration field detected.',
          '0x2': 'Check sum error #2. A check sum error over a secondary data range or configuration field detected.',
          '0x3': 'Low line voltage detected. The changer has disabled acceptance or payout due to a low voltage condition',
          'unknown': 'Unknown Sub-Code',
        }.get(hex(ord(answer[1])), 'unknown')

      if hex(ord(answer[0])) == '0x11':
        message = "Discriminator module error: " + {
          '0x0': 'Non specific discriminator error.',
          '0x10': 'Flight deck open.',
          '0x11': 'Escrow Return stuck open.',
          '0x30': 'Coin jam in sensor.',
          '0x41': 'Discrimination below specified standard.',
          '0x50': 'Validation sensor A out of range. The acceptor detects a problem with sensor A.',
          '0x51': 'Validation sensor B out of range. The acceptor detects a problem with sensor B.',
          '0x52': 'Validation sensor C out of range. The acceptor detects a problem with sensor C.',
          '0x53': 'Operating temperature exceeded. The acceptor detects the ambient temperature has exceeded the changer\'s operating range, thus possibly affecting the acceptance rate.',
          '0x54': 'Sizing optics failure. The acceptor detects an error in the sizing optics.',
          'unknown': 'Unknown Sub-Code',
      }.get(hex(ord(answer[1])), 'unknown')

      if hex(ord(answer[0])) == '0x12':
        message = "Accept gate module error: " + {
          '0x0': 'Non specific accept gate error',
          '0x30': 'Coins entered gate, but did not exit.',
          '0x31': 'Accept gate alarm active.',
          '0x40': 'Accept gate open, but no coin detected.',
          '0x50': 'Post gate sensor covered before gate opened.',
          'unknown': 'Unknown Sub-Code',
      }.get(hex(ord(answer[1])), 'unknown')

      if hex(ord(answer[0])) == '0x13':
        message = "Separator module error: " + {
          '0x0': 'Non specific separator error',
          '0x10': 'Sort sensor error. The acceptor detects an error in the sorting sensor',
          'unknown': 'Unknown Sub-Code',
      }.get(hex(ord(answer[1])), 'unknown')

      if hex(ord(answer[0])) == '0x14':
        message = "Dispenser module error: " + {
          '0x0': 'Non specific dispenser error.',
          'unknown': 'Unknown Sub-Code',
      }.get(hex(ord(answer[1])), 'unknown')

      if hex(ord(answer[0])) == '0x15':
        message = "Coin Cassette / tube module error: " + {
          '0x0': 'Non specific cassette error.',
          '0x2': 'Cassette removed.',
          '0x3': 'Cash box sensor error. The changer detects an error in a cash box sensor.',
          '0x4': 'Sunlight on tube sensors. The changer detects too much ambient light on one or more of the tube sensors.',
          'unknown': 'Unknown Sub-Code',
      }.get(hex(ord(answer[1])), 'unknown')

      print "IN: Message: " + message
      self.ack()
    else:
      print "IN: Fail - " + hex(ord(answer))

  def tubestatus(self):
    print "OUT: Tube Status"
    answer = self._send(data = [0x0A])
    if len(answer) == 19:
      print "IN: Tube Full Status: " + hex(ord(answer[0])) + " " + hex(ord(answer[1]))
      for i in range(2, 18):
        print "IN: Tube Status: " + str(i-2) + " --> " + str(ord(answer[i])) + " (" + hex(ord(answer[i])) + ")"
      self.ack()
    else:
      print "IN: Fail - " + hex(ord(answer))

  def cointype(self):
    print "OUT: Coin type"
    answer = self._send(data = [0x0C, 0xFF, 0xFF, 0x00, 0x00])
    if (len(answer) == 1) and (hex(ord(answer)) == '0x0'):
      print "IN : OK"
      self.ack()
    else:
      print "IN: Fail - " + hex(ord(answer))

  def ack(self):
    print "OUT: ACK"
    self._ftdisend(0x00, 1)

  def payout(self, value):
    print "OUT: Payout"
    self._send(data = [0x0F, 0x02, int(value)])

  def payoutpoll(self):
    print "OUT: Payout Poll"
    self._send(data = [0x0F, 0x04])

  def payoutstatus(self):
    print "OUT: Payout Status"
    self._send(data = [0x0F, 0x03])
