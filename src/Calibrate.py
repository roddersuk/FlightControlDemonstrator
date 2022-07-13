#!/usr/bin/python
'''
Utility to get calibration results for the Bell Simulator flight controls
'''
from random import randint
__author__ = 'Rod Thomas <rod.thomas@talktalk.net>'
__date__ = '19 March 2019'
__version__ = '0.1.0'

import pygame
import defs
from mmi import InputManager
import graphics
import device

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
        
def calibrate(screen : pygame.surface) -> defs.ProgramState:
    im = InputManager.get_instance( )
    im.reset()
    # Draw background
    bgd = defs.CALIBRATE_BACKGROUND_COLOUR
    fgd = defs.CALIBRATE_FOREGROUND_COLOUR
    rect = screen.get_rect() #.inflate(-40, -40)
    graphics.round_rect(screen, rect, 0, bgd)
    device.write(screen, "Potentiometer calibration", "", 0, bgd, fgd)
    device.write(screen, "=========================", "", 1, bgd, fgd)
    
    has_gpio = im._fc.has_gpio()
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
    results = False
    while not finished :
        if not has_gpio:
            device.write(screen, "No interface board detected - calibration not has_gpio", "", 1, bgd, fgd)
            device.write(screen, "Coordinates will be randomly generated", "", 2, bgd, fgd)
        for event in pygame.event.get():
            if (event.type == pygame.QUIT or
                (event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE)) :
                finished = True
            if (start or event.type == pygame.KEYDOWN or event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP):
                if start == False and results == False:
                    axis = index // 2
                    ind = index % 2
                    if not has_gpio:
                        val = randint(0, 10)
                        value = float(val + (90 * ind)) / 100.0
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
                elif results == False:
                    results = True
                    line += 2
                    for limit in limits:
                        if limit[1] > limit[2]:
                            limit[3] = True
                        device.write(screen, "%s_Min %f" % (limit[0], limit[1]), "", line, bgd, fgd)
                        line += 1
                        device.write(screen, "%s_Max %f" % (limit[0], limit[2]), "", line, bgd, fgd)
                        line += 1
                        print("%s_Min %f" % (limit[0], limit[1]))
                        print("%s_Max %f" % (limit[0], limit[2]))
                        if limit[3]:
                            device.write(screen, "%s_reversed %f" % (limit[0], limit[3]), "", line, bgd, fgd)
                            line += 1
                            print("%s_reversed %f" % (limit[0], limit[3]))
                else:
                    finished = True 
            elif event.type == pygame.JOYAXISMOTION:
                axis = index // 2
                if event.axis == axis: # Only interested in one axis at a time
                    value = event.value
        pygame.display.update()
              
if __name__ == "__main__":
    main()

#End  