"""Functions for autonomously discovering color."""

import numpy as np
import GPy

from matplotlib import pyplot as plt
import mpltern
from mpltern.datasets import get_triangular_grid
from colorfunc import colormix


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


def mix_and_measure(compositions_array, vial_index_array, total_volume = 5, simulate=False):
  """Function that mixes a ternary mixture and measures the color"""
  measured_RGB_array = np.empty((0, 3))

  for vial_index, compositions in zip(vial_index_array, compositions_array):

    component_mL = compositions * total_volume

    if simulate == False:

      measured_RGB,_,_ =colormix(vial_index, component_mL)

      measured_RGB_array = np.concatenate((measured_RGB_array, measured_RGB.reshape(-1,3)), axis = 0)


    if simulate == True:

      A_dye = np.array([243.0, 12.0, 50.0])
      B_dye = np.array([100.0, 240.0, 0.0])
      C_dye = np.array([50.0, 2.0, 250.0])

      a_RGB = A_dye * compositions[0]
      b_RGB = B_dye * compositions[1]
      c_RGB = C_dye * compositions[2]

      measured_RGB = a_RGB + b_RGB + c_RGB
      measured_RGB_array = np.concatenate((measured_RGB_array, measured_RGB.reshape(-1,3)), axis = 0)

  return measured_RGB_array

def mix_and_measure_withwrench(compositions_array, vial_index_array, total_volume = 5, simulate=False):
  """Function that mixes a ternary mixture and measures the color
  Thows a monkey wrench in the works by injecting a spurious measurement."""

  measured_RGB_array = np.empty((0, 3))

  for vial_index, compositions in zip(vial_index_array, compositions_array):

    component_mL = compositions * total_volume

    if simulate == False:

      measured_RGB,_ =colormix(vial_index, component_mL)

      measured_RGB_array = np.concatenate((measured_RGB_array, measured_RGB.reshape(-1,3)), axis = 0)


    if simulate == True:

      A_dye = np.array([243.0, 12.0, 50.0])
      B_dye = np.array([100.0, 240.0, 0.0])
      C_dye = np.array([50.0, 2.0, 250.0])

      a_RGB = A_dye * compositions[0]
      b_RGB = B_dye * compositions[1]
      c_RGB = C_dye * compositions[2]

      measured_RGB = a_RGB + b_RGB + c_RGB
      if vial_index == 7:
        measured_RGB = np.array([255, 255, 255])
        print("Monkey wrench in the works!")

      measured_RGB_array = np.concatenate((measured_RGB_array, measured_RGB.reshape(-1,3)), axis = 0)

  return measured_RGB_array



def transform(RGB):

  #Range must have a mean of 0. So for RGB values [0,255] we should subtract 127.5
  #Center the mean
  y = RGB - 127.5

  # #map range to -1,1
  y = y/127.5
  y = y*(1 - 1e-16) #Slightly scale to narrow the range for numerical stability at RGB = 0 or 255

  #Now to capture anything that falls outside that range
  #squash range with tanh
  y = np.arctanh(y)
  return y

def reverse_transform(y):
  #Reverse the squashing with arctanh
  y = np.tanh(y)

  #Mulitply by 127.5 to increase the range and add 127.5 to bring range to [0, 255]
  RGB = y*127.5 + 127.5

  return RGB

def train(training_x, training_y):
  """Function that builds a GP model and trains it
  expects training_x in 3D compositions
  and training y in 3D RGB values (i.e. [R, G, B])."""
  #Define the model
  kernel1 = GPy.kern.RBF(input_dim=3, variance=1., lengthscale=1.)
  kernel2 = GPy.kern.Coregionalize(input_dim = 1, output_dim=3, rank=3 )

  kernel = kernel1 * kernel2

  #Range must have a mean of 0. So for RGB values [0,255] we should subtract 128
  # train_y = training_y - 128
  train_y = transform(training_y)

  m = GPy.models.GPRegression(training_x, train_y, kernel)

  #Optimize the model
  m.optimize()

  return m

def predict(m, test_x):

  mean, var = m.predict(test_x)

  #We subtracted 128 from the training points, so we should add those back.
  # mean = mean + 128
  mean = reverse_transform(mean)

  return mean, var

def pure_explore(mean, var):
  next = np.argmax(var)
  return next

def min_confidence_to_target(mean, var, targetRGB):
  #Calculate the distance to the target
  diff = np.abs(mean - targetRGB)
  diff = np.sum(diff, axis=1).reshape(-1,1)

  #Calculate the confidence uncertainty in the diff
  sigma_diff = np.sqrt(var)

  #Find the index of the minimum of the lower confidence bound on the diff.
  acq_funct = diff - 2*sigma_diff
  next = np.argmin(acq_funct)

  return next, acq_funct


