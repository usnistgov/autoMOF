centrifuge = {}

positions_in_centrifuge = 6

for i in range(positions_in_centrifuge):
    centrifuge[i] = {"Position" : i,
                     "Assignment" : "Empty"}

half_turn = positions_in_centrifuge // 2

loading_order = []
for i in range(half_turn):
    loading_order.append(i)
    loading_order.append(i + half_turn)

centrifuge["Loading Order"] = loading_order