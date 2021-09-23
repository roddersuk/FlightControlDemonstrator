#!/usr/bin/python
'''
Utility to get calibration results for the Bell Simulator flight controls
'''
__author__ = 'Rod Thomas <rod.thomas@talktalk.net>'
__date__ = '19 March 2019'
__version__ = '0.1.0'

import pygame
import defs
#import mmi
from mmi import InputManager
import graphics
# from defs import event_module, reset_calibration, XPOT_MIN, XPOT_MAX, YPOT_MIN, YPOT_MAX
import device
#from mmi import InputManager, get_font, INFO_FONT

def main():
    pygame.init()
    pygame.fastevent.init()
    defs.reset_calibration()
    screen = pygame.display.set_mode((defs.SCREEN_WIDTH, defs.SCREEN_HEIGHT))
    try: 
        calibrate(screen)
    except defs.QuitException as qe:
        import traceback
        tbe = traceback.extract_tb(qe.__traceback__)
        tb = [x[2] for x in tbe]
        print("User quit at %s" % ("->".join(tb)))
    finally:
        pygame.quit()
        
def oldmain():
    limits = [
            ["Cyclic Lat", 1.0, 0.0],
            ["Cylic Long", 1.0, 0.0],
            ["Collective", 1.0, 0.0],
            ["Anti-Torque", 1.0, 0.0]
        ]
    pygame.init()
    pygame.fastevent.init()
    defs.reset_calibration()
    fc = device.InterfaceBoard(defs.event_module)
    if fc.has_gpio():
        fc.start()
        print("Move all flight controls to their limits and then press a button.")
        done = False
        while done == False:
            events = defs.event_module.get()
            for event in events:    
                if event.type is pygame.JOYAXISMOTION:
                    if event.value > limits[event.axis][2]:
                        if event.axis == 2:
                            limits[event.axis][2] = event.value
                        else:
                            limits[event.axis][2] = (event.value + 1.0) / 2.0
                    elif event.value < limits[event.axis][1]:
                        if event.axis == 2:
                            limits[event.axis][1] = event.value
                        else:
                            limits[event.axis][1] = (event.value + 1.0) / 2.0
                elif (event.type is pygame.JOYBUTTONDOWN or event.type is pygame.JOYBUTTONUP):
                    done = True
    else:
        limits[0][1] = defs.XPOT_MIN
        limits[0][2] = defs.XPOT_MAX
        limits[1][1] = defs.YPOT_MIN
        limits[1][2] = defs.YPOT_MAX
        limits[2][1] = defs.ZPOT_MIN
        limits[2][2] = defs.ZPOT_MAX
        limits[3][1] = defs.RPOT_MIN
        limits[3][2] = defs.RPOT_MAX
        print("No interface board")
    print("Calibration Values:")
    for limit in limits:
        print("\t%s\tMin %f\tMax %f" % (limit[0], limit[1], limit[2]))

def calibrate(screen : pygame.surface) -> defs.ProgramState:
    im = InputManager.get_instance( )
    im.reset()
    # Draw background
    bgd = defs.CALIBRATE_BACKGROUND_COLOUR
    fgd = defs.CALIBRATE_FOREGROUND_COLOUR
    rect = screen.get_rect() #.inflate(-40, -40)
    graphics.round_rect(screen, rect, 0, bgd)
    device.write(screen, "Joystick calibration", "", 0, bgd, fgd)
    device.write(screen, "====================", "", 1, bgd, fgd)
    
    possible = im._fc.has_gpio()
    limits = [
        ["Cyclic Lat", 1.0, 0.0, False],
        ["Cylic Long", 1.0, 0.0, False],
        ["Collective", 1.0, 0.0, False],
        ["Anti-Torque", 1.0, 0.0, False]
    ]
    start = True
    index = 0
    txt = "as far as it will go and press the button"
    value = 0.5
    finished = False
    while not finished :
        if not possible:
            device.write(screen, "No interface board detected - calibration not possible", "", 1, bgd, fgd)
        events = defs.event_module.get()
        for event in events:  
            if possible:  
                if (start or event.type == pygame.KEYDOWN or event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP):
                    if start == False:
                        axis = index // 2
                        ind = index % 2
                        limits[axis][ind+1] = value
                        index += 1
                    else:
                        start = False
                    line = (index + 1) * 2 + 2
                    if index == 0:
                        device.write(screen, "Move the cyclic stick left", txt, line, bgd, fgd)
                    elif index == 1:
                        device.write(screen, "Move the cyclic stick right", txt, line, bgd, fgd)
                    elif index == 2:
                        device.write(screen, "Move the cyclic stick forward", txt, line, bgd, fgd)
                    elif index == 3:
                        device.write(screen, "Move the cyclic stick aft", txt, line, bgd, fgd)
                    elif index == 4:
                        device.write(screen, "Move the collective down", txt, line, bgd, fgd)
                    elif index == 5:
                        device.write(screen, "Move the collective up", txt, line, bgd, fgd)
                    elif index == 6:
                        device.write(screen, "Move the rudder pedals left", txt, line, bgd, fgd)
                    elif index == 7:
                        device.write(screen, "Move the rudder pedals right", txt, line, bgd, fgd)
                    else:
                        finished = True
                elif event.type is pygame.JOYAXISMOTION:
                    axis = index // 2
                    if event.axis == axis: # Only interested in one axis at a time
                        value = event.value
            else:   
                finished = (event.type == pygame.KEYDOWN or event.type == pygame.KEYUP)       
        pygame.display.update()
    for limit in limits:
        if limit[1] > limit[2]:
            limit[3] = True
        print("%s_Min %f" % (limit[0], limit[1]))
        print("%s_Max %f" % (limit[0], limit[2]))
        if limit[3]:
            print("%s_reversed %f" % (limit[0], limit[3]))
    return defs.ProgramState.MENU
              
if __name__ == "__main__":
    main()

#End  