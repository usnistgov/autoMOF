
#Setting up a dictionary to keep track of heater block status
heater_block = {}

for i in range(8):
  heater_block[i] = {"Block ID": i,
                     "Temperature": None,
                     "Hat Status": "Off"}

  for j in range(4):
    heater_block[i][j] = {"Position": j,
                          "Assignment": "Empty"}

heater_block

#Function to read heater block temperature
def measure_heater_block_temp(c, system_db, heater_block_id):
  #TODO change heater block to t9 controler
  temp = c.read_heater_block(heater_block_id)
  system_db["heater_block"][heater_block_id]["Temperature"] = temp
  return temp