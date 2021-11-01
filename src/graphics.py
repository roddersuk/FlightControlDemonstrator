'''
Graphics module for the Bell 47 demonstrator rig
This includes all of the graphical objects that can be displayed
'''
import pygame
import math
import random
#import logging
from enum import Enum

import defs
import mmi

def rotate(surface: pygame.surface, angle: float, pivot, offset: pygame.math.Vector2 = pygame.math.Vector2(0, 0), scale:float = 1.0):
    """Rotate the surface around the pivot point.

    surface (pygame.Surface): The surface that is to be rotated.
    angle (float): Rotate by this angle.
    pivot (tuple, list, pygame.math.Vector2): The pivot point.
    offset (pygame.math.Vector2): This vector is added to the pivot.
    """
    rotated_image = pygame.transform.rotozoom(surface, -angle, scale)  # Rotate the image.
    rotated_offset = offset.rotate(angle)  # Rotate the offset vector.
    # Add the offset vector to the center/pivot point to shift the rect.
    rect = rotated_image.get_rect(center = pivot + rotated_offset)
    return rotated_image, rect  # Return the rotated image and shifted rect.

def quantize(value: float, quantum: float):
    """Limit the return value to increments of quantum percent, rounded up
    e.g. for 5% a value of .98 would return 1.0, 0.53 would return 0.55
    
    value: the value to be quantized
    quantum: the percentage
    """
    return int(math.ceil(value * 100 / quantum) * quantum) / 100

def round_rect(surface: pygame.surface, rect: pygame.rect, radius: int, colour: pygame.color):
    """Display a rounded rectangle
    
    surface: the surface to diplay the rectangle on
    rect: the timensions of the rectangle
    radius: the radius of the rectangle corners
    colour: the fill colour
    """
    corners = rect.inflate(-2 * radius, -2 * radius)
    for attribute in ("topleft", "topright", "bottomleft", "bottomright"):
        pygame.draw.circle(surface, colour, getattr(corners,attribute), radius)
    surface.fill(colour, rect.inflate(-2 * radius, 0))
    surface.fill(colour, rect.inflate(0, -2 * radius))

class Dial(object):
    """Base class for all dials
    """
    def __init__(self):
        self._position = [0, 0]
        self._face = None
        self._screen = None
        
    def blit(self) -> pygame.rect:
        """Draw the dial and return its rect
        """
        rect = None
        if self._screen != None and self._face != None :
            rect = self._screen.blit(self._face, self._position) 
        return rect 
    
    def set_pos(self, pos):
        """Set the position for the dial
        
        pos: the coordinates. Positive values are offset from top/left, negative values from bottom/right
        """ 
        self._position = pos
        if self._screen != None and self._face != None :
            if self._position[0] < 0 :
                self._position[0] += self._screen.get_width() - self._face.get_width()
            if self._position[1] < 0 :
                self._position[1] += self._screen.get_height() - self._face.get_height()

class Meter(Dial):
    """Meter base class
    """
    
    def __init__(self, label: str):
        super().__init__()
        self._needle_rect = None
        self._font = mmi.get_font(mmi.METER_FONT)
        self._label = label
        self._needle = pygame.image.load("images/Meter Needle.png").convert_alpha()
        self._needle_pivot_offset = [110, 110]
        self._needle_offset = pygame.math.Vector2(0, -self._needle.get_height() / 2 - 8)
        self._min_angle = -90.0
        self._max_angle = 90.0
        
    def blit(self,
             screen: pygame.surface,
             value: float,
             pos:list = [0, 0]) -> pygame.rect:
        """Draw the meter on the specified screen with the given value at the given position
        
        screen: the surface on which to draw the dial
        value: the needle value
        pos: position on the surface (negative values indicate offset from the right/bottom)
        """
        self._screen = screen
        self.set_pos(pos)
        initial = True
        if self._needle_rect is None :
            # Initially display the full face and apply the text
            txt = self._font.render(self._label, True, (240, 240, 240))
            text_offset = [110 - txt.get_width() / 2, 160]
            self._face.blit(txt, text_offset)
            rect = super().blit()
        else:
            # For updates just restore the face where the needle was
            initial = False
            rect = self._needle_rect
            area = rect.move(-self._position[0], -self._position[1])
            screen.blit(self._face, rect, area)
        
        # Draw the needle in the new position
        needle_angle = self._min_angle + (value / 100.0) * (self._max_angle - self._min_angle)
        pivot = [x + y for x, y in zip(self._position, self._needle_pivot_offset)]
        needle, self._needle_rect = rotate(self._needle, needle_angle, pivot, self._needle_offset)
        screen.blit(needle, self._needle_rect)
        
        if initial:
            return [rect]
        else:
            return rect, self._needle_rect

