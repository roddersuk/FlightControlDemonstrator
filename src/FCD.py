#!/usr/bin/python
'''
Created on 14 Oct 2018
Simple flight controls demonstrator based on the Agusta Bell 47 rig
Designed to run on a Raspberry Pi with a custom interface board providing A-D conversion for the flight controls
as well as a joystick buttons used to select options, a seat switch to detect user presence and a MOSFET to switch
on an optional motor to drive the rotor.
Requires Python3, Pygame and gpiozero

The raspberry pi should have Raspian Lite installed and be configured to enable the SPI interface and optionally 
connect to the THM network. [see INSTAL.md]
To enable the shutdown/startup button add the line 
    dtoverlay=gpio-shutdown
to the file /boot/config.txt 
As a final step it should be configured for a read-only file system as defined here 
https://learn.adafruit.com/read-only-raspberry-pi/ to prevent corruption on switch-off.
This is not reversible so should be the final step before production.

'''
__author__ = 'Rod Thomas <rod.thomas@talktalk.net>'
__date__ = '10 Nov 2021'
__version__ = '0.7.3'

# Library imports
import pygame
import math
from datetime import datetime
#import logging

# Project imports
import defs
from defs import ProgramState, QuitException, ResetException
from i18n import load_languages, select_language, scroll_text 
from mmi import render_text_list, wrap_text, get_font, ask, InputManager, choose_cell, get_image
from mmi import WELCOME_FONT, DESC_FONT, INFO_FONT, SMALL_FONT, MENU_FONT, WELCOME_IMAGE, LOGO_IMAGE
from graphics import CollectiveMeter, PercentMeter, round_rect, rotate
from simulator import simulator

#logging.basicConfig(filename="FCD.log", level=logging.DEBUG, filemode = "w")

def main() :
    """Display a welcome page allowing language selection and then offer a menu of options
    """
    load_languages() # Needs to be done first to set up text translation
    pygame.init()
    if defs.use_fast_events: pygame.fastevent.init()
    pygame.mixer.init()
    pygame.display.set_caption(_("Flight Controls Demonstrator"))
    screen = pygame.display.set_mode((defs.SCREEN_WIDTH, defs.SCREEN_HEIGHT))
    pygame.mouse.set_visible(False)
    im = InputManager.get_instance()
    state = ProgramState.WELCOME
    
    clock = pygame.time.Clock()
    try:
        while True :
            try:
                repaint = True
                if state == ProgramState.WELCOME:
                    repaint = False
                    state = welcome(screen)
                elif state == ProgramState.ABOUT:
                    state = about(screen)
                elif state == ProgramState.INTRODUCTION:
                    state = introduction(screen)
                elif state == ProgramState.MENU :
                    state = menu(screen, 
                                 [
                                  [_("Introduction"), ProgramState.INTRODUCTION],
                                  [_("How Do the Flight Controls Work on a Helicopter?"), ProgramState.DESCRIPTIONS],
                                  [_("Try Out the Flight Controls and See How They Affect the Rotor Blades"), ProgramState.CONTROLS],
                                  [_("Simple Flight Simulator"), ProgramState.BASIC_SIM],
                                  [_("Advanced Flight Simulator"), ProgramState.ADVANCED_SIM],
                                  [_("About"), ProgramState.ABOUT]],
                                 repaint)
                elif state == ProgramState.DESCRIPTIONS :
                    state = describe(screen)
                elif state == ProgramState.CONTROLS :
                    state = try_controls(screen)
                elif state == ProgramState.BASIC_SIM :
                    state = simulator(screen, True)
                elif state == ProgramState.ADVANCED_SIM :
                    state = simulator(screen, False)
            except ResetException:        
                # If there is no-one present return to the welcome screen
                # Make sure the motor is off
                if im.has_motor():
                    im.motor(False)
        
                # Stop any sounds
                if pygame.mixer.get_init():
                    pygame.mixer.stop()
                im.reset()
                state = ProgramState.WELCOME
            clock.tick(10)
                
    except QuitException as qe:
        import traceback
        tbe = traceback.extract_tb(qe.__traceback__)
        tb = [x[2] for x in tbe]
        print("User quit at %s" % ("->".join(tb)))
    finally:
        # Make sure the motor is off
        if im.has_motor():
            im.motor(False)

        # Stop any sounds
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        pygame.quit()

