'''
Man-Machine Interface module for the Bell 47 demonstrator rig
'''
import pygame
import logging
import time

import defs
from defs import event_module, QuitException, ResetException
import i18n
from graphics import Arrows
from device import InterfaceBoard
from pygame import event

WELCOME_FONT = 'welcome'
MENU_FONT = 'menu'
DESC_FONT = 'desc'
INFO_FONT = 'info'
TEXT_FONT = 'text'
SMALL_FONT = 'small'
METER_FONT = "meter"
ALTIMETER_FONT = "altimeter"

font_defs = {
    WELCOME_FONT:   defs.FONT_WELCOME,
    MENU_FONT:      defs.FONT_MENU,
    DESC_FONT:      defs.FONT_DESC,
    INFO_FONT:      defs.FONT_INFO,
    TEXT_FONT:      defs.FONT_TEXT,
    SMALL_FONT:     defs.FONT_SMALL,
    METER_FONT:     defs.FONT_METER,
    ALTIMETER_FONT: defs.FONT_ALTIMETER
    }

# font_defs = {
#     WELCOME_FONT:   ("dancingscript", 128, True, False),
#     MENU_FONT:      (None, 40, False, False),
#     DESC_FONT:      ("timesnewroman", 48, False, False),
#     INFO_FONT:      ("timesnewroman", 32, False, False),
#     TEXT_FONT:      (None, 32, False, False),
#     SMALL_FONT:     (None, 16, False, False),
#     METER_FONT:     ("Arial", 16, True, False),
#     ALTIMETER_FONT: ("Arial", 28, True, False)
#     }

WELCOME_IMAGE = 'welcome'
LOGO_IMAGE = 'logo'
CYCLIC_IMAGE = 'cyclic'
LEFT_IMAGE = 'left'
RIGHT_IMAGE = 'right'
UP_IMAGE = 'up'
DOWN_IMAGE = 'down'

fonts = {}
images = {}

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")

def get_font(name: str) -> pygame.font:
    """Get one of the predefined fonts by name, loading it on first use.
    
    name (str): the font name
    """
    if name not in fonts:
        if name not in font_defs:
            name = TEXT_FONT
        font_def = font_defs[name]
#        logging.debug("font %s is %s with size %s bold %s italic %s", name, font_def[0], font_def[1], font_def[2], font_def[3])
#         fonts[name] = pygame.font.SysFont(font_def[0], font_def[1], font_def[2], font_def[3])
        fonts[name] = pygame.font.SysFont(font_def[0], int(font_def[1]), str2bool(font_def[2]), str2bool(font_def[3]))
    return fonts[name]

def get_image(name: str, filepath: str = None, alpha: bool = True): 
    """Get one of the predefined images by name, loading it on first use.
    
    name: the image name
    filepath: the image file path
    alpha: when True image contains transparency
    """
    if name not in images:
        if alpha:
            images[name] = pygame.image.load(filepath).convert_alpha()
        else:
            images[name] = pygame.image.load(filepath).convert()
    return images[name]

class InputManager(object) :
    """Manage inputs supporting input from both keyboard and analogue controls
    """
    __instance = None
    @staticmethod
    def get_instance():
        """Get the singleton input manager object
        """
        if InputManager.__instance == None:
            InputManager.__instance = InputManager(event_module)
        return InputManager.__instance
    
    def __init__(self, event_module: pygame.event):