class CollectiveMeter(Meter):
    def __init__(self, label: str):
        """Initialise the meter.
        
        label: the label to display on the face of the meter
        """
        super().__init__(label)
        self._face = pygame.image.load("images/CollectiveMeter.png").convert_alpha()
        self._min_angle = -105.0
        self._max_angle = 93.0
        self._needle_pivot_offset = [100, 110]

class PercentMeter(Meter):
    def __init__(self, label: str):
        """Initialise the meter.
        
        label: the label to display on the face of the meter
        """
        super().__init__(label)
        self._face = pygame.image.load("images/PercentMeter.png").convert_alpha()
        self._min_angle = -114.0
        self._max_angle = 126.0
        self._needle_pivot_offset = [105, 110]
        
class Altimeter(Dial):
    def __init__(self):
        super().__init__()
        self._text_rect = None
        self._needle_rect = None
        self._face =  pygame.image.load("images/Altimeter.png").convert_alpha()
        self._text_offset = [72, 65]
        self._font = mmi.get_font(mmi.ALTIMETER_FONT)
     
        self._needle = pygame.image.load("images/Altimeter_Needle.png").convert_alpha()
        self._needle_pivot_offset = [112, 117]
        self._needle_offset = pygame.math.Vector2(1, self._needle.get_height() / 2 + 4)

    def blit(self, 
             screen: pygame.Surface, 
             altitude: float, 
             pos:list = [0, 0]) -> (pygame.rect, pygame.rect):
        """Draw the altimeter on the specified surface at the given position showing the specified altitude
        
        screen - the surface on which to draw the dial
        altitude - the current altitude
        pos - position on the surface (negative values indicate offset from the right/bottom)
        """
        self._screen = screen
        self.set_pos(pos)
        initial = True
        if self._text_rect is None :
            super().blit()
        else:
            initial = False
            self._text_rect = self._text_rect.move(-self._position[0], -self._position[1])
            text_pos = self._text_rect.move(self._position[0], self._position[1])
            screen.blit(self._face, text_pos, self._text_rect)
            prev_needle_rect = self._needle_rect.inflate(10, 10) # Inflate to cope with slow frame rate not keeping up with needle
            area = prev_needle_rect.move(-self._position[0], -self._position[1])
            screen.blit(self._face, prev_needle_rect, area)
        
        # Draw the altitude numerics
        txt = self._font.render("{0:05d}".format(int(altitude)), True, (240, 240, 240))
        self._text_rect = screen.blit(txt, [x + y for x, y in zip(self._position, self._text_offset)])
        
        # Draw the needle
        needle_angle = altitude / 1000.0 * 360.0 + 180.0
        pivot = [x + y for x, y in zip(self._position, self._needle_pivot_offset)]
        
        needle, self._needle_rect = rotate(self._needle, needle_angle, pivot, self._needle_offset)
        screen.blit(needle, self._needle_rect)
        
        if initial:
            return self._text_rect, self._needle_rect
        else:
            return self._text_rect, prev_needle_rect, self._needle_rect
        
