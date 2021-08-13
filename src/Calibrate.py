#!/usr/bin/python
'''
Utility to get calibration results for the Bell Simulator flight controls
'''
__author__ = 'Rod Thomas <rod.thomas@talktalk.net>'
__date__ = '19 March 2019'
__version__ = '0.1.0'

import pygame
import defs
# from defs import event_module, reset_calibration, XPOT_MIN, XPOT_MAX, YPOT_MIN, YPOT_MAX
from device import InterfaceBoard

def main():
    limits = [
            ["Cyclic Lat", 1.0, 0.0],
            ["Cylic Long", 1.0, 0.0],
            ["Collective", 1.0, 0.0],
            ["Anti-Torque", 1.0, 0.0]
        ]
    pygame.init()
    pygame.fastevent.init()
    defs.reset_calibration()
    fc = InterfaceBoard(defs.event_module)
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

if __name__ == "__main__":
    main()

#End  