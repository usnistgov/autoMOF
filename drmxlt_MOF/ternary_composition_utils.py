import numpy as np

import mpltern
from mpltern.datasets import get_triangular_grid


def compositions_3d(compositions_2d):
    """Converting the compostions from the 2D triangle to a 3D simplex"""
    # In 3D space
    A_3d = np.array([1, 0, 0])
    B_3d = np.array([0, 1, 0])
    C_3d = np.array([0, 0, 1])

    # In 2D space
    A_2d = np.array([0, 0])  # A at the origin
    B_2d = np.array([1, 0])  # B at the x-axis = 1 point
    C_2d = np.array(
        [0.5, 0.5 * np.sqrt(3)]
    )  # C at the top of an equilateral triangle with the base along x of length 1.

    points = compositions_2d  # Read in the 2D compostions

    labmda_1 = ((B_2d[1] - C_2d[1])*(points[:,0] - C_2d[0]) + (C_2d[0] - B_2d[0])*(points[:,1] - C_2d[1]))/((B_2d[1] - C_2d[1])*(A_2d[0]-C_2d[0]) + (C_2d[0]-B_2d[0])*(A_2d[1]-C_2d[1]))

    labmda_2 = ((C_2d[1] - A_2d[1])*(points[:,0] - C_2d[0]) + (A_2d[0] - C_2d[0])*(points[:,1] - C_2d[1]))/((B_2d[1] - C_2d[1])*(A_2d[0]-C_2d[0]) + (C_2d[0]-B_2d[0])*(A_2d[1]-C_2d[1]))

    labmda_3 = 1 - labmda_1 - labmda_2

    points_3d = np.vstack([labmda_1, labmda_2, labmda_3]).T
    points_3d = points_3d.reshape(-1,3)
    return points_3d


def compositions_2d(compositions_3d):
      """Converting the compostions from the 3D simplex to a 2D triangle
      NOTE: the triangle is smaller than the simplex by a factor of sqrt(2)."""
      # In 3D space
      A_3d = np.array([1, 0, 0])
      B_3d = np.array([0, 1, 0])
      C_3d = np.array([0, 0, 1])

      # In 2D space
      A_2d = np.array([0, 0])  # A at the origin
      B_2d = np.array([1, 0])  # B at the x-axis = 1 point
      C_2d = np.array(
          [0.5, 0.5 * np.sqrt(3)]
      )  # C at the top of an equilateral triangle with the base along x of length 1.

      points = compositions_3d  # Read in the 3D compostions
      # Multiply 2D coordinates with the compositions for each component
      points_A = points[:, 0].reshape(-1, 1) * A_2d.reshape(1, -1)
      points_B = points[:, 1].reshape(-1, 1) * B_2d.reshape(1, -1)
      points_C = points[:, 2].reshape(-1, 1) * C_2d.reshape(1, -1)
      # Sum the coordinates for each component
      points_2d = points_A + points_B + points_C

      return points_2d

def generate_ternary_grid(points_per_side):
    #Set-up the domain of ternary components
    A_mesh, B_mesh, C_mesh = get_triangular_grid(points_per_side)

    #reshape to collumn vectors
    A_mesh = A_mesh.reshape(-1, 1)
    B_mesh = B_mesh.reshape(-1, 1)
    C_mesh = C_mesh.reshape(-1, 1)

    #concatenate into n x 3 matrix
    compositions = np.hstack([A_mesh, B_mesh, C_mesh])

    #vector of indexes
    domain_index = np.arange(compositions.shape[0])

    return compositions, domain_index


def random_ternary_composition(num, points_per_side = 101):
     
    compositions, domain_index = generate_ternary_grid(points_per_side)


    next_indexes = np.random.choice(domain_index, num).reshape(-1,1)

    next_compositions = compositions[next_indexes].reshape(-1,3)

    return next_compositions