class ArtificialHorizon(Dial):
    def __init__(self):
        self._face = pygame.image.load("images/ArtificialHorizonBezel.png").convert_alpha()
        self._ring = pygame.image.load("images/ArtificialHorizonRing.png").convert_alpha()
        self._ball = pygame.image.load("images/ArtificialHorizonBall.png").convert_alpha()
        self._mask = pygame.image.load("images/ArtificialHorizonMask.png").convert_alpha()
        self._pitch = 0.0
        self._roll = 0.0
        self._shift = 0.0
        self._precision = 1.0
        self._ball_mask = None
        self._rotated_ball = None
        self._ball_rect = None
        self._rotated_ring = None
        self._ring_rect = None
        self._pivot_offset = [109, 109]
        self._ball_dia = 150.0
    
    def blit(self, 
             screen:pygame.surface, 
             pitch:float, 
             roll: float, 
             pos: list = [0, 0]) -> (pygame.rect):
        """Draw the artificial horizon on the specified surface at the given position showing the specified pitch and roll
        
        screen - the surface on which to draw the dial
        value - the needle value
        pos - position on the surface (negative values indicate offset from the right/bottom)
        """
        self._screen = screen
        self.set_pos(pos)
        
        pivot = [x + y for x, y in zip(self._position, self._pivot_offset)]
        pitch_changed = abs(pitch - self._pitch) > self._precision
        roll_changed = abs(roll - self._roll) > self._precision
        if (pitch_changed) :
            self._shift = self._ball_dia * math.sin(math.radians(pitch)) / 2.0
        
        # Prepare the ball mask
        if (self._ball_mask == None or pitch_changed) :
            self._ball_mask = self._ball.copy()
            mask_pos = (0, self._shift + (self._ball.get_height() - self._mask.get_height()) / 2)
            self._ball_mask.blit(self._mask, mask_pos, None, pygame.BLEND_RGBA_MULT)
        
        # Blit the ball
        if (self._rotated_ball == None or pitch_changed or roll_changed) :
            self._rotated_ball, self._ball_rect = rotate(self._ball_mask, -roll, pivot, pygame.math.Vector2(0, 0 - self._shift))
            screen.blit(self._rotated_ball, self._ball_rect)
        
        # Blit the ring
        if (self._rotated_ring == None or pitch_changed or roll_changed) :
            self._rotated_ring, self._ring_rect = rotate(self._ring, -roll, pivot, pygame.math.Vector2(0, 0))
            screen.blit(self._rotated_ring, self._ring_rect)

        # Blit the main bezel
        super().blit()
        if pitch_changed or roll_changed:
            self._pitch = pitch
            self._roll = roll
            return (self._ring_rect)
        else:
            return None

class HelicopterState(Enum):
    STOPPED = 0
    RUNNING = 1
    WINDING_UP = 2
    WINDING_DOWN = 3

