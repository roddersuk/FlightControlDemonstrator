'''
General definitions for the Bell 47 demonstrator rig
'''
import configparser
import pygame
import json
from enum import Enum

# Need to use fastevents to be able to post events from the device thread
use_fast_events = True
if use_fast_events:
    event_module = pygame.fastevent
else:
    event_module = pygame.event
    
class ProgramState(Enum) :
    WELCOME = 0
    INTRODUCTION = 1
    MENU = 2
    DESCRIPTIONS = 3
    CONTROLS = 4
    BASIC_SIM = 5
    ADVANCED_SIM = 6
    ABOUT = 7
    
class BTN(Enum):
    BTN1 = 0
    BTN2 = 1
    BTN3 = 2
    BTN4 = 3
    BTN5 = 4
    LEFT = 5
    RIGHT = 6
    UP = 7
    DOWN = 8
    SEAT = 9
    MOTOR_PRESENT  = 10
    
class GPIO(Enum):
    BTN1 = 5
    BTN2 = 6
    BTN3 = 13
    BTN4 = 16
    BTN5 = 20
    LEFT = 18
    RIGHT = 23
    UP = 25
    DOWN = 24
    SEAT = 26
    MOTOR_PRESENT = 12
    MOTOR = 4
    
config = configparser.ConfigParser()
config.read("FCD.ini")

# main
SCREEN_WIDTH = config['main'].getint('screen_width', fallback = 1280)
SCREEN_HEIGHT = config['main'].getint('screen_height', fallback = 1024)
FLAG_HIGHLIGHT_WIDTH = config['main'].getint('flag_highlight_width', fallback = 4)
SCROLL_INCREMENT = config['main'].getint('scroll_increment', fallback = 10)

#colour
WHITE = '[255, 255, 255]'
BLACK = '[0, 0, 0]'
DARK_GREY = '[64, 64, 64]'
GOLD = '[170, 132, 57]'
LIGHT_GOLD = '[212, 177, 106]'
VERY_LIGHT_GOLD = '[255, 227, 170]'
VERY_LIGHT_BLUE = '[120, 135, 171]'
LIGHT_BLUE = '[79, 98, 142]'
MID_BLUE = '[46, 65, 114]'
DARK_BLUE = '[22, 41, 85]'
GREEN = '[10, 170, 10]'
LIGHT_RED = '[255, 77, 77]'

WELCOME_TEXT_COLOUR = json.loads(config['colours'].get('welcome_text', fallback = WHITE))
ABOUT_FOREGROUND_COLOUR = json.loads(config['colours'].get('about_text', fallback = GOLD))
ABOUT_BACKGROUND_COLOUR = json.loads(config['colours'].get('about_background', fallback = DARK_BLUE))
MENU_BACKGROUND_COLOUR = json.loads(config['colours'].get('menu_background', fallback = LIGHT_BLUE))
MENU_FOREGROUND_COLOUR = json.loads(config['colours'].get('menu_foreground', fallback = GOLD))
MENU_SELECT_COLOUR = json.loads(config['colours'].get('menu_select', fallback = VERY_LIGHT_GOLD))
DESC_FOREGROUND_COLOUR = json.loads(config['colours'].get('desc_text', fallback = DARK_GREY))
DESC_BACKGROUND_COLOUR = json.loads(config['colours'].get('desc_background', fallback = VERY_LIGHT_GOLD))
DASH_FOREGROUND_COLOUR = json.loads(config['colours'].get('dash_text', fallback = WHITE))
DASH_BACKGROUND_COLOUR = json.loads(config['colours'].get('dash_background', fallback = DARK_GREY))
CONTROL_FOREGROUND_COLOUR = json.loads(config['colours'].get('control_text', fallback = BLACK))
CONTROL_BACKGROUND_COLOUR = json.loads(config['colours'].get('control_background', fallback = '[123, 181, 218]'))
SIM_BACKGROUND_COLOUR = json.loads(config['colours'].get('sim_background', fallback = GREEN))
HIGHLIGHT_COLOUR = json.loads(config['colours'].get('highlight', fallback = VERY_LIGHT_GOLD))
CALIBRATE_BACKGROUND_COLOUR = json.loads(config['colours'].get('calibrate_background', fallback = LIGHT_RED))
CALIBRATE_FOREGROUND_COLOUR = json.loads(config['colours'].get('calibrate_foreground', fallback = BLACK))

