'''
Simulator module for the Bell 47 demonstrator rig
'''
import pygame
#import logging
import time
import math

import defs
from defs import ProgramState, CRASH_LANDING_SPEED, HEANY_LANDING_SPEED, LANDING_PAD_OFFSET
from graphics import Altimeter, ArtificialHorizon, Helicopter, DirectionIndicator, LandingPad, HelicopterState, Landscape, write
from mmi import InputManager, get_font, INFO_FONT, render_text_list,\
    wrap_text

class FlightControls(object) :
    """Structure for the flight controls
    """
    def __init__(self):
        self.reset()
    def reset(self):
        self.collective = 0.0
        self.cyclic_pitch = 0.0
        self.cyclic_roll = 0.0
        self.anti_torque = 0.0
        self.startup = False
    def set(self, im: InputManager):
        self.collective = im.z
        self.cyclic_pitch = im.y
        self.cyclic_roll = im.x
        self.anti_torque = im.r
        self.startup = im._button_pressed

class SimProperties(object):
    """Structure for attributes of the simulator controlling what is displayed
    Really only useful when using a keyboard to drive the simulator
    """
    def __init__(self):
        self.reset()
    def reset(self):
        self.basic = False
        self.show_altimeter = True
        self.show_artificial_horizon = True
        self.show_direction = True
        self.show_grid = False
        self.show_pad = True
        self.show_text = False
        self.show_landscape = True
    def set(self, key):
        if key == pygame.K_s:
            self.basic = not self.basic
            self.show_altimeter = True
            self.show_artificial_horizon = not self.basic
            self.show_grid = False
            self.show_direction = not self.basic
            self.show_pad = True
            self.show_text = False
            self.show_landscape = True
        elif key == pygame.K_l:
            self.show_altimeter = not self.show_altimeter
        elif key == pygame.K_h:
            self.show_artificial_horizon = not self.show_artificial_horizon
        elif key == pygame.K_g:
            self.show_grid = not self.show_grid
        elif key == pygame.K_d:
            self.show_direction = not self.show_direction
        elif key == pygame.K_p:
            self.show_pad = not self.show_pad
        elif key == pygame.K_t:
            self.show_text = not self.show_text
        elif key == pygame.K_v:
            self.show_landscape = not self.show_landscape

