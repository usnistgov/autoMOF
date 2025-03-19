class dummy_c9():
  def __init__(self):
    self.sonicator = True
    self.centrifuge = False
    self.PUMP_VALVE_RIGHT = True
    self.PUMP_VALVE_LEFT = False

    self.pumps = {0 : {"volume" : 10},
                  1 : {"volume" : 10},
                  2 : {"volume" : 10},
                  3 : {"volume" : 10},
                  4 : {"volume" : 10},
                  5 : {"volume" : 10},
                  6 : {"volume" : 10},
                  7 : {"volume" : 10}}

  def zero_scale(self):
    pass

  def read_steady_scale(self):
    return 0.0

  def open_clamp(self):
    pass

  def close_clamp(self):
    pass

  def read_heater_block(self, heater_block_id):
    return 23.0

  def goto_safe(self, position):
    pass

  def goto_xy_safe(self, position):
    pass

  def open_gripper(self):
    pass

  def close_gripper(self):
    pass

  def uncap(self):
    pass

  def move_z(self, height):
    pass
  
  def move_pump(self, rot, z):
    pass

  def set_pump_valve(self, z, rot):
    pass

  def move_carousel(self, angle, z):
    pass

  def aspirate_ml(self, pump, vol):
    pass

  def dispense_ml(self, pump, vol):
    pass

  def delay(self, time):
    pass

def tare_balance(c):
    c.zero_scale()
    while c.read_steady_scale() != 0:
        c.delay(.2)
        c.zero_scale()




