import numpy as np

# from drmxlt_MOF.ternary_composition_utils import random_ternary_composition
from .ternary_composition_utils import random_ternary_composition, generate_simplex_grid
from drmxlt_MOF.op_scheduler import create_unit_ops_df, assign_reactors, define_cp_job

class Experiment():
    """"Base class for all experiments"""
    
    #number of initial samples
    initial_samples : int = 3
    #sample code length in number of characters
    code_length : int = 4 

    #sample db
    sample_db : dict = {}
    #TODO: push sample db to Cordra?
        #This is the initialization of the sample_db

    #fluids
    fluid_db : dict = {}
    #TODO: push fluid db to Cordra?
        #This is the initialization of the fluid_db

    def __init__(self):
        self.generate_sample_db()

    def generate_sample_db(self):
        sample_codes = []
        for i in range(self.initial_samples):
            code = self.generate_sample_codes(existing_code_list=sample_codes)
            sample_codes.append(code)

        #Generate initial addresses 
        sample_addresses = np.zeros(shape=(self.initial_samples, 3), dtype=int)

        for ID, address in zip(sample_codes, sample_addresses):
            sub_db = {"Sample ID": ID, "Address": address}

            self.sample_db[ID] = sub_db
        #TODO: push sample db to Cordra
        

    def generate_sample_codes(self, existing_code_list):
        """This function will generate a new code, 
        checking existing_code_list make sure that code has not been used yet."""
          
        alphabet = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        np_alphabet = np.array(alphabet)  

        #Choose from set of characters and join into a string
        np_code = np.random.choice(np_alphabet, [1, self.code_length])
        new_code = ["".join(np_code[i]) for i in range(len(np_code))]

        
        #Check to see if there would be enough possible codes (this generation method is very inefficient if number of existing codes is a significant fraction of possible codes)
        if len(existing_code_list) >= len(np_alphabet)**self.code_length:
            raise Exception("No more codes available")

        #Check to make sure that new code isn't in use, if not try again. (should work if it passed the above test, albiet potentially very inefficiently)
        if new_code in existing_code_list:
            new_code = self.generate_sample_codes(self, existing_code_list)

        return new_code[0]
    

    def find_address(self, Sample_ID):
        return self.sample_db[Sample_ID]["Address"]
    
    def single_fluid_check(self, vol_needed, name):

        fluid_remaining = self.fluid_db[name]["Volume (mL)"]
        fluid_purge = self.fluid_db[name]["Purged"]
        if fluid_purge == False:
            vol_needed += self.fluid_db[name]["Purg Vol."] #Add the volume needed to purge

        enough_fluid = fluid_remaining - vol_needed > self.fluid_db[name]["Empty threshold"]

        return enough_fluid, vol_needed
    