def simulator(screen : pygame.surface, basic : bool = False) -> ProgramState:
    """Display a simple flight simulator based on a plan view of the helicopter.
    
    screen: the surface on which to display the simulator
    basic: when True use simpler algorithms to make the helicopter easier to fly 
    """
    im = InputManager.get_instance()
    im.reset()
    
    PITCH_INC = 3.0
    ROLL_INC = 3.0
    HEADING_INC = 2.0
    ALTITUDE_INC = .5
    SCALE_FACTOR = 0.8
    
    sim_properties = SimProperties()
    sim_properties.basic = basic
    flight_controls = FlightControls()

    # Set the flight limits
    window_width = screen.get_width()
    window_height = screen.get_height() - defs.DASH_HEIGHT
    if (sim_properties.basic):
        # Keep the landing pad in sight
        X_MAX = window_width / 2
        Y_MAX = window_height / 2
        sim_properties.show_artificial_horizon = False
        sim_properties.show_direction = False
    else :
        X_MAX = 2000.0
        Y_MAX = X_MAX * window_height / window_width
    
    pitch = 0.0
    roll = 0.0
    lift = 0.0
    yaw = 0.0
    forward_thrust = 0.0
    side_thrust = 0.0
    heading = 0.0
    helicopter_rotation = 0.0
    ground_rotation = 0.0
    altitude = 0.0
    prev_altitude = 0.0
    vertical_speed = 0.0
    pad_scale = 1.0
    x = 0.0
    y = 0.0
    
    pivot = [window_width / 2, window_height / 2]
    pad_offset = pygame.math.Vector2(0, 0)
    
    running = False
    landed = False
    
    # Initialize the display objects
    helicopter = Helicopter(pivot)
    landing_pad = LandingPad(pivot)
    direction_indicator = DirectionIndicator()
    altimeter = Altimeter()
    if sim_properties.show_artificial_horizon:
        artificial_horizon = ArtificialHorizon()
    landscape = Landscape(pivot,
        int((X_MAX + window_width / 2) / (1 - SCALE_FACTOR)),
        int((Y_MAX + window_height / 2)/ (1 - SCALE_FACTOR))
        )
        
    helicopter_state = _("On the ground")
     
    if __debug__:
        # Set up performance data
        count = 0
        timings = {
        'events': 0,
        'startup': 0,
        'calcs': 0,
        'text': 0,
        'landingpad': 0,
        'landscape': 0,
        'direction': 0,
        'helicopter': 0,
        'altimeter': 0,
        'artificialhorizon': 0,
        'update': 0
        }
    
    # Initialize screen areas
    main_rect = screen.get_rect()
    main_rect.height -= defs.DASH_HEIGHT
    dash_rect = screen.get_rect()
    dash_rect.top = main_rect.height
    dash_rect.height = defs.DASH_HEIGHT
    dash_text = _('Centre the cyclic stick, lower the collective and put your feet on the anti-torque pedals.\n'
                  'Then press the button to start the engine.\n'
                  'Try to take off, fly around and land back on the pad.')
    max_fps = 40
    if basic:
        dash_text_left = 10
    else:
        max_fps = 20
        dash_text_left = 250
        dash_text += _('\nThe direction arrow at the top of the screen indicates where to find the landing pad.')
    screen.fill(defs.DASH_BACKGROUND_COLOUR, dash_rect)
    screen.fill(defs.SIM_BACKGROUND_COLOUR, main_rect)
    dash_text_rect = pygame.Rect(dash_text_left, dash_rect.top + 30 , screen.get_width() - 500, defs.DASH_HEIGHT - 60)
    write_dash_text(screen, dash_text, get_font(INFO_FONT), defs.DASH_FOREGROUND_COLOUR, defs.DASH_BACKGROUND_COLOUR, dash_text_rect)
        
    # -------- Main Loop -----------
    done = False
    fps = 30
    clock = pygame.time.Clock()
    first_pass = True
    while not done:
        if __debug__:
            count += 1
        rects = []
                                   
        # Process events
        if __debug__:t = time.time()
        for event in im.get_events():
            got = im.get_input(event)
            if not im._seat_occupied:
                done = True
            if got:
                flight_controls.set(im)
            if im.char != None:
                sim_properties.set(im.char)
        if __debug__:timings['events'] += time.time() - t
        # print("%3.3f %3.3f %3.3f %3.3f %5s %5s" % (im.x, im.y, im.z, im.r, im._button_pressed, im._seat_occupied), end='\r')
        
        # Start up the helicopter
        if __debug__:t = time.time()
        if (flight_controls.startup) :
            if not running :
                running = True
                heading = 0.0
                x = 0.0
                y = 0.0
                helicopter.set_state(HelicopterState.WINDING_UP)
                helicopter_state = _("Starting up")
        if __debug__:timings['startup'] += time.time() - t
        
        # Calculate the flight parameters
        if __debug__:t = time.time()
        st = helicopter.get_state()
        if st == HelicopterState.RUNNING:
            # Don't allow the helicopter to move until its running
            helicopter_state = _("Running")
            if altitude > 0.0 :
                if basic:
                    pitch = flight_controls.cyclic_pitch * defs.PITCH_MAX
                    roll = flight_controls.cyclic_roll * defs.ROLL_MAX
                else:
                    pitch = min(pitch + flight_controls.cyclic_pitch * PITCH_INC, defs.PITCH_MAX)
                    roll = min(roll + flight_controls.cyclic_roll * ROLL_INC, defs.ROLL_MAX)
            else :
                pitch = roll = 0.0
            thrust = flight_controls.collective * defs.THRUST_FACTOR
            if (flight_controls.collective > 0.01) :
                thrust2 = thrust
            else : # windmilling
                thrust2 = defs.WINDMILL_THRUST
            lift = thrust2 * abs(math.cos(math.radians(pitch))) * abs(math.cos(math.radians(roll)))
            forward_thrust = thrust2 * math.sin(math.radians(pitch))
            side_thrust = thrust2 * math.sin(math.radians(roll))
            if (not basic and abs(forward_thrust) > 0.1 and abs(side_thrust) > 0.01) :
                heading_change = math.degrees(math.atan2(side_thrust, forward_thrust)) / defs.BANKING_FACTOR
            else :
                heading_change = 0.0
            altitude = max(0.0, min(defs.ALTITUDE_MAX, altitude + (ALTITUDE_INC * (lift - defs.TAKEOFF_LIFT))))
            vertical_speed = (prev_altitude - altitude) * fps
            pad_scale = 1.0 - (altitude / defs.ALTITUDE_MAX) * SCALE_FACTOR
            if (altitude > 1.0):
                # We're off the ground
                helicopter_state = _("Flying")
                heading = (heading + HEADING_INC * flight_controls.anti_torque) % 360 + heading_change
                xmax = X_MAX / pad_scale
                ymax = Y_MAX / pad_scale
                x = max(-xmax, min(xmax, x - (forward_thrust * math.sin(math.radians(heading)) 
                                 + side_thrust * math.sin(math.radians(heading + 90.0)))))
                y = max(-ymax, min(ymax, y + (forward_thrust * math.cos(math.radians(heading)) 
                                 + side_thrust * math.cos(math.radians(heading + 90.0)))))
                pad_offset.x = x * pad_scale
                pad_offset.y = y * pad_scale
            elif (altitude < 1.0 and prev_altitude > 1.0) :
                # We've landed
                landed = True
                helicopter_state = _("Landed OK")
                running = False
                helicopter.set_state(HelicopterState.WINDING_DOWN)
                flight_controls.reset()
                pitch = roll = lift = thrust = 0.0
                if vertical_speed > CRASH_LANDING_SPEED:
                    msg = _("Oh dear, I'm afraid you crash landed!")
                elif (pad_offset.length() > LANDING_PAD_OFFSET) :
                    helicopter_state = _("Missed the landing pad")
                    if vertical_speed < HEANY_LANDING_SPEED:
                        msg = _('You landed OK but you missed the landing pad')
                    else:
                        msg = _("That was a heavy landing,\nand you missed the landing pad!")
                else:
                    if vertical_speed < HEANY_LANDING_SPEED:
                        msg = _('Well done!\nYou landed safely back on the landing pad')
                    else:
                        msg = _("You landed back on the pad\nbut it was quite a heavy landing")
                write_dash_text(screen, msg, get_font(INFO_FONT), defs.DASH_FOREGROUND_COLOUR, defs.DASH_BACKGROUND_COLOUR, dash_text_rect)
                rects.append(dash_text_rect)
            helicopter_rotation = heading
            ground_rotation = 0.0