class Helicopter(object):
    def __init__(self, pivot):
        self._pivot = pivot
        self._state = HelicopterState.STOPPED
        self.MAX_ROTOR_INC = 35.0
        self.ROTOR_STEP = 0.2
        self.HELI_OFFSET = 64
        self.HELI_SHADOW = False
        if self.HELI_SHADOW:
            self._helicopter_shadow_image = pygame.image.load("images/Bell47HelicopterShadow.png").convert_alpha()
            self._heli_shadow_offset = pygame.math.Vector2(0, self.HELI_OFFSET)
        
        self._helicopter_image = pygame.image.load("images/Bell47Helicopter.png").convert_alpha()
        self._heli_offset = pygame.math.Vector2(0, self.HELI_OFFSET)
    
        self._rotor_image = pygame.image.load("images/Rotor2.png").convert_alpha()
        self._rotor_offset = pygame.math.Vector2(0, 0)
        
        self._rotor_angle = 0.0
        self._rotor_inc = 0.0
        
        self._heli_rect = self._helicopter_image.get_rect(center = pivot + self._heli_offset)
        if self.HELI_SHADOW:
            self._heli_shadow_rect = None
        self._rotor_rect = None
        self._prev_heading = None
        self._prev_img_heading = 0
        self._rotated_image = None
        
        pygame.mixer.music.load("sounds/running.ogg")
    
    def __del__(self) :
        # Ensure that the music is stopped when the helicopter is destroyed
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
    
    def set_state(self, state: HelicopterState):
        self._state = state
        
    def get_state(self) -> HelicopterState :
        return self._state
    
    def clear(self, screen: pygame.surface, colour: (), heading: float):
        """Clear the previous helicopter position
            The rotor is always cleared but the helicopter body is only cleared if the heading has changed
            by more than a given percentage to improve performance
        """
        if self._rotor_rect != None:
            screen.fill(colour, self._rotor_rect)
            img_heading = quantize(heading, defs.HELI_ROTATION_PERCENT)
            if img_heading != self._prev_img_heading:
                if self.HELI_SHADOW:
                    rect = self._heli_rect.union(self._heli_shadow_rect)
                else:
                    rect = self._heli_rect
                screen.fill(colour, rect)
            
    def blit(self, 
             screen:pygame.Surface, 
             heading: float,
             altitude: float) -> (pygame.rect, pygame.rect):
        """Display the helicopter on the given surface with the given heading
        
        screen: the surface to draw the helicopter on
        heading: the helicopter direction
        altitude: the helicopter altitude used to scle the shadow image (if shown)
        """
        img_heading = quantize(heading, defs.HELI_ROTATION_PERCENT)
        
        # Draw the shadow, rotating and scaling it if the heading or altitude have changed
        if self.HELI_SHADOW:
            prev_heli_shadow_rect = self._heli_shadow_rect
            self._heli_shadow_offset.from_polar((100 * altitude / defs.ALTITUDE_MAX, - (heading - 45)))
            self._heli_shadow_offset.y += self.HELI_OFFSET
             
            scale = 1.0 - (altitude / defs.ALTITUDE_MAX) * 0.8
            heli_shadow, self._heli_shadow_rect = rotate(
                self._helicopter_shadow_image,
                heading,
                self._pivot,
                self._heli_shadow_offset,
                scale)
            screen.blit(heli_shadow, self._heli_shadow_rect)

        # Draw the helicopter body, rotating it if the heading has changed by more than 5% (perf improvement)
        prev_heli_rect = self._heli_rect
        if img_heading == 0:
            self._rotated_image = self._helicopter_image
        elif img_heading != self._prev_img_heading:
            self._rotated_image, self._heli_rect = rotate(self._helicopter_image, img_heading, self._pivot, self._heli_offset)
        screen.blit(self._rotated_image, self._heli_rect)
        
        # Update the rotor state
        if (self._state == HelicopterState.STOPPED) :
            self._rotor_inc = 0.0
        elif self._state == HelicopterState.RUNNING :
            self._rotor_inc = self.MAX_ROTOR_INC
        elif self._state == HelicopterState.WINDING_UP :
            if self._rotor_inc < self.MAX_ROTOR_INC:
                self._rotor_inc += self.ROTOR_STEP
            else : self._state = HelicopterState.RUNNING
        elif self._state == HelicopterState.WINDING_DOWN :
            if self._rotor_inc > 0.0:
                self._rotor_inc -= self.ROTOR_STEP
            else : self._state = HelicopterState.STOPPED

        # Play the sound and update the rotor position
        if self._state == HelicopterState.WINDING_DOWN :
            pygame.mixer.music.stop()
        elif self._state != HelicopterState.STOPPED  and not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1)
        self._rotor_angle = (self._rotor_angle - self._rotor_inc) % 360.0

        # Draw the rotor
        prev_rotor_rect = self._rotor_rect
        rot, self._rotor_rect = rotate(self._rotor_image, self._rotor_angle, self._pivot, self._rotor_offset)
        if prev_rotor_rect is None:
            rotor_rect = self._rotor_rect
        else:
            rotor_rect = self._rotor_rect.union(prev_rotor_rect)
        screen.blit(rot, self._rotor_rect)

        # Work out the rects to be updated
        heli_rect = heli_shadow_rect = None
        if img_heading != self._prev_img_heading:
            if prev_heli_rect is None:
                heli_rect = self._heli_rect
                if self.HELI_SHADOW:
                    heli_shadow_rect = self._heli_shadow_rect
            else:
                heli_rect = self._heli_rect.union(prev_heli_rect)
                if self.HELI_SHADOW:
                    heli_shadow_rect = self._heli_shadow_rect.union(prev_heli_shadow_rect)
        self._prev_img_heading = img_heading
        return rotor_rect, heli_rect, heli_shadow_rect