#         InputManager.__instance = self
        self._fc = InterfaceBoard(event_module)
        if self._fc.has_gpio():
            self._fc.start()
        self.reset()
        self._last_x = True
        self._last_y = True
        self.char = None
        self.r_inc = 0.05
        self.x_inc = 0.05
        self.y_inc = 0.05
        self.z_inc = 0.05
        self._seat_timer = None
        self._seat_timeout = defs.SEAT_TIMEOUT
        self._inactive_timer = None
        self._inactive_timeout = defs.INACTIVE_TIMEOUT
        
    def reset(self) :
        self.x = self.y = self.z = self.r = 0.0
        self._button_pressed = False
        if self._fc.has_gpio():
            self.x = self._fc.get_axis_value(0)
            self.y = self._fc.get_axis_value(1)
            self.z = self._fc.get_axis_value(2)
            self.r = self._fc.get_axis_value(3)
            self._seat_occupied = self._fc.is_seat_switch_pressed()
            self._has_motor = self._fc.is_motor_present()
        else:
            self._seat_occupied = True
            self._has_motor = False
        self.set_scroll(False)
    
    def reset_inactive_timer(self):
        self._inactive_timer = time.time()
            
    def has_motor(self) -> bool:
        return self._has_motor
    
    def motor(self, on: bool):
        self._fc.motor(on)
    
    def get_events(self) -> event:
        events = event_module.get()
        for event in events:    
            if (event.type == pygame.QUIT or (event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE) or
                (event.type == pygame.JOYBUTTONDOWN and event.button == defs.BTN_RESET and
                self._fc.is_button_pressed(defs.BTN.BTN2))):
                raise QuitException()
            if ((event.type == pygame.JOYBUTTONDOWN and event.button == defs.BTN_RESET)
                or (event.type == pygame.KEYDOWN and event.key == pygame.K_HOME)) :
                raise ResetException()
        if self._inactive_timer != None and (time.time() - self._inactive_timer) > self._inactive_timeout:
            self._inactive_timer = None
            raise ResetException()
        elif self._seat_timer != None and time.time() - self._seat_timer >= self._seat_timeout:
            self._seat_timer = None
            raise ResetException()
        return events

    def get_any_key(self):
        """ Wait for a key or button press
        """
        done = False
        while not done:   
            for event in self.get_events():
                if event.type is pygame.KEYDOWN or event.type is pygame.JOYBUTTONDOWN:
                    done = True
    
    def get_input(self, event) -> bool:
        """Process events to get the control positions and button states.
        
        event (event): the event to process
        return: True if button pressed or x-y input obtained
        """
        got_input = False
        self._button_pressed = False
        if (event.type is pygame.KEYDOWN
            or event.type is pygame.KEYUP):
            got_input = self._get_keyboard_input(event)
        elif (event.type is pygame.JOYAXISMOTION 
              or event.type is pygame.JOYBUTTONDOWN
              or event.type is pygame.JOYBUTTONUP):
            got_input = self._get_joystick_input(event)
        return got_input

    def _increment(self, value: float, inc: float) :
        return max(min(value + inc, 1.0), -1.0)

    def _incrementz(self, value: float, inc: float):
        return max(min(value + inc, 1.0), 0)

    def _get_keyboard_input(self, event):
        """Get input from the keyboard.
        
            In addition to controls to simulate the joysticks and buttons it also allows elements of the simulator 
            to be individually enabled/disabled and the app to be terminated
        """
        chars = (pygame.K_b, pygame.K_d, pygame.K_g, pygame.K_h, pygame.K_l, pygame.K_p, pygame.K_t)
        self.char = None
        got_input = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE :
                self._button_pressed = True
                self.char = event.key
                got_input = True
            elif event.key == pygame.K_b:
                self._seat_occupied = False
                self.char = event.key
                got_input = True
            elif event.key == pygame.K_UP:
                self.y = self._increment(self.y, self.y_inc)
                got_input = True
            elif event.key == pygame.K_DOWN:
                self.y = self._increment(self.y, -self.y_inc)
                got_input = True
            elif event.key == pygame.K_LEFT:
                self.x = self._increment(self.x, -self.x_inc)
                got_input = True
            elif event.key == pygame.K_RIGHT:
                self.x = self._increment(self.x, self.x_inc)
                got_input = True
            elif event.key == pygame.K_KP5:
                self.x = 0.0
                self.y = 0.0
                got_input = True
            elif event.key == pygame.K_a:
                self.z = self._incrementz(self.z, self.z_inc)
                got_input = True
            elif event.key == pygame.K_z:
                self.z = self._incrementz(self.z, -self.z_inc)
                got_input = True
            elif event.key == pygame.K_x:
                self.r = self._increment(self.r, self.r_inc)
                got_input = True
            elif event.key == pygame.K_BACKSLASH:
                self.r = self._increment(self.r, -self.r_inc)
                got_input = True
            elif event.key in chars :
                self.char = event.key
                got_input = True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                self._button_pressed = False
                got_input = True
        if got_input:
            self.reset_inactive_timer()
        return got_input
    
    def _get_joystick_input(self, event: pygame.event) -> bool:
        """Get input from the joystick events.
        
            When the seat button is released a timer is started which will reset the app unless the switch is pressed again
            before the timeout
        
        event (event): the joystick event
        return: bool indicating that input was obtained from the buttons or the cyclic joystick which are used to control the app
        """
        got_input = False
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == defs.BTN_SELECT:
                self._button_pressed = True
                got_input = True
            elif event.button == defs.BTN.SEAT.value:
                self._seat_timer = None
                self._seat_occupied = True
                got_input = True
        elif event.type == pygame.JOYBUTTONUP:
            if event.button == defs.BTN_SELECT:
                self._button_pressed = False
                got_input = True
            elif event.button == defs.BTN.SEAT.value:
                self._seat_timer = time.time()
                got_input = True
        elif event.type == pygame.JOYAXISMOTION:
            if event.axis == 0:
                self.x = event.value
                got_input = True
            elif event.axis == 1:
                self.y = event.value
                got_input = True
            elif event.axis == 2:
                self.z = event.value
                got_input = True
            elif event.axis == 3:
                self.r = event.value
                got_input = True
        if got_input:
            self.reset_inactive_timer()
        return got_input
    
    def set_scroll(self, scroll):
        self._fc.set_scroll(scroll)
    
    def get_arrow(self, event):
        """ Get an arrow key or thumb button from an event
        
        event: the event to process
        
        return: the arrow or None
        """
        arrow = None
        if ((event.type == pygame.KEYDOWN and event.key == pygame.K_UP)
            or (event.type == pygame.JOYBUTTONDOWN and event.button == defs.BTN.UP.value)
            ):
            arrow = pygame.K_UP
        elif ((event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN)
            or (event.type == pygame.JOYBUTTONDOWN and event.button == defs.BTN.DOWN.value)
            ):
            arrow = pygame.K_DOWN
        elif ((event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT)
            or (event.type == pygame.JOYBUTTONDOWN and event.button == defs.BTN.LEFT.value)
            ):
            arrow = pygame.K_LEFT
        elif ((event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT)
            or (event.type == pygame.JOYBUTTONDOWN and event.button == defs.BTN.RIGHT.value)
            ):
            arrow = pygame.K_RIGHT
        if arrow != None:
            self.reset_inactive_timer()
        return arrow

