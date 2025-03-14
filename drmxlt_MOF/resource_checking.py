

def single_fluid_check(vol_needed, name, fluid_db):

  fluid_remaining = fluid_db[name]["Volume (mL)"]
  fluid_purge = fluid_db[name]["Purged"]
  if fluid_purge == False:
    vol_needed += fluid_db[name]["Purg Vol."] #Add the volume needed to purge

  enough_fluid = fluid_remaining - vol_needed > fluid_db[name]["Empty threshold"]

  return enough_fluid, vol_needed

def exp_fluid_resource_check(Sample_ID, sample_db, fluid_db):
  #Read the target volumes of eaach fluid for this sample
  exp_volumes = sample_db[Sample_ID]["Experiment Volumes (mL)"]

  #Check for Contrast:
  contrast_vol = exp_volumes["Contrast"]
  #Try contrast 1
  assigned_contrast = "Contrast 1"
  enough_contrast_1, contrast_needed = single_fluid_check(contrast_vol, 'Contrast 1', fluid_db)
  enough_contrast = enough_contrast_1
  if enough_contrast == False:
    #If not enough in contrast 1, check contrast 2
    assigned_contrast = "Contrast 2"
    enough_contrast, contrast_needed = single_fluid_check(contrast_vol, 'Contrast 2', fluid_db)

  if enough_contrast == False:
    #If there is still not enough constrat
    raise Exception("Not enough contrast")


  #Check precusors
  precursor_1_vol = exp_volumes["Precursor 1"]
  precursor_2_vol = exp_volumes["Precursor 1"]

  enough_precursor_1, precursor_1_needed = single_fluid_check(precursor_1_vol, 'Precursor 1', fluid_db)
  if enough_precursor_1 == False:
    raise Exception("Not enough precursor 1")

  enough_precursor_2, precursor_2_needed = single_fluid_check(precursor_2_vol, 'Precursor 2', fluid_db)
  if enough_precursor_2 == False:
    raise Exception("Not enough precursor 2")


  fluid_assignments = {assigned_contrast: contrast_needed, "Precursor 1": precursor_1_needed, "Precursor 2": precursor_2_needed}

  return fluid_assignments
