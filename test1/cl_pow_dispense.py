from north import NorthC9
from powder_settings import *  # import everything from powder settings, should be in same dir as this script
from time import perf_counter


c9 = NorthC9('A',network_serial="AU06D2C0")  # instantiate a C9 controller object with C9 network address A-
t2=NorthC9('B',network=c9.network)

#c9 = NorthC9('A')  # assumes balance is plugged into C9
p2 = NorthC9('C', network=c9.network)

c9.get_info()
p2.get_info()

def powder_init():
    p2.home_OL_stepper(0, 300)


# set the valve to degrees between 0 and 90
def set_opening(deg):
    p2.move_axis(0, deg * (1000 / 360.0), accel=5000)


# shake the cartridge for t ms, with frequency f [40, 180] hz, amplitude [60, 100] %
def shake(t, f=120, a=100, wait=True):
    return p2.amc_pwm(int(f), int(t), int(a), wait=wait)


# closed loop powder dispense
def cl_pow_dispense(mg_target, protocol=None, zero_scale=False):
    start_t = perf_counter()
    mg_togo = mg_target

    if protocol is None:
        protocol = default_ps
    ps = protocol.fast_settings
    if mg_togo < protocol.slow_settings.thresh:
        ps = protocol.slow_settings
    elif mg_togo < protocol.med_settings.thresh:
        ps = protocol.med_settings

    # intialize
    set_opening(0)  # make sure everything starts closed
    prev_mass = 0
    delta_mass = 0
    shake_t = ps.min_shake_t

    if zero_scale:
        c9.zero_scale()
        c9.delay(protocol.scale_delay)
    tare = c9.read_steady_scale() * 1000

    meas_mass = 0
    count = 0
    while mg_togo > protocol.tol and count<30:
        count += 1

        set_opening(ps.opening_deg)
        shake(shake_t, ps.freq, ps.amplitude)
        if ps.shut_valve:
            set_opening(0)
        c9.delay(0.5)
        c9.read_steady_scale()  # dummy read to wait for steady
        c9.delay(protocol.scale_delay)  # delay after steady to allow for more settling time
        meas_mass = c9.read_steady_scale() * 1000 - tare

        mg_togo = mg_target - meas_mass
        delta_mass = meas_mass - prev_mass
        prev_mass = meas_mass
        
        settings_str='fast setting'
        if mg_togo < protocol.slow_settings.thresh:
            ps = protocol.slow_settings
            settings_str='slow setting'
        elif mg_togo < protocol.med_settings.thresh:
            ps = protocol.med_settings
            settings_str='medium setting'

        iter_target = (ps.percent_target * mg_togo)
        max_new_t = ps.max_growth * shake_t
        if delta_mass <= 0:
            shake_t = max_new_t
        else:
            shake_t *= (iter_target / delta_mass)
        shake_t = min(max_new_t, shake_t)  # no larger than max growth allows
        shake_t = max(ps.min_shake_t, shake_t)  # no shorter than min time
        shake_t = min(ps.max_shake_t, shake_t)  # no longer than max time

        print(f'Iteration {count}:')
        print(f'\tJust dispensed:  {delta_mass:.1f} mg')
        print(f'\tRemaining:       {mg_togo:.1f} mg')
        print(f'\tNext target:     {iter_target:.1f} mg')
        print(f'\tNext time:       {int(shake_t)} ms')
        print(f'\tSetting:         {settings_str}')
        print('')
        
        
        
    set_opening(0)

    print(f'Result:')
    print(f'\tLast iter:  {delta_mass:.1f} mg')
    print(f'\tDispensed: {meas_mass:.1f} mg')
    print(f'\tRemaining: {mg_togo:.1f} mg')
    print(f'\tTime:      {int(perf_counter() - start_t)} s')
    print('')

    return meas_mass



# example usage:
#cl_pow_dispense(20, protocol=default_ps)  # dispense 20mg according to the default powder settings in powder_settings.py