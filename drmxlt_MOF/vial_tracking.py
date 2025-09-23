import numpy as np


# Vials

vial_rack_left_array = np.arange(0,48).reshape(-1,6) #Array 0-48, 6x7
vial_rack_right_array = np.arange(0,48).reshape(-1,6) #Array 0-48, 6x7


def loaded_vial_racks(vial_racks = "left", empty_rack_left_indexes = [], empty_rack_right_indexes = []):
    """Create arrays that show where the vials are loaded.
    If any indexes are empty, enter those as a list,
    e.g. empty_rack_left_indexes = [0, 10, 43]"""

    if vial_racks == "left":
      loaded_rack_left = np.ones_like(vial_rack_left_array)
      loaded_rack_right = np.zeros_like(vial_rack_right_array)

      for i in empty_rack_left_indexes:
          position = np.where(vial_rack_left_array == i)
          loaded_rack_left[position] = 0

      return loaded_rack_left, loaded_rack_right

    if vial_racks == "right":
      loaded_rack_left = np.zeros_like(vial_rack_left_array)
      loaded_rack_right = np.ones_like(vial_rack_right_array)

      for i in empty_rack_right_indexes:
          position = np.where(vial_rack_right_array == i)
          loaded_rack_right[position] = 0
      return loaded_rack_left, loaded_rack_right

    if vial_racks == "both":
      loaded_rack_left, _ = loaded_vial_racks("left", empty_rack_left_indexes)
      _, loaded_rack_right = loaded_vial_racks("right", empty_rack_right_indexes)
      return loaded_rack_left, loaded_rack_right
    

## Create the initial loadings of the vial racks
loaded_rack_left, loaded_rack_right = loaded_vial_racks("left")

# loaded_rack_left = loaded_vial_racks('left')
# loaded_rack_right = loaded_vial_racks('right')

## Create the initial assignments of the vial racks
left_rack_assignments = np.ones_like(vial_rack_left_array) * loaded_rack_left
left_rack_assignments = np.where(left_rack_assignments == 1, "Unassigned", "Empty")

right_rack_assignments = np.ones_like(vial_rack_right_array) * loaded_rack_right
right_rack_assignments = np.where(right_rack_assignments == 1, "Unassigned", "Empty")