def discover_color_AL_campaign(starting_measurements, max_loops, simulate ):
    #Number of random data points to start with
    # starting_measurements = 2

    #Number of active learning loops
    # max_loops = 20

    #Set-up the domain of mixtures
    A_mesh, B_mesh, C_mesh = get_triangular_grid(101)

    A_mesh = A_mesh.reshape(-1, 1)
    B_mesh = B_mesh.reshape(-1, 1)
    C_mesh = C_mesh.reshape(-1, 1)

    compositions = np.hstack([A_mesh, B_mesh, C_mesh])
    comp_2d = compositions_2d(compositions)

    domain_index = np.arange(compositions.shape[0])

    groundtruth_RGB = mix_and_measure(compositions, domain_index, 5, simulate=True)

    #Choose the first random points
    next_indexes = np.random.choice(domain_index, starting_measurements).reshape(-1,1)

    #Set up vial index container
    vial_index_array = np.arange(starting_measurements)

    #Set up containers for the measured compositions and RGB
    measured_indexes = np.empty((0, 1))
    measured_compositions = np.empty((0, 3))
    measured_RGB = np.empty((0, 3))

    for i in range(max_loops):
        #Find the compositions to be measured
        next_compositions = compositions[next_indexes].reshape(-1,3)

        #Find the next vials to be used
        ###count how many measurements have been done, and slice those off the vial index array
        next_vials = vial_index_array[measured_indexes.shape[0]:]

        #Mix those compositions and measure the RGB of them
        next_RGB = mix_and_measure(next_compositions,
                                    next_vials,
                                    5, simulate=simulate)
        print("Next vials \n")
        print(next_vials)
        print("Next RGB \n")
        print(next_RGB)

        #Add results to containers
        measured_indexes = np.concatenate((measured_indexes, next_indexes), axis=0)
        measured_compositions = np.concatenate((measured_compositions, next_compositions), axis=0)
        measured_RGB = np.concatenate((measured_RGB, next_RGB), axis=0)

        #Train the model
        model = train(measured_compositions, measured_RGB)

        #Predict over the whole domain
        mean, var = predict(model, compositions)

        #Acquire
        next_indexes = pure_explore(mean, var)
        next_indexes = next_indexes.reshape(-1,1)

        #Add the next vial to the array
        vial_index_array = np.concatenate((vial_index_array,
                                        vial_index_array[-1].reshape(-1) + 1),
                                        axis=0)

        #Plot
        fig1 = plt.figure(figsize = (6,24))
        ax1 = fig1.add_subplot(131, projection="ternary")
        ax1.scatter(compositions[:,0], compositions[:,1], compositions[:,2],
                    marker= "o",
                    facecolors = mean/256,
                    s = 10,
                    alpha=1,
                    # edgecolors='r'
                    )

        ax1.scatter(measured_compositions[:,0], measured_compositions[:,1], measured_compositions[:,2],
                    marker= "x",
                    facecolors = "k",
                    s = 10,
                    alpha=1,
                    # edgecolors='r'
                    )
        ax1.scatter(compositions[next_indexes,0],
                    compositions[next_indexes,1],
                    compositions[next_indexes,2],
                    marker= "o",
                    facecolors = 'none',
                    s = 100,
                    alpha=1,
                    edgecolors='k'
                    )
        ax1.set_tlabel('A')
        ax1.set_llabel('B')
        ax1.set_rlabel('C')
        ax1.set_title('Predictions')
        # plt.show()

        # fig1 = plt.figure(figsize = (6,6))
        ax2 = fig1.add_subplot(132, projection="ternary")
        ax2.scatter(compositions[:,0], compositions[:,1], compositions[:,2],
                    marker= "o",
                    c = var.reshape(-1),
                    cmap = "plasma",
                    s = 10,
                    alpha=1,
                    # edgecolors='r'
                    )

        ax2.scatter(measured_compositions[:,0], measured_compositions[:,1], measured_compositions[:,2],
                    marker= "x",
                    facecolors = "k",
                    s = 10,
                    alpha=1,
                    # edgecolors='r'
                    )
        ax2.scatter(compositions[next_indexes,0],
                    compositions[next_indexes,1],
                    compositions[next_indexes,2],
                    marker= "o",
                    facecolors = 'none',
                    s = 100,
                    alpha=1,
                    edgecolors='k'
                    )
        ax2.set_tlabel('A')
        ax2.set_llabel('B')
        ax2.set_rlabel('C')
        ax2.set_title('Uncertainty')

        diff = np.abs(groundtruth_RGB - mean)
        diff = np.sum(diff, axis=1).reshape(-1)
        # ax3 = fig1.add_subplot(133, projection="ternary")
        # ax3.scatter(compositions[:,0], compositions[:,1], compositions[:,2],
                    # marker= "o",
                    # c = diff,
                    # cmap = "plasma",
                    # s = 10,
                    # alpha=1,
                    # # edgecolors='r'
                    # )

        # ax3.scatter(measured_compositions[:,0], measured_compositions[:,1], measured_compositions[:,2],
                    # marker= "x",
                    # facecolors = "k",
                    # s = 10,
                    # alpha=1,
                    # # edgecolors='r'
                    # )
        # ax3.scatter(compositions[next_indexes,0],
                    # compositions[next_indexes,1],
                    # compositions[next_indexes,2],
                    # marker= "o",
                    # facecolors = 'none',
                    # s = 100,
                    # alpha=1,
                    # edgecolors='k'
                    # )
        # ax3.set_tlabel('A')
        # ax3.set_llabel('B')
        # ax3.set_rlabel('C')
        # ax3.set_title('Diff to Ground Truth')
        plt.savefig('colorfig.png')
        plt.savefig(f'colorfig_{i}')