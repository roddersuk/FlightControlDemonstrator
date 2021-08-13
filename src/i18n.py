'''
Internationalisation module for the Bell 47 demonstrator rig
Performs language selection and all translations
'''
import gettext
import pygame
from pathlib import Path

from mmi import choose_cell
from defs import HIGHLIGHT_COLOUR

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
    # Ensure English is in the middle so its the default with a centred joystick
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
            pygame.draw.rect(screen, HIGHLIGHT_COLOUR, flag_rects[cellx], 2)
    # Let the user choose
    result = choose_cell(cells, cellx)
    if result[1] != cellx:
        cellx = result[1]
        set_language(sorted_flags[cellx])
        pygame.draw.rect(screen, HIGHLIGHT_COLOUR, flag_rects[cellx], 2)
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
    
        
        