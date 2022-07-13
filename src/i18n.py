'''
Internationalisation module for the Bell 47 demonstrator rig
Performs language selection and all translations
'''
import gettext
import pygame
from pathlib import Path

import mmi
import graphics
from defs import HIGHLIGHT_COLOUR, FLAG_HIGHLIGHT_WIDTH, SCROLL_INCREMENT, BTN_SELECT
from pygame.time import delay
from time import sleep

languages = {}
current_language = 'en'
flags = {}
images = {}

def load_languages():
    """Load language translations from directories that exist in the locale and have message strings.
    """
    languages['en'] = gettext.NullTranslations() 
    locale = Path.cwd() / 'locale'
    for d in locale.iterdir() : 
        if d.is_dir():
            if (d / 'LC_MESSAGES').exists() :
                languages[d.name] = gettext.translation('FCD', localedir='locale', languages=[d.name])
            if (d / 'flag.png').exists() :
                flags[d.name] = d / 'flag.png'
    set_language('en')

def set_language(lang : str) :
    """Set the current language.
    
    lang: language id
    """
    global current_language
    try :
        languages[lang].install()
        current_language = lang
    except :
        languages['en'].install()
        current_language = 'en'
    mmi.current_language = current_language
        
def get_languages() -> {} :
    return languages

def select_language(screen : pygame.surface) -> bool:
    """Select language from display of country flags
    
    screen: the surface to display the flags on
    """
    FLAG_WIDTH = 100
    FLAG_HEIGHT = 60
    FLAG_GAP = 50
    x = (screen.get_width() - len(flags) * FLAG_WIDTH - (len(flags) - 1) * FLAG_GAP) / 2
    y = 50
    cells = [[], []]
    flag_rects = []
    # Ensure English is in the middle so its the default
    f = list(flags.keys())
    fi = [i for i in range(len(f))]
    mid = int(len(f) / 2)
    for i in range(len(f)):
        if f[i] == "en":
            if i != mid:
                temp = fi[mid]
                fi[mid] = i
                fi[i] = temp
            break
    sorted_flags = [f[i] for i in fi]
    # Display the flag images, highlighting the selected language
    for i, flag in enumerate(sorted_flags) :
        if flag not in images:
            images[flag] = pygame.image.load(flags[flag].as_posix()).convert()
        f = images[flag]
        rect = pygame.Rect(x, y, FLAG_WIDTH, FLAG_HEIGHT)
        screen.blit(f, rect)
        flag_rects.append(rect)
        x += FLAG_WIDTH + FLAG_GAP
        cells[0].append(x - FLAG_GAP / 2)
        if flag == current_language:
            cellx = i
            pygame.draw.rect(screen, HIGHLIGHT_COLOUR, flag_rects[cellx], FLAG_HIGHLIGHT_WIDTH)
    # Let the user choose
    result = mmi.choose_cell(cells, len(sorted_flags), cellx)
    if result[1] != cellx:
        cellx = result[1]
        set_language(sorted_flags[cellx])
        pygame.draw.rect(screen, HIGHLIGHT_COLOUR, flag_rects[cellx], FLAG_HIGHLIGHT_WIDTH)
    return result[0]

def read_file(name : str) -> str :
    """Read a language specific text file
    
    name: the name of the file to read
    """
    path = Path.cwd() / 'locale' / current_language / name
    try :
        f = open(str(path), 'r')
        text = f.read()
    except :
        text = _("Missing file") + " '" + name + "' " + _("for language") + " '" + current_language + "'"
    return text    
    
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
    im = mmi.InputManager.get_instance()
    rect = rectmain.copy()
    prev_page = page = 0
    if not label: 
        pygame.key.set_repeat(150, 100)
        im.set_scroll(True)
        rect.inflate_ip(-100, -100)
        arrows = graphics.Arrows()
    rects = []
    finished = False
    while not finished :
        # Get the page text and render it onto a surface, wrapped if necessary
        text = read_file(filenames[page])
        lines = mmi.wrap_text(text, font, rect.width)
        surf = mmi.render_text_list(lines, font, fgd, bgd) 
        maxy = rect.top
        if surf.get_height() > rect.height :
            miny = maxy - surf.get_height() + rect.height
        else :
            miny = maxy
        y_offset = maxy
        y_inc = SCROLL_INCREMENT
        prev_y_offset = y_offset - 1
        change_page = False
        while not finished and (label or not change_page):
            if bgd != None:
                screen.fill(bgd, rectmain)
            rects = [rectmain]
            if not label:
                # Get input, changing page in the x direction and scrolling in the y direction
                for event in im.get_events():
                    if ((event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) 
                        or (event.type == pygame.JOYBUTTONDOWN and event.button == BTN_SELECT)):
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
                if y_offset != prev_y_offset:
                    # Display arrows if there is more to come in the x or y direction
                    rects += arrows.blit(screen, rectmain, page > 0, page < len(filenames) - 1, y_offset < maxy, y_offset > miny)
            # Show the scrolled text if it has moved
            if y_offset != prev_y_offset:  
                screen.set_clip(rect)
                rects.append(screen.blit(surf, [rect.left, y_offset]))      
                screen.set_clip()
                pygame.display.update(rects)
            if label:
                finished = True
            prev_y_offset = y_offset
            prev_page = page
    if not label: 
        pygame.key.set_repeat()
        im.set_scroll(False)
        
        