# TODO            if not basic:
#                 helicopter_rotation = 0.0
#                 ground_rotation = heading
        if __debug__:timings['calcs'] += time.time() - t

        # Display debug text
        if __debug__:
            t = time.time()
            if sim_properties.show_text:
                display_text = [
                    ["Cyclic (pitch):", flight_controls.cyclic_pitch],
                    ["Cyclic (roll):", flight_controls.cyclic_roll],
                    ["Collective:", flight_controls.collective],
                    ["Anti-Torque:", flight_controls.anti_torque],
                    ["Pitch:", pitch],
                    ["Roll:", roll],
                    ["Forward Thrust:", forward_thrust],
                    ["Sideways Thrust:", side_thrust],
                    ["Lift:", lift],
                    ["Yaw:", yaw],
                    ["Heading:", heading],
                    ["Altitude:", altitude],
                    ["Pad x:", pad_offset.x],
                    ["Pad y:", pad_offset.y],
                    ["HelicopterState:", helicopter_state],
                    ["Vertical Speed:", vertical_speed],
                    ["fps", fps]
                    ]
            else:
                display_text = [
                    ["fps", fps]
                    ]
            
            for i, item in enumerate(display_text):
                text_rect = write(screen, item[0],  item[1], i, bgd=defs.SIM_BACKGROUND_COLOUR)
                if i == 0:
                    total_rect = text_rect
                else :
                    total_rect.union_ip(text_rect)
            rects.append(total_rect)
            timings['text'] += time.time() - t
            
        # Draw objects clipped to the main area
        if __debug__:t = time.time()
        screen.set_clip(main_rect)
        
        # Clear static objects before drawing the pad which could move under them
        if sim_properties.show_direction:
            direction_indicator.clear(screen, defs.SIM_BACKGROUND_COLOUR, pad_offset)
        helicopter.clear(screen, defs.SIM_BACKGROUND_COLOUR, helicopter_rotation)
        
        if sim_properties.show_pad :
            landing_pad.clear(screen, defs.SIM_BACKGROUND_COLOUR, ground_rotation)
            rects += landing_pad.blit(screen, pad_scale, pad_offset, ground_rotation)
        if __debug__:timings['landingpad'] += time.time() - t
        
        if __debug__:t = time.time()
        if sim_properties.show_landscape:
            landscape.clear(screen, defs.SIM_BACKGROUND_COLOUR, ground_rotation)
            rects += landscape.blit(screen, pad_scale, pad_offset, ground_rotation)
        if __debug__:timings['landscape'] += time.time() - t
        
        if __debug__:t = time.time()
        if sim_properties.show_direction :
            rects.append(direction_indicator.blit(screen, pad_offset, [screen.get_width() / 2, 30]))
        if __debug__:timings['direction'] += time.time() - t
        
        if __debug__:t = time.time()
        rects += helicopter.blit(screen, helicopter_rotation, altitude)
        if __debug__:timings['helicopter'] += time.time() - t
        
        if __debug__:t = time.time()
        screen.set_clip()
        if sim_properties.show_altimeter :
            rects += altimeter.blit(screen, altitude, [-10, -10])
        if __debug__:timings['altimeter'] += time.time() - t
        
        if __debug__:t = time.time()
        if sim_properties.show_artificial_horizon :
            rects.append(artificial_horizon.blit(screen, pitch, roll, [10, -10]))
        if __debug__:timings['artificialhorizon'] += time.time() - t
     
        # Go ahead and update the screen with what we've drawn.
        if __debug__:t = time.time()
        if first_pass:
            pygame.display.update()
        else:
            pygame.display.update(rects)
        if __debug__: timings['update'] += time.time() - t
     
        prev_altitude = altitude
        
        clock.tick(max_fps)
        fps = clock.get_fps()
        first_pass = False
        
        # If we've landed, wait for a short period before returning to the menu
        st = helicopter.get_state()
        if landed and st == HelicopterState.STOPPED:
            done = True
            time.sleep(5)

    if __debug__:
        print("Performance Stats")
        total = 0
        for key in timings:
            total += timings[key]
        for name, value in timings.items() :
            print("%s:\t%f ms \t%f%%" % (name, value / count * 1000, value/total*100))
        print("average %f ms per frame" % (total / count * 1000)) 
        print("fps: %f" % fps)
        
    return ProgramState.MENU

def write_dash_text(screen, text, font, fgd, bgd, rect):
    """Write wrapped text into the dashboard.
    """
    screen.fill(defs.DASH_BACKGROUND_COLOUR, rect)
    screen.blit(render_text_list(wrap_text(text, font, rect.w), font, fgd, bgd), rect)
    
