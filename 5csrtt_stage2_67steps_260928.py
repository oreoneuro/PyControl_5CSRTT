#--------------------------5-CSRTT Stage 1 Protocol----------------------
# Adapted from KaetzelLab/Operant-Box-Code (tasks/5CSRTT)
#   https://github.com/KaetzelLab/Operant-Box-Code
#   Original authors: Sampath K. T. Kapanaiah, Dennis Kaetzel (Kaetzel Lab)
# Runs on pyControl (https://github.com/pyControl/code), Thomas Akam et al.
#
# Modified by Soyeon Lee, Laboratory of Neuroscience, KOREA UNIVERSITY, 2026-09

# Changes:
#   - Reward delivered only upon reward-port entry, including the initial reward
#   - One reward delivery allowed per reward state to prevent duplicate rewards
#   - Reward-port exit debounce (2 s) to prevent false exit detection
#   - First trial passes through ITI, matching the sequence of subsequent trials
#   - Syringe pump parameters adjusted and periodic step compensation added
#   - Correct/error auditory feedback added
#   - Trial, response, omission, premature-response, and poke-frequency counters added
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.


from pyControl.utility import *
import hardware_definition as hw
import random

# States and events
states = ['start',
          'choice_task',
          'reward',
          'penalty',
          'iti']

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
          'distraction_on_timer',
          'distraction_off_timer',
          'feedback_off',
          'reward_port_exit_timer']  # debounce: 진짜 포트 이탈 확인용

initial_state = 'start'

# ---------------- Variables ----------------

# Stage parameters
v.state_dur = 8 * second
v.ITI_dur   = 2 * second
v.variable_ITI = False
v.sound_distraction = False

v.trials = 0
v.omission_num = 0
v.premature_num = 0
v.correct_num = 0
v.incorrect_num = 0

v.poke_1_frequency = 0
v.poke_2_frequency = 0
v.poke_3_frequency = 0
v.poke_4_frequency = 0
v.poke_5_frequency = 0

# Other parameters
v.session_dur   = 30 * minute
v.LH_dur        = 2 * second
v.reward_in_dur = 5 * second
v.penalty_dur   = 5 * second

# ---- Pump parameters ----
v.steps_rate    = 250
v.n_steps       = 67

# ---- Compensation variables ----
v.reward_count = 0
v.comp_count = 0
v.comp_period = 12
v.comp_list = [2, 6, 10]
v.comp_batch = 2

v.target = 0

# Feedback sound
v.sound_feedback = True
v.correct_sound_ms = 60
v.error_sound_ms = 200
v.correct_volume = 10
v.error_volume = 30

# one-shot flag to prevent multiple reward triggers inside reward state
v.reward_given_this_state = False

# Reward port exit debounce: 왔다갔다 무시하고 진짜 이탈만 감지
v.reward_port_exit_debounce = 2 * second

# ---------------- Run start/end ----------------
def run_start():
    set_timer('session_timer', v.session_dur)
    hw.house_light.on()

def run_end():
    hw.off()
    hw.house_light.off()

# ---------------- helper: feedback sound ----------------
def play_feedback(is_correct):
    if not v.sound_feedback:
        return
    if is_correct:
        hw.speaker.set_volume(v.correct_volume)
        hw.speaker.noise()
        set_timer('feedback_off', v.correct_sound_ms * ms)
    else:
        hw.speaker.set_volume(v.error_volume)
        hw.speaker.noise()
        set_timer('feedback_off', v.error_sound_ms * ms)

# ---------------- helper: deliver reward with compensation ----------------
def deliver_reward():
    print('Reward_delivered')

    v.reward_count += 1
    v.comp_count += 1
    k = v.comp_count % v.comp_period

    rate2 = v.steps_rate
    v.main_steps = v.n_steps

    if k in v.comp_list:
        v.main_steps = v.n_steps * v.comp_batch
        v.comp_count += (v.comp_batch - 1)
        rate2 = v.steps_rate * 2

    print('COMP: count={}, comp_count={}, period={}, main_steps={}'.format(
        v.reward_count, v.comp_count, k, v.main_steps))

    hw.syringe_pump.backward(rate2, v.main_steps)

# ---------------- State functions ----------------
def start(event):
    if event == 'entry':
        hw.reward_port.LED.on()
        v.reward_given_this_state = False      # changed: was deliver_reward()

    elif event == 'poke_6':
        if v.reward_given_this_state:          # already gave water this trial
            disarm_timer('reward_port_exit_timer')
            return
        deliver_reward()                       # first poke only
        v.reward_given_this_state = True

    elif event == 'poke_6_out':
        set_timer('reward_port_exit_timer', v.reward_port_exit_debounce)  

    elif event == 'reward_port_exit_timer':
        print("ITI_duration:{} \n SD_duration:{}\n LH_duration:{}".format(
            v.ITI_dur, v.state_dur, v.LH_dur))
        goto_state('iti')                      

    elif event == 'exit':
        hw.reward_port.LED.off()
        disarm_timer('reward_in_timer')
        disarm_timer('reward_port_exit_timer')