class DirectionIndicator(object) :
    """Direction Indicator showing where the landing pad is
    """
    def __init__(self):
        self._image = pygame.image.load("images/Direction.png").convert_alpha()
        self._offset = pygame.math.Vector2(0, 0)
        self._rect = None
        self._direction = None
    
    def clear(self, screen: pygame.surface, colour: (), pad_offset: pygame.math.Vector2):
        """Clear the previous direction indicator.
        """
        if (self._rect != None and 
            self.direction(pad_offset) != self._direction):
            screen.fill(colour, self._rect)
    
    def direction(self, pad_offset: pygame.math.Vector2):
        if (abs(pad_offset.x) < 0.001 and abs(pad_offset.y) < 0.001) :
            return 0.0
        else :
            return math.degrees(math.atan2(pad_offset.y, pad_offset.x)) + 90.0

    def blit(self, 
             screen:pygame.Surface, 
             pad_offset: pygame.math.Vector2, 
             pivot: list) -> (pygame.rect):
        """Draw the direction indicator.
        """
        direction = self.direction(pad_offset)
        if self._direction == None or self._direction != direction:
            dir_img, self._rect = rotate(self._image, direction, pivot, self._offset)
            screen.blit(dir_img, self._rect)
            direction = self._direction
            return self._rect
        else :
            return None

class LandingPad(object):
    def __init__(self, pivot: list):
        """Initialize the landing pad
        
        pivot: the helicopter pivot point
        """
        self._pivot = pivot
        self._image = pygame.image.load("images/Pad.png").convert_alpha()
        self._pad_rect = None
        self._scaled_image = None
        self._prev_img_scale = 1
        
    def clear(self,
              screen: pygame.surface,
              colour: (),
              heading: float):
        """Clear the previous landing pad

        screen: the surface to draw the landing pad on
        colour: the background colour to clear to
        heading: direction of the helicopter
        """
        screen.fill(colour, self._pad_rect)
       
    def blit(self,
             screen: pygame.Surface, 
             scale: float, 
             offset: pygame.math.Vector2,
             heading: float) -> (pygame.rect):
        """Draw the landing pad.
        
        screen: the surface to draw the landing pad on
        scale: the scale of the landing pad (based on altitude)
        offset: the offset vector from the helicopter position
        heading: direction of the helicopter
        """
        img_scale = quantize(scale, 1)
        prev_rect = self._pad_rect
        if img_scale == 1:
            pad = self._image
        elif img_scale == self._prev_img_scale:
            pad = self._scaled_image
        else:
            img_width = int(self._image.get_width() * img_scale)
            pad = pygame.transform.scale(self._image, (img_width, img_width))
            self._scaled_image = pad
        rect = pad.get_rect(center = self._pivot + offset)
        self._pad_rect = screen.blit(pad, rect)
        self._prev_img_scale = img_scale
        return self._pad_rect, prev_rect 

class Landscape(object):
    def __init__(self,
                 pivot:list,
                 xmax: int,
                 ymax: int):
        """Initialize the lanscape items randomly distributed over the defined area
            The distribution aims to ensure there are always some items visible
            
        pivot: the helicopter pivot point
        xmax: the area size in the x direction
        ymax: the area size in the y direction
        """
        DENSITY_PERCENT = 0.5
        XBLOCKS = 7 # odd number helps ensure some around the landing pad
        YBLOCKS = 7
        self._pivot = pivot
        self._images = []
        self._images.append(pygame.image.load("images/Landscape/Tree.png").convert_alpha())        
        self._images.append(pygame.image.load("images/Landscape/Palm.png").convert_alpha())        
        self._images.append(pygame.image.load("images/Landscape/Plant.png").convert_alpha())        
        self._images.append(pygame.image.load("images/Landscape/Rock.png").convert_alpha())        
        self._images.append(pygame.image.load("images/Landscape/Boulder.png").convert_alpha())
        self._prev_img_scale = 1
        self._scaled_images = []
        
        self._rects = []
        iw = self._images[0].get_width()
        ih = self._images[0].get_height()
        n = int(xmax * 2 / iw * ymax * 2 / ih * DENSITY_PERCENT / 100)
        xinc = int(xmax * 2 / XBLOCKS)
        yinc = int(ymax * 2 / YBLOCKS)
        nblock = int(n / XBLOCKS / YBLOCKS) # Number of items per block
        random.seed()
        # Create items randomly in each block 
        items = [
            {
                "x": random.randint(col, col + xinc),
                "y": random.randint(row, row + yinc),
                "image" : random.randint(0, len(self._images) - 1),
            } 
            for row in range(-ymax, ymax, yinc)
            for col in range(-xmax, xmax, xinc)
            for _ in range(nblock)
            ]
        # Add extra items in the centre to ensure some are on screen at the start
        xs = defs.SCREEN_WIDTH / 2
        ys = (defs.SCREEN_HEIGHT - defs.DASH_HEIGHT) / 2
        items += [
            {
                "x": random.randint(-xs, xs),
                "y": random.randint(-ys, ys),
                "image" : random.randint(0, len(self._images) - 1),
            } 
            for _ in range(3)
            ]
        # Eliminate items that coincide with the landing pad
        self._items = [item for item in items if abs(item["x"]) > 150 and abs(item["y"]) > 150]
    
    def clear(self,
              screen: pygame.surface,
              colour: (),
              heading: float):
        """Clear the previous landscape items.
        
        screen: the surface to clear the items from
        colour: the background colour to clear to
        heading: direction of the helicopter
        """
        [screen.fill(colour, rect) for rect in self._rects]
    
    def blit(self,
             screen: pygame.surface,
             scale: float,
             offset: pygame.math.Vector2,
             heading: float) -> (pygame.rect):
        """Display the landscape items.
        
        screen: the surface to display the items on
        scale: the scale of the items
        offset: the offset vector from the helicopter position
        heading: direction of the helicopter
        """
        # Limit the scale to increments of 1% for performance
        img_scale = quantize(scale, 1)
        prev_rects = self._rects
        self._rects = []
        if (img_scale == 1):
            imgs = self._images
        elif img_scale == self._prev_img_scale:
            imgs = self._scaled_images
        else:
            img_width = int(self._images[0].get_width() * img_scale)
            imgs = [pygame.transform.scale(img, (img_width, img_width)) for img in self._images]
            self._scaled_images = imgs
        for item in self._items:
            centre = (self._pivot[0] + item['x'] * img_scale, self._pivot[1] + item['y'] * img_scale) + offset
            img = imgs[item['image']]
            rect = img.get_rect(center = centre)
            self._rects.append(screen.blit(img, rect))
        self._prev_img_scale = img_scale
        return self._rects + prev_rects
         