class Ternary_colordemo(Experiment):
    """Class for exploring the ternary compositions for a colormap"""

    def __init__(self):
        super().__init__()
        self.initialize_target_compositions()
        self.define_experiment_conditions()
        self.initalize_fluid_db()

    def initialize_target_compositions(self):
        compositions = random_ternary_composition(self.initial_samples)

        for key, comp in zip(self.sample_db.keys(), compositions):
            self.sample_db[key]["TargetComposition"] = comp
        #TODO: push sample db to Cordra

    
    def define_experiment_conditions(self, total_exp_vol = 10):

        """ In this example experiment, we'll use 1 ml of a contrast fluid in each experiment
        then the remaining volume will be for the precusors.
        This experiment considers a ternary precusor composition.
        """
        

        for key in list(self.sample_db.keys()):
            #Specify the order to add the fluids
            self.sample_db[key]["Fluid Order"] = ["Contrast", "Precursor 1", "Precursor 2", "Precursor 3" ]

            targetcomposition = self.sample_db[key]["TargetComposition"]

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

            self.sample_db[key]["Experiment Volumes (mL)"] = exp_volumes
        #TODO: push sample db to Cordra
    
    def add_new_sample(self, compositions, total_exp_vol = 10):
        """This function will add new samples to the existing sample database"""

        #Find existing sample codes
        existing_codes = []
        for key in self.sample_db.keys():
            existing_codes.append(self.sample_db[key]["Sample ID"])

        for comp in compositions:
            code = self.generate_sample_codes(existing_codes)
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
            self.sample_db[code] = sub_db
        #TODO: push sample db to Cordra


    def find_compositions(self, Sample_ID):
        return self.sample_db[Sample_ID]["TargetComposition"]
    
    def initalize_fluid_db(self):

        self.fluid_db["Contrast 1"] = {"Fluid Name": "Almond Milk 1",
                                "Volume (mL)": 10,
                                "Address": np.array([1, 1, 4]), # Vial rack, right rack, position 4
                                "Purged": True, #Vial rack gets pipette tips, Does not need purge
                                "Purg Vol.": 0, #Vial rack gets pipette tips, Does not need purge
                                "Empty threshold": 1 # mL
                                }


        self.fluid_db["Contrast 2"] = {"Fluid Name": "Almond Milk 2",
                                "Volume (mL)": 10,
                                "Address": np.array([1, 1, 5]), # Vial rack, right rack, position 5
                                "Purged": True, #Vial rack gets pipette tips, Does not need purge
                                "Purg Vol.": 0, #Vial rack gets pipette tips, Does not need purge
                                "Empty threshold": 1 # mL
                                }

        self.fluid_db["Precursor 1"] = {"Fluid Name": "Precursor 1",
                                "Volume (mL)": 300,
                                "Address": np.array([5, 3, 0]), # Syringe Pump, Pump index 1, splitter valve position 0
                                "Purged": False,
                                "Purg Vol.": 0.6,
                                "Empty threshold": 10 # mL
                                }


        self.fluid_db["Precursor 2"] = {"Fluid Name": "Precursor 2",
                                "Volume (mL)": 300,
                                "Address": np.array([5, 4, 0]), # Syringe Pump, Pump index 2, splitter valve position 0
                                "Purged": False,
                                "Purg Vol.": 0.6,
                                "Empty threshold": 10 # mL
                                }

        self.fluid_db["Precursor 3"] = {"Fluid Name": "Precursor 3",
                                "Volume (mL)": 300,
                                "Address": np.array([5, 5, 0]), # Syringe Pump, Pump index 1, splitter valve position 0
                                "Purged": False,
                                "Purg Vol.": 0.6,
                                "Empty threshold": 10 # mL
                                }

        self.fluid_db["Solvent 1"] = {"Fluid Name": "Solvent 1",
                                "Volume (mL)": 300,
                                "Address": np.array([5, 4, 0]), # Syringe Pump, Pump index 3, splitter valve position 0
                                "Purged": False,
                                "Purg Vol.": 10,
                                "Empty threshold": 10 # mL
                                }
        #TODO: push fluid db to Cordra

        #TODO
        # Test fluid db for:
        ## vials were loaded, but unassigned before?
        ## If at a syringe pump,
        ### Not pump index 0 - reserved for arm
        ### if splitter valve index != 0
        #### Splitter valve installed on that pump?





    
    def exp_fluid_resource_check(self, Sample_ID):
        #Read the target volumes of eaach fluid for this sample
        exp_volumes = self.sample_db[Sample_ID]["Experiment Volumes (mL)"]

        #Check for Contrast:
        contrast_vol = exp_volumes["Contrast"]
        #Try contrast 1
        assigned_contrast = "Contrast 1"
        enough_contrast_1, contrast_needed = self.single_fluid_check(contrast_vol, 'Contrast 1')
        enough_contrast = enough_contrast_1
        if enough_contrast == False:
            #If not enough in contrast 1, check contrast 2
            assigned_contrast = "Contrast 2"
            enough_contrast, contrast_needed = self.single_fluid_check(contrast_vol, 'Contrast 2')

        if enough_contrast == False:
            #If there is still not enough constrat
            raise Exception("Not enough contrast")
        
        #Re-name the contrast with the assigned contrast
        self.sample_db[Sample_ID]["Experiment Volumes (mL)"][assigned_contrast] = self.sample_db[Sample_ID]["Experiment Volumes (mL)"].pop("Contrast")
        self.sample_db[Sample_ID]['Fluid Order'] = [item.replace('Contrast', assigned_contrast) for item in self.sample_db[Sample_ID]['Fluid Order']]  


        #Check precusors
        precursor_1_vol = exp_volumes["Precursor 1"]
        precursor_2_vol = exp_volumes["Precursor 2"]
        precursor_3_vol = exp_volumes["Precursor 3"]

        enough_precursor_1, precursor_1_needed = self.single_fluid_check(precursor_1_vol, 'Precursor 1')
        if enough_precursor_1 == False:
            raise Exception("Not enough precursor 1")

        enough_precursor_2, precursor_2_needed = self.single_fluid_check(precursor_2_vol, 'Precursor 2')
        if enough_precursor_2 == False:
            raise Exception("Not enough precursor 2")
        
        enough_precursor_3, precursor_3_needed = self.single_fluid_check(precursor_3_vol, 'Precursor 3')
        if enough_precursor_3 == False:
            raise Exception("Not enough precursor 2")


        fluid_assignments = {assigned_contrast: contrast_needed, 
                            "Precursor 1": precursor_1_needed, 
                            "Precursor 2": precursor_2_needed,
                            "Precursor 3": precursor_3_needed}

        return fluid_assignments


