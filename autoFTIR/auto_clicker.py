import pyautogui
import time

class AutoClicker:
    def __init__(self):
         self.button_measure = None
         self.button_background = None
         self.button_expt_set = None
         self.button_after_mins = None
         self.button_ok = None

    def setup_autopro(self):
        self.button_measure = self.get_coords_m()
        self.button_background = self.get_coords_b()

    def setup_omnic(self):
        self.button_expt_set = self.get_expt_set()
        self.button_after_mins = self.get_after_mins()
        self.button_ok = self.get_ok()

    def get_coords_m(self):
        print("Get ready to set measurement...")
    # Countdown so you have time to move your mouse
        for i in range(5, 0, -1):
            print(f"{i}...", end=" ", flush=True)
            time.sleep(1)
    # Capture the current mouse position
        point_a = pyautogui.position() 
        print(f"\nCaptured measurement at: {point_a}")
        return point_a 

    def get_coords_b(self):
        print("Get ready to set background...")
    # Countdown so you have time to move your mouse
        for i in range(5, 0, -1):
            print(f"{i}...", end=" ", flush=True)
            time.sleep(1)
    
    # Capture the current mouse position
        point_b = pyautogui.position() 
        print(f"\nCaptured background at: {point_b}")
        return point_b 
    
    def get_expt_set(self):
        print("Get ready to set Expt Set")
        for i in range (5, 0, -1):
            print(f"{i}...", end=" ", flush=True)
            time.sleep(1)
        point_expt = pyautogui.position()
        return point_expt
    
    def get_after_mins(self):
        print("Get ready to set collect bg after x mins")
        for i in range (5, 0, -1):
            print(f"{i}...", end=" ", flush=True)
            time.sleep(1)
        point_after = pyautogui.position()
        return point_after
    
    def get_ok(self):
        print("Get ready to set OK")
        for i in range (5, 0, -1):
            print(f"{i}...", end=" ", flush=True)
            time.sleep(1)
        point_ok = pyautogui.position()
        return point_ok

# Now you can use them as variables
#print(f"Point A is {point_a}")
#print(f"Point B is {point_b}")

# Example: Accessing X and Y individually
#print(f"The X coordinate of Point A is: {point_a.x}")


    def run_clicker(self,n=2, i=1):
        if self.button_measure is None or self.button_background is None:
             print("Coordinates not set! Please run setup_coordinates() first.")
             return
        
        print("Starting Clicker in 5 seconds")
        time.sleep(5)
        while n > 0:
                print(f"--- Step {i} ---")
                print("Taking Background")
                pyautogui.click(self.button_background)
                time.sleep(5) #need to make it trigger when background measurement file is saved?
                print("Taking Measurement")
                pyautogui.click(self.button_measure)
                time.sleep(5) #same thing as with the bg measurement
                i += 1
                n -= 1
        print("Measurement Compelete!")
        return
    
    def click_bg(self):
         pyautogui.click(self.button_background)
         print("Background Taken")
         return
    
    def click_meas(self):
         pyautogui.click(self.button_measure)
         print("Measurement Taken")
         return
    
    def click_expt_set(self):
         pyautogui.click(self.button_expt_set)
         print("Expt Set Clicked")
         return
    
    def click_after_mins(self):
         pyautogui.click(self.button_after_mins)
         print("After Mins Clicked")
         return
    
    def click_ok(self):
        pyautogui.click(self.button_ok)
        print("OK Clicked")
        return


auto = AutoClicker()

#setup_coordinates = auto.setup_coordinates
#get_coords_m = auto.get_coords_m
#get_coords_b = auto.get_coords_b
#run_clicker = auto.run_clicker