class Arrows(object):
    def __init__(self):
        self._left_arrow = mmi.get_image(mmi.LEFT_IMAGE, "images/LeftArrow.png")
        self._right_arrow = mmi.get_image(mmi.RIGHT_IMAGE, "images/RightArrow.png")
        self._up_arrow =  mmi.get_image(mmi.UP_IMAGE, "images/UpArrow.png")
        self._down_arrow =  mmi.get_image(mmi.DOWN_IMAGE, "images/DownArrow.png")
    
    def blit(self, screen, rect, show_left, show_right, show_up, show_down) -> ():
        """Draw direction arrows as required.
        
        screen: the surface to draw the arrows on
        rect: the rect to draw the arrows within
        show_left: show the left arrow
        show_right: show the right arrow
        show_up: show the up arrow
        show_down: show the down arrow
        """
        rects = []
        if show_left:
            arrow_rect = pygame.Rect(rect.left + 1, rect.top + rect.height / 2 - 24, 48, 48)
            rects.append(screen.blit(self._left_arrow, arrow_rect))
        if show_right:
            arrow_rect = pygame.Rect(rect.left + rect.width - 49, rect.top + rect.height / 2 - 24, 48, 48)
            rects.append(screen.blit(self._right_arrow, arrow_rect))
        if show_up:
            arrow_rect = pygame.Rect(rect.left + rect.width / 2 - 24, rect.top + 1, 48, 48)
            rects.append(screen.blit(self._up_arrow, arrow_rect))
        if show_down:
            arrow_rect = pygame.Rect(rect.left + rect.width / 2 - 24, rect.top + rect.height - 49, 48, 48)
            rects.append(screen.blit(self._down_arrow, arrow_rect))
        return rects

def write(screen: pygame.surface, 
          label: str, 
          value, 
          line: int, 
          fontname = "text", 
          fgd = [0, 0, 0], 
          bgd = [255, 255, 255]) -> pygame.rect:
    """ Write a value to a line on the screen
    
    label (string): the label text
    value (float): the value to write
    line (int): the line to write the text on
    fontname (str): the font to use
    fgd: the foreground colour
    bgd: the background colour
    """
    font = mmi.get_font(fontname)
    if type(value) is str:
        t = font.render(label + " " + value + "     ", True, fgd, bgd)
    else:
        t = font.render(label + " {0:.2f}".format(value), True, fgd, bgd)
    return screen.blit(t, [0, line*20])

            
            
    