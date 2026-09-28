
#--------------------------5-CSRTT Poke Habituation Protocol--------------------------
# Developed as a pre-training stage prior to the 5-CSRTT task.
# This habituation stage trains animals to:
#   - retrieve reward by poking the reward port
#   - poke any illuminated 5-choice port
#   - alternate between the 5-choice ports and reward port
#
# Additional features:
#   - one reward delivered per reward-port entry
#   - syringe pump step compensation
#   - automatic session termination after 100 rewards or 30 min
from pyControl.utility import *
import hardware_definition as hw

# list of states
states = ['choice',
          'reward']

# list of events
events = ['session_timer',
          'poke_1',
          'poke_2',
          'poke_3',
          'poke_4',
          'poke_5',
          'poke_6',
          'poke_6_out',
          'port_lights_timer',
          'reward_in_timer',
          'penalty_omission',
          'reward_lockout']

# initial state name
initial_state = 'reward'

# variables
v.steps_rate = 250
v.n_steps = 67
v.session_duration = 30 * minute
v.reward_lockout_ms = 100
v.max_trial = 100.         # 자동 종료 trial


v.reward_count = 0         # 실제 보상이 나온 수
v.comp_count = 0           # 보정을 위한 count
v.comp_period = 12         # 주기 설정(360도)
v.comp_list = [2, 6, 10]   # 한번에 6trial이 나오는 부분
v.comp_batch = 2           # 보정 trial

def run_start():
    set_timer('session_timer', v.session_duration)
    hw.reward_port.SOL.on()
    v.in_reward_lockout = False

def run_end():
    hw.off()

def reward(event):
    if event == 'entry':
        v.in_reward_lockout = True
        set_timer('reward_lockout', v.reward_lockout_ms * ms)
        #deliver_reward()
        hw.reward_port.LED.on()
        v.reward_delivered = False

    elif event == 'reward_lockout':
        v.in_reward_lockout = False

    elif event == 'exit':
        hw.reward_port.LED.off()
        hw.speaker.off()

    elif event == 'poke_6':
        #시작 시 poke를 해야 reward 제공
        if not v.reward_delivered:
            #코를 찔렀을 때 단 한 번만 보상 지급
            deliver_reward()
            v.reward_delivered = True
            print('Reward_taken')

    elif event == 'poke_6_out':
        if v.reward_delivered:
            goto_state('choice')

    #elif event == 'poke_6_out' or event == 'poke_6':
        #if v.in_reward_lockout:
            #return
        #hw.reward_port.LED.off()
        #print('reward_obtained')
        #goto_state('choice')

def deliver_reward():

    print('Reward_delivered')

    v.reward_count += 1
    v.comp_count += 1
    k = v.comp_count % v.comp_period
        
    rate2 = v.steps_rate
    v.main_steps = v.n_steps

    if k in v.comp_list:
        # 총 72 맞추기(6trial)
        v.main_steps = v.n_steps * v.comp_batch
        v.comp_count += (v.comp_batch - 1)
        rate2 = v.steps_rate *2

        

    print('COMP: count={}, comp_count={}, period={}, main_steps={}'.format(
        v.reward_count, v.comp_count, k, v.main_steps))

    hw.syringe_pump.backward(rate2, v.main_steps)

    if v.reward_count >= v.max_trial:
                stop_framework()

    

def choice(event):
    if event == 'entry':
        hw.five_poke.poke_1.LED.on()
        hw.five_poke.poke_2.LED.on()
        hw.five_poke.poke_3.LED.on()
        hw.five_poke.poke_4.LED.on()
        hw.five_poke.poke_5.LED.on()

    elif event == 'exit':
        hw.five_poke.poke_1.LED.off()
        hw.five_poke.poke_2.LED.off()
        hw.five_poke.poke_3.LED.off()
        hw.five_poke.poke_4.LED.off()
        hw.five_poke.poke_5.LED.off()
        hw.speaker.off()

    elif event == 'poke_1' or event == 'poke_2' or event == 'poke_3' or event == 'poke_4' or event == 'poke_5':
        hw.five_poke.poke_1.LED.off()
        hw.five_poke.poke_2.LED.off()
        hw.five_poke.poke_3.LED.off()
        hw.five_poke.poke_4.LED.off()
        hw.five_poke.poke_5.LED.off()
        print('Correct_response')
        goto_state('reward')

def all_states(event):
    if event == 'session_timer':
        stop_framework()






