import numpy as np

from ternary_composition_utils import random_ternary_composition

# Generate some sample names
num_samples = 3

#Generate random ids for those samples
LENGTH = 4 # How many characters in the code
NO_CODES = num_samples # How many samples

alphabet = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
np_alphabet = np.array(alphabet)
np_codes = np.random.choice(np_alphabet, [NO_CODES, LENGTH])
codes = ["".join(np_codes[i]) for i in range(len(np_codes))]

#Generate Binary compositions for those samples
compositions = random_ternary_composition(num_samples)

#Generate initial addresses 
sample_addresses = np.zeros(shape=(num_samples, 3), dtype=int)


#Initialize sample db container
sample_db = {}

for ID, comp, address in zip(codes, compositions, sample_addresses):
  sub_db = {"Sample ID": ID, "TargetComposition": comp, "Address": address}

  sample_db[ID] = sub_db


def define_experiment_conditions(sample_db, total_exp_vol = 10):

  """ In this example experiment, we'll use 1 ml of a contrast fluid in each experiment
  then the remaining volume will be for the precusors.
  This experiment considers a ternary precusor composition.
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
    precursor_3_vol = targetcomposition[2] * total_precusor_vol

    exp_volumes["Precursor 1"] = precursor_1_vol
    exp_volumes["Precursor 2"] = precursor_2_vol
    exp_volumes["Precursor 3"] = precursor_3_vol

    #Add that info to sample database

    sample_db[key]["Experiment Volumes (mL)"] = exp_volumes

  return sample_db

def add_new_sample(sample_db, compositions, total_exp_vol = 10):
  """This function will add new samples to the existing sample database"""

  #Find existing sample codes
  existing_codes = []
  for key in sample_db.keys():
    existing_codes.append(sample_db[key]["Sample ID"])

  for comp in compositions:
    code = gernerate_new_sample_code(existing_codes)
    address = np.zeros(shape=(1,3), dtype= int)

    exp_volumes = {}

    #Contrast
    contrast_vol = 1.0 #ml

    exp_volumes["Contrast"] = contrast_vol

    #Precusors
    total_precusor_vol = total_exp_vol - contrast_vol

    precursor_1_vol = comp[0] * total_precusor_vol
    precursor_2_vol = comp[1] * total_precusor_vol
    precursor_3_vol = comp[2] * total_precusor_vol

    exp_volumes["Precursor 1"] = precursor_1_vol
    exp_volumes["Precursor 2"] = precursor_2_vol
    exp_volumes["Precursor 3"] = precursor_3_vol


    #Package that to the sample database
    sub_db = {"Sample ID": code, "TargetComposition": comp, "Address": address}
    sub_db["Experiment Volumes (mL)"] = exp_volumes
    sample_db[code] = sub_db

    return sample_db

def gernerate_new_sample_code(existing_code_list):
  """This function will generate a new code, 
  checking existing_code_list make sure that code has not been used yet."""

  #Choose from set of characters and join into a string
  np_code = np.random.choice(np_alphabet, [1, LENGTH])
  new_code = ["".join(np_code[i]) for i in range(len(np_code))]

  
  #Check to see if there would be enough possible codes (this generation method is very inefficient if number of existing codes is a significant fraction of possible codes)
  if len(existing_code_list) >= len(np_alphabet)**LENGTH:
    raise Exception("No more codes available")

  #Check to make sure that new code isn't in use, if not try again. (should work if it passed the above test, albiet potentially very inefficiently)
  if new_code in existing_code_list:
    new_code = gernerate_new_sample_code(existing_code_list)

  return new_code[0]

sample_db = define_experiment_conditions(sample_db)

def find_compositions(Sample_ID):
  return sample_db[Sample_ID]["TargetComposition"]

def find_temperature(Sample_ID):
  return sample_db[Sample_ID]["AnnealingTemperature"]

def find_time(Sample_ID):
  return sample_db[Sample_ID]["AnnealingTime"]

def find_address(Sample_ID):
  return sample_db[Sample_ID]["Address"]

