# -------------------------------------------------------------------------
#--------------------------5-CSRTT Pump Flush / Prime Utility--------------------------
# Custom utility script developed for maintenance of the 5-CSRTT fluid-delivery system.
# This script is not part of the original 5-CSRTT training protocol.
#
# Purpose:
#   - prime the reward-delivery tubing with water before behavioral sessions
#   - flush the tubing during cleaning or maintenance
#
# Operation:
#   - reward-port sensor activation initiates pump operation
#   - reward-port exit turns off the indicator LED and returns to the waiting state
#   - pump operates at a higher rate than during behavioral testing
#   - session duration is limited to 30 min as a safety measure


from pyControl.utility import *
import hardware_definition as hw  

# -------------------------------------------------------------------------
# States and Events
# -------------------------------------------------------------------------
states = ['waiting',   
          'pumping']   

events = ['poke_6',      
          'poke_6_out',  
          'session_timer']

initial_state = 'waiting'

# -------------------------------------------------------------------------
# Variables
# -------------------------------------------------------------------------
# 물을 빨리 끌어오기 위해 속도를 높이고, 한 번에 돌릴 스텝 수를 크게 설정합니다.
v.flush_rate = 1000      
v.flush_steps = 5000000   

v.session_dur = 30 * minute 

# -------------------------------------------------------------------------
# Run Start / End Behavior
# -------------------------------------------------------------------------
def run_start():
    if hasattr(hw, 'house_light'): 
        hw.house_light.on() 
    print("Pump Flush/Prime Task Started. Trigger sensor 6 to pump.")

def run_end():
    hw.off()

# -------------------------------------------------------------------------
# State Behavior
# -------------------------------------------------------------------------

def waiting(event):
    if event == 'poke_6':
        goto_state('pumping')

def pumping(event):
    if event == 'entry':
        hw.reward_port.LED.on()
        hw.syringe_pump.backward(v.flush_rate, v.flush_steps) 
        print('Pumping started...')

    elif event == 'poke_6_out':
        hw.reward_port.LED.off()
        print('Pumping stopped.')
        goto_state('waiting')

# -------------------------------------------------------------------------
# All States Behavior
# -------------------------------------------------------------------------
def all_states(event):
    if event == 'session_timer':
        stop_framework()