def choose_cell(cells, cellx, celly = 0) -> ():
    """Choose a cell position using keyboard or joystick.
    
    cells: list of x,y pairs giving upper coordinates of the cell (only used for joystick input)
    cellx: the x coordinate of the initial cell
    celly: the y coordinate for the initial cell
    
    return: list containing:
        selected (bool): user pressed the selection button for this cell
        cellx: the x coordinate of the current cell
        celly: the y coordinate of the current cell
        x: the joystick x value
        y: the joystick y value
    """
    im = InputManager.get_instance()
    selected = False
    for event in im.get_events():
        if ((event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) 
            or (event.type == pygame.JOYBUTTONDOWN and event.button == defs.BTN_SELECT)):
            selected = True
            im.reset_inactive_timer()
        else:
            arrow = im.get_arrow(event)
            if arrow != None:
                if arrow == pygame.K_UP and celly > 0:
                    celly -= 1
                elif arrow == pygame.K_DOWN and celly < len(cells[1]) - 1:
                    celly += 1
                elif arrow == pygame.K_LEFT and cellx > 0:
                    cellx -= 1
                elif arrow == pygame.K_RIGHT and cellx < len(cells[0]) - 1:
                    cellx += 1
    return selected, cellx, celly#, x, y
        
def ask(screen: pygame.surface, question: str, fgd: () = defs.WHITE, bgd: () = defs.BLACK, font = None) -> bool:
    """Prompt the user for a Yes/No answer
    
    screen: the surface to display the promp on
    question: the prompt text
    fgd: the foreground colour
    bgd: the background colour
    font: the font to display the prompt in
    """
    im = InputManager.get_instance()
    screen_rect = screen.get_rect()
    if font == None: font = get_font(TEXT_FONT)
    t = font.render(question, True, fgd)
    text_rect = t.get_rect(center = screen_rect.center)
    t_yes = font.render(_("Yes"), False, fgd)
    t_yes_rect = t_yes.get_rect(center = screen_rect.center).move(-150, 100)
    t_yes_box = t_yes_rect.inflate(10, 10)
    t_no = font.render(_("No"), False, fgd)
    t_no_rect = t_no.get_rect(center = screen_rect.center).move(150, 100)
    t_no_box = t_no_rect.inflate(10, 10)
    rect = text_rect.unionall([t_yes_rect, t_no_rect]).inflate(50, 50)
    restore = pygame.Surface((rect.w, rect.h))
    restore.blit(pygame.display.get_surface(), (0, 0), rect)
    screen.fill(bgd, rect)
    screen.blit(t, text_rect)
    screen.blit(t_yes, t_yes_rect)
    screen.blit(t_no, t_no_rect)
    pygame.display.update(rect)
    answer = True
    done = False
    while not done:   
        for event in im.get_events():
            im.reset()
            im.get_input(event)
            if im._button_pressed:
                done = True
            else :
                answer = im.x < 0
        if answer == True:
            yes_colour = defs.HIGHLIGHT_COLOUR
            no_colour = bgd
        else:
            yes_colour = bgd
            no_colour = defs.HIGHLIGHT_COLOUR
        pygame.draw.rect(screen, yes_colour, t_yes_box, 2)
        pygame.draw.rect(screen, no_colour, t_no_box, 2)
        pygame.display.update((t_yes_box, t_no_box))
    screen.blit(restore, rect)
    pygame.display.update(rect)
    return answer