def welcome(screen : pygame.surface) -> ProgramState:
    """Display a welcome page with language selection flags
    
    screen: The surface to display the welcome page on
    """
    screen_rect = screen.get_rect()
    welcome_image = get_image(WELCOME_IMAGE, "images/AgustaBell47.jpg", False)
    img_rect = welcome_image.get_rect(center = screen_rect.center)
    screen.blit(welcome_image, img_rect)
    
    logo_image = get_image(LOGO_IMAGE, "images/blue_museum_logo.png")
    logo_rect = logo_image.get_rect(bottomright = screen_rect.bottomright).move(-20, -25)
    screen.blit(logo_image, logo_rect)
    
    font = get_font(WELCOME_FONT)
    t = font.render(_("Welcome to the"), True, defs.WELCOME_TEXT_COLOUR)
    text_rect = t.get_rect(center=screen_rect.center).move(0, -150)
    screen.blit(t, text_rect)
    t = font.render(_("Flight Controls"), True, defs.WELCOME_TEXT_COLOUR)
    text_rect = t.get_rect(center=screen_rect.center)
    screen.blit(t, text_rect)
    t = font.render(_("Demonstrator"), True, defs.WELCOME_TEXT_COLOUR)
    text_rect = t.get_rect(center=screen_rect.center).move(0, 150)
    screen.blit(t, text_rect)
    
    small_font = get_font(SMALL_FONT)
    now = datetime.now()
    t = small_font.render("%s" % (now.strftime("%d/%b/%Y %H:%M:%S")), False, defs.WHITE)
    text_rect = t.get_rect(bottomleft = screen_rect.bottomright).move(-120, -10)
    screen.blit(t, text_rect)
    t = small_font.render("v %s" % (__version__), False, defs.WHITE)
    text_rect = t.get_rect(bottomleft = screen_rect.bottomleft).move(10, -10)
    screen.blit(t, text_rect)

    if select_language(screen):
        return ProgramState.MENU
    else:
        pygame.display.update()
        return ProgramState.WELCOME

def about(screen: pygame.surface):
    """ Display details of the program in a window
    
    screen: The surface to display the about details on
    """
    text = render_text_list(
        ["<c>" + _("Flight Controls Demonstrator") + " v " + __version__,
         "<c>" + _("Developed by Rod Thomas"),
         "<c>" + _("for The Helicopter Museum"),
         "<c>" + _("2021")], 
        get_font(INFO_FONT), 
        defs.ABOUT_FOREGROUND_COLOUR,
        defs.ABOUT_BACKGROUND_COLOUR) 
    rect = text.get_rect()
    rect.center = screen.get_rect().center
    bgd_rect = rect.inflate(100, 100)
    round_rect(screen, bgd_rect, 40, defs.ABOUT_BACKGROUND_COLOUR)
    screen.blit(text, rect)
    pygame.display.update(bgd_rect)
    im = InputManager.get_instance( )
    im.get_any_key()
    return ProgramState.MENU

def introduction(screen : pygame.surface):
    screen_rect = screen.get_rect()
#     cyclic_image = get_image(CYCLIC_IMAGE, "images/CyclicGrip.png")
#     cyclic_rect = cyclic_image.get_rect(midright = screen_rect.midright).move(-50, 0)
#     screen.blit(cyclic_image, cyclic_rect)

    scroll_text(screen, 
        ['Intro.txt', 'Intro_Hardware.txt', 'Intro_Software.txt'], 
        get_font(DESC_FONT), 
        defs.DESC_FOREGROUND_COLOUR, 
        defs.DESC_BACKGROUND_COLOUR, 
        pygame.Rect(50, 50 ,screen_rect.w - 100, screen_rect.h - 100))
    return ProgramState.MENU

