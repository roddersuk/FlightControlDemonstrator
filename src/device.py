'''
Device module for the Bell 47 demonstrator rig
This manages the interface board attached to the Pi GPIO ports
'''
import threading
# import logging
import time
import warnings
from pygame.constants import JOYAXISMOTION, JOYBUTTONDOWN, JOYBUTTONUP, USEREVENT
import defs

gpio_present = True
try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from gpiozero import MCP3008, Button, DigitalOutputDevice
except:
    gpio_present = False

class InterfaceBoard(threading.Thread):
    """ Class for managing the analogue devices attached to the GPIO port
        This class handles the IO to the flight controls and buttons on the simulator rig
        and turns them into pygame events
    """
    def __init__(self, event_module):
        super().__init__()
        self.daemon = True
        self._event_module = event_module
        self._present = gpio_present
        if self._present:
            self._buttons = {
                defs.GPIO.BTN1.value  : {"id" : defs.BTN.BTN1.value,  "name" : "Btn1"}, 
                defs.GPIO.BTN2.value  : {"id" : defs.BTN.BTN2.value, "name" : "Btn2"}, 
                defs.GPIO.BTN3.value : {"id" : defs.BTN.BTN3.value,  "name" : "Btn3"}, 
                defs.GPIO.BTN4.value : {"id" : defs.BTN.BTN4.value,  "name" : "Btn4"},
                defs.GPIO.BTN5.value : {"id" : defs.BTN.BTN5.value,  "name" : "Btn5"},
                defs.GPIO.LEFT.value : {"id" : defs.BTN.LEFT.value,  "name" : "Left"},
                defs.GPIO.RIGHT.value : {"id" : defs.BTN.RIGHT.value, "name" : "Right"},
                defs.GPIO.UP.value : {"id" : defs.BTN.UP.value,    "name" : "Up"},
                defs.GPIO.DOWN.value : {"id" : defs.BTN.DOWN.value,  "name" : "Down"},
                defs.GPIO.SEAT.value : {"id" : defs.BTN.SEAT.value,  "name" : "Seat"},
                defs.GPIO.MOTOR_PRESENT.value : {"id" : defs.BTN.MOTOR_PRESENT.value, "name" : "Motor"}, 
            }
            self._run = True
            self._x = self._y = self._z = self._r = 0.0
            try:
                self._xpot = MCP3008(0)
                self._ypot = MCP3008(1)
                self._zpot = MCP3008(2)
                self._rpot = MCP3008(3)
                for pin, data in self._buttons.items():
                    if pin == defs.GPIO.SEAT.value or pin == defs.GPIO.MOTOR_PRESENT.value:
                        btn = Button(pin)
                    else:
                        btn = Button(pin, hold_repeat=True)
                        btn.when_held = self._button_held
                    if pin == defs.GPIO.MOTOR_PRESENT.value:
                        self._motor_present = btn.is_pressed
                    else:
                        data["NC"] = btn.is_pressed
                        btn.when_activated = self._button_pressed
                        btn.when_deactivated = self._button_released
                        if pin == defs.GPIO.SEAT.value:
                            self._seat_switch = btn
                    data["btn"] = btn
                if (self._motor_present):
                    self._motor = DigitalOutputDevice(defs.GPIO.MOTOR.value)
            except Exception as e:
                print(e)
                self._present = False
            
    def has_gpio(self) -> bool:
        """Return true if a GPIO port is present.
        """
        return self._present
    
    def is_seat_switch_pressed(self):
        """Return True if the seat switch is pressed.
        """
        return self._seat_switch.is_pressed
    
    def is_motor_present(self):
        """Return true if a motor is present.
        """
        return self._motor_present
    
    def set_scroll(self, scroll):
        if self._present:
            hold_time = 1.0
            if scroll:
                hold_time = 0.1
            self._buttons[24]["btn"].hold_time = hold_time
            self._buttons[25]["btn"].hold_time = hold_time

    def _button_pressed(self, button):
        """Callback function for when a button is pressed, generates a JOYBUTTON event
        
        button: the button that was pressed
        """
        if self._present:
            btn = self._buttons[button.pin.number]
            if btn["NC"]:
                self._event_module.post(self._event_module.Event(JOYBUTTONUP, {'button':btn["id"], 'name':btn["name"]}))
            else:
                self._event_module.post(self._event_module.Event(JOYBUTTONDOWN, {'button':btn["id"], 'name':btn["name"]}))
    
    def _button_released(self, button):
        """Callback function for when a button is released, generates a JOYBUTTON event
        
        button: the button that was released
        """
        if self._present:
            btn = self._buttons[button.pin.number]
            if btn["NC"]:
                self._event_module.post(self._event_module.Event(JOYBUTTONDOWN, {'button':btn["id"], 'name':btn["name"]}))
            else:
                self._event_module.post(self._event_module.Event(JOYBUTTONUP, {'button':btn["id"], 'name':btn["name"]}))

    def _button_held(self, button):
        self._button_pressed(button)
        
    def _get_button(self, button):
        btn = None
        for data in self._buttons.values():
            if data['id'] == button:
                btn = data['btn']
                break
        return btn
            
    def is_button_pressed(self, button):
#         logging.debug("In is_button_pressed, button=%d" % (button.value))
        btn = self._get_button(button.value)
#         pin = btn.pin.number
#         logging.debug("btn=%d name=%s" % (pin, self._buttons[pin]["name"]))
        is_pressed = False
        if self.has_gpio() and btn != None:
            is_pressed = btn.is_pressed
