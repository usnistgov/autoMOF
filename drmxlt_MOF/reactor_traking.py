
#Setting up a dictionary to keep track of reactor status
reactor = {}

for i in range(8):
  reactor[i] = {"Block ID": i,
                     "Temperature": None,
                     "Hat Status": "Off"}

  for j in range(4):
    reactor[i][j] = {"Position": j,
                          "Assignment": "Empty"}

reactor

#Function to read reactor temperature
def measure_reactor_temp(c, system_db, reactor_id):
  #TODO change reactor to t9 controler
  temp = c.read_reactor(reactor_id)
  system_db["reactor"][reactor_id]["Temperature"] = temp
  return temp