def menu(screen : pygame.surface, items : list, repaint : bool = True) -> ProgramState :
    """Display a set of menu options and return the selected state
    
    screen: the surface to display the menu on
    items: a list of item labels and states to select from
    repaint: repaint the welcome background when true
    """
    border_thickness = 10
    spacing = 100
    margin = 100
    corner_rad = 10
    gap = spacing + corner_rad

    # Set up menu cells
    cells_per_row = math.floor(math.sqrt(len(items)))
    no_rows = math.ceil(len(items) / cells_per_row)
    w = screen.get_width()
    h = screen.get_height()
    cell_width = w / cells_per_row
    cell_height = h / no_rows
    cells = [[],[]]
    for i in range(cells_per_row):
        cells[0].append(cell_width * (i + 1))
    for j in range(no_rows):
        cells[1].append(cell_height * (j + 1))
    
    # Get selected item based on current control position
    result = choose_cell(cells, menu.selected_column, menu.selected_row)
    menu.selected_row = result[2]
    menu.selected_column = result[1]
    selected = result[0]
    selected_item = menu.selected_row * cells_per_row + menu.selected_column

    if repaint:
        # Need to repaint background image after returning from selection
        repaint_rects = []
        for row in range(no_rows+1):
            top = int(row * cell_height - gap / 2)
            height = gap
            repaint_rects.append(pygame.Rect(0, top, w, height))
        for col in range(cells_per_row+1):
            left = int(col * cell_width - gap / 2)
            width = gap
            repaint_rects.append(pygame.Rect(left, int(gap / 2), width, h - gap))
        welcome_image = get_image(WELCOME_IMAGE)
        for r in repaint_rects:
            screen.blit(welcome_image, r, r)
     
    # Draw the menu cells        
    font = get_font(MENU_FONT)
    row = 0
    column = 0
    for item in items :
        bt = border_thickness
        cx = int(column * cell_width  + spacing / 2)
        cy = int(row * cell_height + spacing / 2)
        cw = int(cell_width - spacing)
        ch = int(cell_height - spacing)
        cell_rect = pygame.Rect(cx, cy, cw, ch)
        round_rect(screen, cell_rect, corner_rad, defs.MENU_BACKGROUND_COLOUR)
        border_rects = [
            pygame.Rect(cx + bt, cy + bt, cw - 2 *bt, bt),
            pygame.Rect(cx + bt, cy + ch - 2 * bt, cw - 2 * bt, bt),
            pygame.Rect(cx + bt, cy + bt, bt, ch - 2 * bt),
            pygame.Rect(cx + cw - 2 * bt, cy + bt, bt, ch - 2 * bt)
            ]
            
        if row == menu.selected_row and column == menu.selected_column:
            text_colour = colour = defs.MENU_SELECT_COLOUR
        else:
            text_colour = colour = defs.MENU_FOREGROUND_COLOUR
        [screen.fill(colour, r) for r in border_rects]
            
        t = render_text_list(wrap_text(item[0], font, cell_width - margin * 2), font, text_colour)
        t_rect = t.get_rect(center = cell_rect.center)
        screen.blit(t, t_rect)
        column += 1
        if column >= cells_per_row :
            column = 0
            row += 1
        
    if selected :
        return items[selected_item][1]
    else :
        pygame.display.update()
        return ProgramState.MENU
menu.selected_row = 0
menu.selected_column = 0
    
def describe(screen : pygame.surface) -> ProgramState :
    """Display pages of description about the flight controls
    
    screen: The surface to display the descriptions on
    """
    scroll_text(screen, 
                ['Inst_Overview.txt', 'Inst_Collective.txt', 'Inst_Cyclic.txt', 'Inst_AntiTorque.txt', 'Inst_Precession.txt'], 
                get_font(DESC_FONT), 
                defs.DESC_FOREGROUND_COLOUR, 
                defs.DESC_BACKGROUND_COLOUR, 
                pygame.Rect(100, 100 ,screen.get_width() - 200, screen.get_height() - 200))
    return ProgramState.MENU