#         logging.debug("Is pressed %s" % (str(is_pressed)))
        return is_pressed
        
    def motor(self, on: bool):
        """Turn the motor on or off
        
        on: turn the motor on when True and off when False
        """
        if self._present and self._motor_present:
            if on:
                self._motor.on()
                self._event_module.post(self._event_module.Event(USEREVENT, {'motor':1}))
            else:
                self._motor.off()
                self._event_module.post(self._event_module.Event(USEREVENT, {'motor':0}))
    
    def calibrated_pot(self, pot_value, pot_min, pot_max):
        return (min(max(pot_value, pot_min), pot_max) - pot_min) / (pot_max - pot_min)
    
    def get_axis_value(self, axis):
        value = 0.0
        if axis == 0:
            raw = self._xpot.value
            if defs.XPOT_REVERSED:
                raw = 1.0 - raw
            value = self.calibrated_pot(1.0 - raw, defs.XPOT_MIN, defs.XPOT_MAX) * 2.0 - 1.0
        elif axis == 1:
            raw = self._ypot.value
            if defs.YPOT_REVERSED:
                raw = 1.0 - raw
            value = self.calibrated_pot(raw, defs.YPOT_MIN, defs.YPOT_MAX) * 2.0 - 1.0
        elif axis == 2:
            raw = self._zpot.value
            if defs.ZPOT_REVERSED:
                raw = 1.0 - raw
            value = self.calibrated_pot(raw, defs.ZPOT_MIN, defs.ZPOT_MAX)
        elif axis == 3:
            raw = self._rpot.value
            if defs.RPOT_REVERSED:
                raw = 1.0 - raw
            value = self.calibrated_pot(raw, defs.RPOT_MIN, defs.RPOT_MAX) * 2.0 - 1.0
        return value

    def run(self):
        """Daemon process for the thread to monitor potentiometer movements.
        
        Only movements greater than the specified TOLERANCE are used to generate JOYAXISMOTION events
        """
        if self._present: 
            while self._run:
                if abs(self._xpot.value - self._x) > defs.TOLERANCE:
                    self._x = self._xpot.value
                    x = self.get_axis_value(0)
                    self._event_module.post(self._event_module.Event(JOYAXISMOTION, {'joy':0, 'axis':0, 'value':x}))
                if abs(self._ypot.value - self._y) > defs.TOLERANCE:
                    self._y = self._ypot.value
                    y = self.get_axis_value(1)
                    self._event_module.post(self._event_module.Event(JOYAXISMOTION, {'joy':0, 'axis':1, 'value':y}))
                if abs(self._zpot.value - self._z) > defs.TOLERANCE:
                    self._z = self._zpot.value
                    z = self.get_axis_value(2)
                    self._event_module.post(self._event_module.Event(JOYAXISMOTION, {'joy':0, 'axis':2, 'value':z}))
                if abs(self._rpot.value - self._r) > defs.TOLERANCE:
                    self._r = self._rpot.value
                    r = self.get_axis_value(3)
                    self._event_module.post(self._event_module.Event(JOYAXISMOTION, {'joy':0,'axis':3, 'value':r}))
                time.sleep(0.1)
    
    def stop(self):
        """Stop the daemon process, terminating the thread.
        """
        self._run = False

import pygame
def write(screen: pygame.surface, 
          label: str, 
          value, 
          line: int, 
          bgd = [0, 0, 0], 
          fgd = [255, 255, 255]) -> pygame.rect:
    font = pygame.font.SysFont(None, 32, False)
    if type(value) is str:
        t = font.render(label + " " + value + "     ", True, fgd, bgd)
    elif type(value) is bool:
        t = font.render(label + " " + str(value) + "   ", True, fgd, bgd)
    else:
        t = font.render(label + " {0:.2f}".format(value) + "   ", True, fgd, bgd)
    return screen.blit(t, [0, line*24])

def test():
    pygame.init()   
    pygame.fastevent.init()         
    screen = pygame.display.set_mode((defs.SCREEN_WIDTH, defs.SCREEN_HEIGHT))
    fc = InterfaceBoard(pygame.fastevent)
    done = False
    if fc.has_gpio():
        fc.start()
    else:
        print('No gpio')
    axis = {'x' : 0.0, 'y' : 0.0, 'z' : 0.0, 'r' : 0.0}
    btn = {}
    for k,b in fc._buttons.items():
        btn[b['id']] = {'pressed' : False, 'key': k, 'name' : b['name']}
    motor_on = False
    while not done:
        for event in pygame.event.get():
            if (event.type == pygame.QUIT or
                (event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE)) :
                done = True
            elif event.type == JOYAXISMOTION:
                axis[event.axis] = event.value
                if event.axis == 0:
                    axis['x'] = event.value
                elif event.axis == 1:
                    axis['y'] = event.value
                elif event.axis == 2:
                    axis['z'] = event.value
                elif event.axis == 3:
                    axis['r'] = event.value
            elif event.type == JOYBUTTONDOWN:
                btn[event.button]['pressed'] = True
            elif event.type == JOYBUTTONUP:
                btn[event.button]['pressed'] = False
            elif event.type == USEREVENT:
                motor_on = event.motor
        
        write(screen, "Controls State", "", 1)
        write(screen, "X:", axis['x'], 2)
        write(screen, "Y:", axis['y'], 3)
        write(screen, "Z:", axis['z'], 4)
        write(screen, "R:", axis['r'], 5)
        write(screen, "Buttons", "", 7)
        line = 8
        for k,b in btn.items():
            write(screen, "", "%s Key(%d) : %s" % (b['name'], b['key'], b['pressed']), line)
            line = line + 1
        motor_text = "off"
        if motor_on:
            motor_text = "on"
        write(screen, "The motor is ", motor_text, line + 1)
            
        pygame.display.update()
    fc.stop()
    pygame.quit()
    
if __name__ == "__main__":
    test()