class Cu_BTC(Experiment):


    def __init__(self):
        super().__init__()
        self.initialize_target_compositions()
        self.initialize_fluid_db()
        self.define_experiment_conditions()
        self.initialize_reaction_conditions()
        self.build_unit_ops_df()

    def initialize_reaction_conditions(self):
        temperatures = np.random.uniform(40, 80, self.initial_samples)

        times = np.random.uniform(np.log10(2), np.log10(10), self.initial_samples)
        times = np.power(10, times)

        for key, temp, time in zip(self.sample_db.keys(), temperatures, times):
            self.sample_db[key]["Temperature (C)"] = temp
            self.sample_db[key]["Reaction Time (min)"] = time


    def initialize_target_compositions(self): 
        min_Cu_concentration = 0.5 #mol/L
        max_Cu_concentration = 2.0 #mol/L

        Cu_concentrations = np.random.uniform(min_Cu_concentration, max_Cu_concentration, self.initial_samples)
        
        for key, Cu_conc in zip(self.sample_db.keys(), Cu_concentrations):
            self.sample_db[key]["Target Cu Concentration (mol/L)"] = Cu_conc
            self.sample_db[key]["Target BTC Concentration (mol/L)"] = 0.2
        #TODO: push sample db to Cordra

    def define_experiment_conditions(self):

        """ In this example experiment, we'll use concentrated precursors solution and a solvent mixture.
        We'll dispense the concentrated stock and dilute in the vial to the desired concentration
        """
        

        for key in list(self.sample_db.keys()):
            #Specify the order to add the fluids
            self.sample_db[key]["Fluid Order"] = ["Cu Solution", "Solvent Mixture", "BTC Solution" ]

            exp_volumes = {}
            
            target_BTC_concentration = self.sample_db[key]["Target BTC Concentration (mol/L)"]
            target_Cu_concentration = self.sample_db[key]["Target Cu Concentration (mol/L)"]

            stock_BTC_concentration = self.fluid_db["BTC Solution"]["Concentration (mol/L)"]
            stock_Cu_concentration = self.fluid_db["Cu Solution"]["Concentration (mol/L)"]

            total_BTC_vol = 5 #mL
            total_Cu_vol = 5 #mL
            
            BTC_dispense_vol = total_BTC_vol*target_BTC_concentration/stock_BTC_concentration
            Cu_dispense_vol = total_Cu_vol*target_Cu_concentration/stock_Cu_concentration

            solvent_to_dilute_BTC = total_BTC_vol - BTC_dispense_vol
            solvent_to_dilute_Cu = total_Cu_vol - Cu_dispense_vol

            solvent_dispense_vol = solvent_to_dilute_BTC + solvent_to_dilute_Cu 


            exp_volumes["BTC Solution"] = BTC_dispense_vol
            exp_volumes["Cu Solution"] = Cu_dispense_vol
            exp_volumes["Solvent Mixture"] = solvent_dispense_vol

            #Add that info to sample database

            self.sample_db[key]["Experiment Volumes (mL)"] = exp_volumes
        #TODO: push sample db to Cordra
    
    def add_new_sample(self, Cu_concentrations):
        """This function will add new samples to the existing sample database"""

        #Find existing sample codes
        existing_codes = []
        for key in self.sample_db.keys():
            existing_codes.append(self.sample_db[key]["Sample ID"])

        for Cu_conc in Cu_concentrations:
            code = self.generate_sample_codes(existing_codes)
            address = np.zeros(shape=(1,3), dtype= int)

            self.sample_db[key]["Fluid Order"] = ["Cu Solution", "Solvent Mixture", "BTC Solution" ]

            exp_volumes = {}
            
            target_BTC_concentration = self.sample_db[key]["Target BTC Concentration (mol/L)"]
            target_Cu_concentration = self.sample_db[key]["Target Cu Concentration (mol/L)"]

            stock_BTC_concentration = self.fluid_db["BTC Solution"]["Concentration (mol/L)"]
            stock_Cu_concentration = self.fluid_db["Cu Solution"]["Concentration (mol/L)"]

            total_BTC_vol = 5 #mL
            total_Cu_vol = 5 #mL
            
            BTC_dispense_vol = total_BTC_vol*target_BTC_concentration/stock_BTC_concentration
            Cu_dispense_vol = total_Cu_vol*target_Cu_concentration/stock_Cu_concentration

            solvent_to_dilute_BTC = total_BTC_vol - BTC_dispense_vol
            solvent_to_dilute_Cu = total_Cu_vol - Cu_dispense_vol

            solvent_dispense_vol = solvent_to_dilute_BTC + solvent_to_dilute_Cu 


            exp_volumes["BTC Solution"] = BTC_dispense_vol
            exp_volumes["Cu Solution"] = Cu_dispense_vol
            exp_volumes["Solvent Mixture"] = solvent_dispense_vol

            #Add that info to sample database

            self.sample_db[key]["Experiment Volumes (mL)"] = exp_volumes


            #Package that to the sample database
            sub_db = {"Sample ID": code, "TargetComposition": comp, "Address": address}
            sub_db["Experiment Volumes (mL)"] = exp_volumes
            self.sample_db[code] = sub_db
        #TODO: push sample db to Cordra
    
    def find_compositions(self, Sample_ID):
        return self.sample_db[Sample_ID]["Target Cu Concentration (mol/L)"]
    

    def initialize_fluid_db(self):

        self.fluid_db["Cu Solution"] = {"Fluid Name": "Cu Solution",
                                "Volume (mL)": 300,
                                "Address": np.array([5, 2, 0]), # Syringe Pump, Pump index 1, splitter valve position 0
                                "Purged": False,
                                "Purg Vol.": 1.6,
                                "Empty threshold": 10, # mL
                                "Concentration (mol/L)": 3.0
                                }
        
        self.fluid_db["BTC Solution"] = {"Fluid Name": "BTC Solution",
                                "Volume (mL)": 300,
                                "Address": np.array([5, 4, 0]), # Syringe Pump, Pump index 1, splitter valve position 0
                                "Purged": False,
                                "Purg Vol.": 1.8,
                                "Empty threshold": 10, # mL
                                "Concentration (mol/L)": 0.2
                                }

        self.fluid_db["Solvent Mixture"] = {"Fluid Name": "Water",
                                "Volume (mL)": 300,
                                "Address": np.array([5, 5, 0]), # Syringe Pump, Pump index 3, splitter valve position 0
                                "Purged": False,
                                "Purg Vol.": 1.7,
                                "Empty threshold": 10 # mL
                                }
        #TODO: push fluid db to Cordra



    
    def exp_fluid_resource_check(self, Sample_ID):
        #Read the target volumes of eaach fluid for this sample
        exp_volumes = self.sample_db[Sample_ID]["Experiment Volumes (mL)"]

        #Check precusors
        precursor_1_vol = exp_volumes["Cu Solution"]
        precursor_2_vol = exp_volumes["BTC Solution"]
        precursor_3_vol = exp_volumes["Solvent Mixture"]

        enough_precursor_1, precursor_1_needed = self.single_fluid_check(precursor_1_vol, 'Cu Solution')
        if enough_precursor_1 == False:
            raise Exception("Not enough precursor 1")

        enough_precursor_2, precursor_2_needed = self.single_fluid_check(precursor_2_vol, 'BTC Solution')
        if enough_precursor_2 == False:
            raise Exception("Not enough precursor 2")
        
        enough_precursor_3, precursor_3_needed = self.single_fluid_check(precursor_3_vol, 'Solvent Mixture')
        if enough_precursor_3 == False:
            raise Exception("Not enough precursor 2")


        fluid_assignments = {"Cu Solution": precursor_1_needed, 
                            "BTC Solution": precursor_2_needed,
                            "Solvent Mixture": precursor_3_needed}

        return fluid_assignments
    
    def build_unit_ops_df(self):
        #TODO pull number of reactors, centrifuge, sonicators, and postions from system_db

        #Create the inital list of unit ops for each sample
        unit_ops_df = create_unit_ops_df(self.sample_db, 
                                         Add_fluids = True, 
                                         React = True, 
                                         Centrifuge = False, 
                                         Remove_supernatent = False, 
                                         Sonicate = False)
        
        #Assign reactions to reactors
        unit_ops_df, reactor_df = assign_reactors(unit_ops_df, 
                                                  number_of_reactors = 2, 
                                                  positions_in_reactor = 2)
        
        #Constratin Satisfaction problem scheduling
        unit_ops_df, overall_time = define_cp_job(unit_ops_df, 
                                                  reactors = 2)
        
        #TODO: interleave reactor pre-heating steps
        

        self.unit_ops_df = unit_ops_df
        self.reactor_df = reactor_df
        self.overall_time = overall_time
        #TODO: push unit_ops_df to Cordra
        #TODO: push reactor_df to Cordra
        