# fonts
FONT_WELCOME = config['fonts'].get('welcome', fallback = 'Arial,64,False,False').split(',')
FONT_WELCOME_zh = config['fonts'].get('welcome_zh', fallback = 'LongCang,128,False,False').split(',')
FONT_WELCOME_ru = config['fonts'].get('welcome_ru', fallback = 'Caveat,100,False,False').split(',')
FONT_MENU = config['fonts'].get('menu', fallback = 'None,40,False,False').split(',')
FONT_DESC = config['fonts'].get('desc', fallback = 'timesnewroman,48,False,False').split(',')
FONT_INFO = config['fonts'].get('info', fallback = 'timesnewroman,32,False,False').split(',')
FONT_TEXT = config['fonts'].get('text', fallback = 'None,32,False,False').split(',')
FONT_SMALL = config['fonts'].get('small', fallback = 'None,16,False,False').split(',')
FONT_METER = config['fonts'].get('meter', fallback = 'Arial,16,True,False').split(',')
FONT_ALTIMETER = config['fonts'].get('altimeter', fallback = 'Arial,28,True,False').split(',')
FONT_MENU_ru = config['fonts'].get('menu_ru', fallback = 'NotoSans,32,False,False').split(',')
FONT_DESC_ru = config['fonts'].get('desc_ru', fallback = 'NotoSerif,40,False,False').split(',')
FONT_INFO_ru = config['fonts'].get('info_ru', fallback = 'NotoSerif,32,False,False').split(',')
FONT_TEXT_ru = config['fonts'].get('text_ru', fallback = 'NotoSans,28,False,False').split(',')
FONT_METER_ru = config['fonts'].get('meter_ru', fallback = 'NotoSans,12,True,False').split(',')
FONT_MENU_zh = config['fonts'].get('menu_zh', fallback = 'NotoSansSC,24,False,False').split(',')
FONT_DESC_zh = config['fonts'].get('desc_zh', fallback = 'NotoSerifSC,32,False,False').split(',')
FONT_INFO_zh = config['fonts'].get('info_zh', fallback = 'NotoSerifSC,28,False,False').split(',')
FONT_TEXT_zh = config['fonts'].get('text_zh', fallback = 'NotoSansSC,28,False,False').split(',')
FONT_METER_zh = config['fonts'].get('meter_zh', fallback = 'NotoSansSC,12,True,False').split(',')

# control
SEAT_TIMEOUT = config['control'].getfloat('seat_timeout', fallback = 60.0)
INACTIVE_TIMEOUT = config['control'].getfloat('inactive_timeout', fallback = 300.0)

# device
TOLERANCE = config['device'].getfloat('tolerance', fallback = 0.005)
BTN_SELECT = config['device'].getint('select_button', fallback = BTN.BTN3.value)
BTN_RESET = config['device'].getint('reset_button', fallback = BTN.BTN5.value)

# calibration
XPOT_MIN = config['calibration'].getfloat('cyclic_lat_min', fallback = 0.0)
XPOT_MAX = config['calibration'].getfloat('cyclic_lat_max', fallback = 1.0)
XPOT_REVERSED = config['calibration'].getboolean('cyclic_lat_reversed', fallback = False)
YPOT_MIN = config['calibration'].getfloat('cyclic_long_min', fallback = 0.0)
YPOT_MAX = config['calibration'].getfloat('cyclic_long_max', fallback = 1.0)
YPOT_REVERSED = config['calibration'].getboolean('cyclic_long_reversed', fallback = False)
ZPOT_MIN = config['calibration'].getfloat('collective_min', fallback = 0.0)
ZPOT_MAX = config['calibration'].getfloat('collective_max', fallback = 1.0)
ZPOT_REVERSED = config['calibration'].getboolean('collective_reversed', fallback = False)
RPOT_MIN = config['calibration'].getfloat('anti_torque_min', fallback = 0.0)
RPOT_MAX = config['calibration'].getfloat('anti_torque_max', fallback = 1.0)
RPOT_REVERSED = config['calibration'].getboolean('anti_torque_reversed', fallback = False)

# blade
MAX_COLLECTIVE = config['blade'].getfloat('max_collective_angle', fallback = 20.0)
MAX_CYCLIC = config['blade'].getfloat('max_cyclic_angle', fallback = 20.0)
MAX_TAIL = config['blade'].getfloat('min_tail_angle', fallback = 10.0)
MIN_TAIL = config['blade'].getfloat('max_tail_angle', fallback = 30.0)

# simulator
ALTITUDE_MAX = config['simulator'].getfloat('altitude_limit', fallback = 4000.0)
PITCH_MAX = config['simulator'].getfloat('pitch_limit', fallback = 30.0)
ROLL_MAX = config['simulator'].getfloat('roll_limit', fallback = 30.0)
THRUST_FACTOR = config['simulator'].getfloat('thrust_factor', fallback = 100.0)
TAKEOFF_LIFT = config['simulator'].getfloat('takeoff_lift', fallback = 20.0)
WINDMILL_THRUST = config['simulator'].getfloat('windmill_thrust', fallback = 5.0)
BANKING_FACTOR = config['simulator'].getfloat('banking_factor', fallback = 1000.0)
DASH_HEIGHT = config['simulator'].getint('dashboard_height', fallback = 240)
HELI_ROTATION_PERCENT = config['simulator'].getfloat('helicopter_rotation_percent', fallback = 5.0)
CRASH_LANDING_SPEED = config['main'].getfloat('crash_landing_speed', fallback = 250.0)
HEANY_LANDING_SPEED = config['main'].getfloat('heavy_landing_speed', fallback = 100.0)
LANDING_PAD_OFFSET = config['main'].getint('landing_pad_offset', fallback = 100)

def reset_calibration():
    global XPOT_MIN, YPOT_MIN, ZPOT_MIN, RPOT_MIN, XPOT_MAX, YPOT_MAX, ZPOT_MAX, RPOT_MAX
    XPOT_MIN = YPOT_MIN = ZPOT_MIN = RPOT_MIN = 0.0
    XPOT_MAX = YPOT_MAX = ZPOT_MAX = RPOT_MAX = 1.0
    
class QuitException(Exception):
    pass

class ResetException(Exception):
    pass

# Define some colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
