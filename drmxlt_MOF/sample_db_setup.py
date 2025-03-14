import numpy as np

# Generate some sample names
num_samples = 10

#Generate random ids for those samples
LENGTH = 4 # How many characters in the code
NO_CODES = num_samples # How many samples

alphabet = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
np_alphabet = np.array(alphabet)
np_codes = np.random.choice(np_alphabet, [NO_CODES, LENGTH])
codes = ["".join(np_codes[i]) for i in range(len(np_codes))]

#Generate Binary compositions for those samples
compositions = np.random.random(size=(num_samples, 1))
compositions = np.concatenate((compositions, 1 - compositions), axis = 1)

#Generate Random Temperatures
temperatures = np.random.normal(loc = 175, scale= 25, size=(num_samples, 1))

#Generate Random Annealing Time
annealing_powers = np.random.normal(loc = np.log10(10), scale= .75, size=(num_samples, 1))
annealing_times = 10**annealing_powers

#Generate initial addresses 
sample_addresses = np.zeros(shape=(num_samples, 3), dtype=int)


#Initialize sample db container
sample_db = {}

for ID, comp, temp, anneal_time, address in zip(codes, compositions, temperatures, annealing_times, sample_addresses):
  sub_db = {"Sample ID": ID, "TargetComposition": comp, "AnnealingTemperature": temp, "AnnealingTime": anneal_time, "Address": address}

  sample_db[ID] = sub_db


def define_experiment_conditions(sample_db, total_exp_vol = 10):

  """ In this example experiment, we'll use 1 ml of a contrast fluid in each experiment
  then the remaining volume will be for the precusors.
  This experiment considers a binary precusor composition.
  """

  for key in list(sample_db.keys()):

    targetcomposition = sample_db[key]["TargetComposition"]

    exp_volumes = {}

    #Contrast
    contrast_vol = 1.0 #ml

    exp_volumes["Contrast"] = contrast_vol

    #Precusors
    total_precusor_vol = total_exp_vol - contrast_vol

    precursor_1_vol = targetcomposition[0] * total_precusor_vol
    precursor_2_vol = targetcomposition[1] * total_precusor_vol

    exp_volumes["Precursor 1"] = precursor_1_vol
    exp_volumes["Precursor 2"] = precursor_2_vol

    #Add that info to sample database

    sample_db[key]["Experiment Volumes (mL)"] = exp_volumes

  return sample_db


sample_db = define_experiment_conditions(sample_db)

def find_compositions(Sample_ID):
  return sample_db[Sample_ID]["TargetComposition"]

def find_temperature(Sample_ID):
  return sample_db[Sample_ID]["AnnealingTemperature"]

def find_time(Sample_ID):
  return sample_db[Sample_ID]["AnnealingTime"]

def find_address(Sample_ID):
  return sample_db[Sample_ID]["Address"]