def scroll_text(screen : pygame.surface,
                filenames : [],
                font : pygame.font, 
                fgd: (),
                bgd: (),
                rectmain : pygame.rect,
                label : bool = False):
    """Render text to the screen in a scrollable window.
    
    screen: the screen to render to
    filenames: files containing the text to render
    font: the font to use
    fgd: the foreground colour
    bgd: the background colour
    rectmain: the window to scroll within
    label: text is static requiring no input
    """
    im = InputManager.get_instance()
    rect = rectmain.copy()
    prev_page = page = 0
    if not label: 
        pygame.key.set_repeat(150, 100)
        im.set_scroll(True)
        rect.inflate_ip(-100, -100)
        arrows = Arrows()
    rects = []
    finished = False
    while not finished :
        first_pass = True
        # Get the page text and render it onto a surface, wrapped if necessary
        text = i18n.read_file(filenames[page])
        lines = wrap_text(text, font, rect.width)
        surf = render_text_list(lines, font, fgd, bgd) 
        maxy = rect.top
        if surf.get_height() > rect.height :
            miny = maxy - surf.get_height() + rect.height
        else :
            miny = maxy
        y_offset = maxy
        y_inc = 10
        prev_y_offset = y_offset - 1
        change_page = False
        while not finished and (label or not change_page):
            if first_pass:                  
                if bgd != None:
                    screen.fill(bgd, rectmain)
                rects = []
            else:
                for r in rects:
                    screen.fill(bgd, r)
            if not label:
                # Get input, changing page in the x direction and scrolling in the y direction
                for event in im.get_events():
                    if ((event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) 
                        or (event.type == pygame.JOYBUTTONDOWN and event.button == defs.BTN_SELECT)):
                        finished = True
                    else :
                        arrow = im.get_arrow(event)
                        if arrow != None:
                            if arrow == pygame.K_UP and y_offset < maxy:
                                y_offset += y_inc
                            elif arrow == pygame.K_DOWN and y_offset > miny:
                                y_offset -= y_inc
                            elif arrow == pygame.K_LEFT and page > 0:
                                page -= 1
                            elif arrow == pygame.K_RIGHT and page < len(filenames) - 1:
                                page += 1
                        change_page = page != prev_page
                        if change_page or y_offset != prev_y_offset:
                            break
                # Display arrows if there is more to come in the x or y direction
                if y_offset != prev_y_offset:                    
                    rects += arrows.blit(screen, rectmain, page > 0, page < len(filenames) - 1, y_offset < maxy, y_offset > miny)
            # Show the scrolled text if it has moved
            if y_offset != prev_y_offset:                    
                screen.set_clip(rect)
                rects.append(screen.blit(surf, [rect.left, y_offset]))      
                screen.set_clip()
                if first_pass:
                    first_pass = False
                    pygame.display.update()
                else:
                    pygame.display.update(rects)
            if label:
                finished = True
            prev_y_offset = y_offset
            prev_page = page
    if not label: 
        pygame.key.set_repeat()
        im.set_scroll(False)
    