def try_controls(screen : pygame.surface) -> ProgramState :
    """Display a schematic of the helicopter showing the rotor airofoil angle at positions around the helicopter
    and the position of the flight controls in meters allowing the user to try out the controls and observe their effect
    
    screen: The surface to display the schematic and control meters on
    """
    im = InputManager.get_instance( )
    im.reset()
    rotor_on = False
    if im.has_motor():
        if ask(screen, _("Do you want the blades to rotate?"), defs.WHITE, defs.DESC_BACKGROUND_COLOUR):
            rotor_on = True
            im.motor(True)
        
    collective_meter = CollectiveMeter(_("COLLECTIVE"))
    cyclic_long_meter = PercentMeter(_("CYCLIC LONG"))
    cyclic_lat_meter = PercentMeter(_("CYCLIC LAT"))
    rudder_pedal_meter = PercentMeter(_("RUDDER PEDAL"))
    
    # Draw background
    background_colour = defs.CONTROL_BACKGROUND_COLOUR
    rect = screen.get_rect().inflate(-40, -40)
    round_rect(screen, rect, 40, background_colour)

    # Draw helicopter and rotor
    area_rect = pygame.Rect(0, 0, screen.get_width() - 250, screen.get_height())
    helicopter = pygame.transform.scale2x(pygame.image.load("images/Bell47Helicopter.png").convert_alpha())
    heli_rect = helicopter.get_rect(center = area_rect.center)
    rotor = pygame.transform.scale2x(pygame.image.load("images/Rotor2.png").convert_alpha())
    rotor_rect = rotor.get_rect(center = area_rect.center).move(0, -128)
    screen.blit(helicopter, heli_rect)
    screen.blit(rotor, rotor_rect)
    
    # Set up aerofoil positions
    aerofoil = pygame.image.load("images/AerofoilCircle.png").convert_alpha()
    aerofoil_offset = 250
    port_aerofoil_rect = aerofoil.get_rect(center = rotor_rect.center).move(-aerofoil_offset, 0)
    stbd_aerofoil_rect = aerofoil.get_rect(center = rotor_rect.center).move(aerofoil_offset, 0)
    fwd_aerofoil_rect = aerofoil.get_rect(center = rotor_rect.center).move(0, -aerofoil_offset)
    aft_aerofoil_rect = aerofoil.get_rect(center = rotor_rect.center).move(0, aerofoil_offset)
    tail_aerofoil_rect = aerofoil.get_rect(center = rotor_rect.center).move(150, 350)

    # Draw explanatory text    
    font = get_font(INFO_FONT)
    screen.blit(
        render_text_list(
            wrap_text(_("Watch how the blade angle changes as you move the controls."), font, area_rect.w - 100), 
            font, 
            defs.CONTROL_FOREGROUND_COLOUR,
            background_colour), 
        (area_rect.left + 50, area_rect.bottom - 200))
    screen.blit(
        render_text_list(
            wrap_text(_("The movement is exaggerated for the purposes of illustration."), font, area_rect.w - 100), 
            font, 
            defs.CONTROL_FOREGROUND_COLOUR,
            background_colour), 
        (area_rect.left + 50, area_rect.bottom - 100))
    
    # Show the static items
    pygame.display.update(rect)
    
    clock = pygame.time.Clock()
    finished = False
    pygame.key.set_repeat(150, 100)
    while not finished :
        for event in im.get_events():
            im.get_input(event)
            if im._button_pressed:
                finished = True
            else:
                # Get control positions
                port_aerofoil_angle = im.z * defs.MAX_COLLECTIVE + (im.x + 1.0) * defs.MAX_CYCLIC
                stbd_aerofoil_angle = im.z * defs.MAX_COLLECTIVE - (im.x - 1.0) * defs.MAX_CYCLIC
                fwd_aerofoil_angle = im.z * defs.MAX_COLLECTIVE - (im.y - 1.0) * defs.MAX_CYCLIC
                aft_aerofoil_angle = im.z * defs.MAX_COLLECTIVE + (im.y  + 1.0) * defs.MAX_CYCLIC
                tail_aerofoil_angle = defs.MIN_TAIL - im.r * (defs.MAX_TAIL - defs.MIN_TAIL) + 90.0
                 
                # Draw aerofoils      
                rects = [port_aerofoil_rect, stbd_aerofoil_rect, fwd_aerofoil_rect, aft_aerofoil_rect, tail_aerofoil_rect]
                i, r = rotate(aerofoil, port_aerofoil_angle, port_aerofoil_rect.center)
                screen.blit(i, r)
                i, r = rotate(aerofoil, stbd_aerofoil_angle, stbd_aerofoil_rect.center)
                screen.blit(i, r)
                i, r = rotate(aerofoil, fwd_aerofoil_angle, fwd_aerofoil_rect.center)
                screen.blit(i, r)
                i, r = rotate(aerofoil, aft_aerofoil_angle, aft_aerofoil_rect.center)
                screen.blit(i, r)
                i, r = rotate(aerofoil, tail_aerofoil_angle, tail_aerofoil_rect.center)
                screen.blit(i, r)
                
                # Draw the position meters
                rects += collective_meter.blit(screen, im.z * 100.0, [-40, 40])
                rects += cyclic_long_meter.blit(screen, (im.y + 1.0) / 2.0 * 100.0, [-40, 280])
                rects += cyclic_lat_meter.blit(screen, (im.x + 1.0) / 2.0 * 100.0, [-40, 520])
                rects += rudder_pedal_meter.blit(screen, (im.r + 1.0) / 2.0 * 100.0, [-40, 760])
                
                pygame.display.update(rects)
        clock.tick(60)
        
    pygame.key.set_repeat()
    
    if rotor_on:
        im.motor(False)
    return ProgramState.MENU

if __name__ == "__main__":
    main()

#End  