def choice_task(event):
    if event == 'entry':
        set_timer('port_lights_timer', v.state_dur)
        set_timer('penalty_omission', (v.state_dur + v.LH_dur))
        v.target = random.randint(1, 5)
        print('v.target:{}'.format(v.target))

        if v.target == 1:
            hw.five_poke.poke_1.LED.on()
        elif v.target == 2:
            hw.five_poke.poke_2.LED.on()
        elif v.target == 3:
            hw.five_poke.poke_3.LED.on()
        elif v.target == 4:
            hw.five_poke.poke_4.LED.on()
        elif v.target == 5:
            hw.five_poke.poke_5.LED.on()

    elif event == 'poke_1' and v.target == 1 \
            or event == 'poke_2' and v.target == 2 \
            or event == 'poke_3' and v.target == 3 \
            or event == 'poke_4' and v.target == 4 \
            or event == 'poke_5' and v.target == 5:
        print('Correct_response')
        v.correct_num += 1
        print('Num of Correct response={}'.format(v.correct_num))
        play_feedback(is_correct=True)
        goto_state('reward')

    elif event == 'poke_1' and v.target != 1 \
            or event == 'poke_2' and v.target != 2 \
            or event == 'poke_3' and v.target != 3 \
            or event == 'poke_4' and v.target != 4 \
            or event == 'poke_5' and v.target != 5:
        print('Incorrect_response')
        v.incorrect_num += 1
        print('Num of Incorrect response={}'.format(v.incorrect_num))
        play_feedback(is_correct=False)
        goto_state('penalty')

    elif event == 'exit':
        hw.five_poke.poke_1.LED.off()
        hw.five_poke.poke_2.LED.off()
        hw.five_poke.poke_3.LED.off()
        hw.five_poke.poke_4.LED.off()
        hw.five_poke.poke_5.LED.off()
        disarm_timer('port_lights_timer')
        disarm_timer('penalty_omission')


def reward(event):
    if event == 'entry':
        hw.reward_port.LED.on()
        v.reward_given_this_state = False

    elif event == 'reward_in_timer':
        hw.reward_port.LED.off()

    elif event == 'poke_6':
        if v.reward_given_this_state:
            disarm_timer('reward_port_exit_timer')
            return
        deliver_reward()
        v.reward_given_this_state = True

    elif event == 'poke_6_out':
        set_timer('reward_port_exit_timer', v.reward_port_exit_debounce)

    elif event == 'reward_port_exit_timer':
        print('Reward_taken')
        goto_state('iti')

    elif event == 'exit':
        hw.reward_port.LED.off()
        disarm_timer('reward_in_timer')
        disarm_timer('reward_port_exit_timer')


def penalty(event):
    if event == 'entry':
        print('penalty')
        hw.house_light.off()
        hw.reward_port.LED.off()
        timed_goto_state('iti', v.penalty_dur)

    elif event == 'exit':
        hw.house_light.on()

    elif event == 'poke_1' \
            or event == 'poke_2' \
            or event == 'poke_3' \
            or event == 'poke_4' \
            or event == 'poke_5':
        print('attempts_dur_penalty')


def iti(event):
    if event == 'entry':
        print('iti_start_time')
        v.trials += 1
        print('Trials={}'.format(v.trials))
        if v.variable_ITI:
            rand_ITI_dur = random.choice([7, 9, 11, 13]) * second
            print('iti_dur:{}'.format(rand_ITI_dur))
            timed_goto_state('choice_task', rand_ITI_dur)
        else:
            timed_goto_state('choice_task', v.ITI_dur)

        if v.sound_distraction:
            sound_start_delay = random.randint(500, 3500) * ms
            set_timer('distraction_on_timer',  sound_start_delay)
            set_timer('distraction_off_timer', sound_start_delay + 1000)

    elif event == 'poke_1' \
            or event == 'poke_2' \
            or event == 'poke_3' \
            or event == 'poke_4' \
            or event == 'poke_5':
        print('Premature_response')
        v.premature_num += 1
        print('Num of Premature={}'.format(v.premature_num))
        goto_state('penalty')


# ---------------- State independent behavior ----------------
def all_states(event):
    if event == 'session_timer':
        print("Event Closing")
        print('Trials:{}, Correct:{}, Incorrect:{}, Omissions:{}, Premature:{}'.format(
            v.trials, v.correct_num, v.incorrect_num, v.omission_num, v.premature_num))
        print('Frequency[Poke1:{}, Poke2:{}, Poke3:{}, Poke4:{}, Poke5:{}]'.format(
            v.poke_1_frequency, v.poke_2_frequency, v.poke_3_frequency,
            v.poke_4_frequency, v.poke_5_frequency))
        stop_framework()

    elif event == 'port_lights_timer':
        hw.five_poke.poke_1.LED.off()
        hw.five_poke.poke_2.LED.off()
        hw.five_poke.poke_3.LED.off()
        hw.five_poke.poke_4.LED.off()
        hw.five_poke.poke_5.LED.off()

    elif event == 'reward_in_timer':
        hw.reward_port.LED.off()

    elif event == 'penalty_omission':
        print('omission')
        v.omission_num += 1
        print('Num of Omission={}'.format(v.omission_num))
        goto_state('penalty')

    elif event == 'poke_1':
        v.poke_1_frequency += 1
    elif event == 'poke_2':
        v.poke_2_frequency += 1
    elif event == 'poke_3':
        v.poke_3_frequency += 1
    elif event == 'poke_4':
        v.poke_4_frequency += 1
    elif event == 'poke_5':
        v.poke_5_frequency += 1

    elif event == 'feedback_off':
        hw.speaker.off()

    elif event == 'distraction_on_timer':
        hw.speaker.set_volume(35)
        hw.speaker.noise()

    elif event == 'distraction_off_timer':
        hw.speaker.set_volume(5)
        hw.speaker.off()