def wrap_text(text, font, width):
    """Wrap text to fit inside a given width when rendered.
    
    text: The text to be wrapped.
    font: The font the text will be rendered in.
    width: The width to wrap to.
    """
    text_lines = text.replace('\t', '    ').split('\n')
    if width is None or width == 0:
        return text_lines

    wrapped_lines = []
    for line in text_lines:
        line = line.rstrip() + ' '
        if line == ' ':
            wrapped_lines.append(line)
            continue

        # Get the leftmost space ignoring leading whitespace
        start = len(line) - len(line.lstrip())
        start = line.index(' ', start)
        while start + 1 < len(line):
            # Get the next potential splitting point
            nxt = line.index(' ', start + 1)
            if font.size(line[:nxt])[0] <= width:
                start = nxt
            else:
                wrapped_lines.append(line[:start])
                line = line[start+1:]
                start = line.index(' ')
        line = line[:-1]
        if line:
            wrapped_lines.append(line)
    return wrapped_lines

def render_text_list(lines, font, colour=(255, 255, 255), bgd=(0,0,0,0)):
    """Draw multiline text to a surface with a transparent background and return the surface
    lines: The lines of text to render.
    font: The font to render in.
    colour: The colour to render the font in, default is white.
    """
    centred = []
    for i, line in enumerate(lines):
        if line.startswith('<c>'):
            lines[i] = line[3:]
            centred.append(i)
    rendered = [font.render(line, True, colour).convert_alpha() for line in lines]
    line_height = font.get_linesize()
    width = max(line.get_width() for line in rendered)
    tops = [int(round(i * line_height)) for i in range(len(rendered))]
    height = tops[-1] + font.get_height()
    surface = pygame.Surface((width, height)).convert_alpha()
    surface.fill(bgd)
    i = 0
    for y, line in zip(tops, rendered):
        x = 0
        if i in centred:
            x = (surface.get_width() - line.get_width()) / 2
        surface.blit(line, (x, y))
        i += 1
    return surface

def test():
    pygame.init()
    im = InputManager.get_instance()
    pygame.display.set_mode((100, 100))
    clock = pygame.time.Clock()
    done = False
    print("cycr  cycp  coll  antq  btn   soc")                          
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or(event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE):
                raise QuitException()
            else:
                im.get_input(event)
        print("%3.3f %3.3f %3.3f %3.3f %5s %5s" % (im.x, im.y, im.z, im.r, im._button_pressed, im._seat_occupied), end='\r')
        clock.tick(10)

if __name__ == "__main__":
    test()