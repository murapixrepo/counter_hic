#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 13 09:25:55 2018
how to use:



@author: hyamanieu
"""

import pygame
import pygame.locals as pgl
from pygame.math import Vector2
import math
import os
import random
import itertools
import sys
import time

murapix_path = os.path.join(os.path.dirname(__file__),'..','..')
sys.path.append(murapix_path)
from murapix.murapix import Murapix, get_panel_adresses, get_deadzone_addresses, get_largest_rect_add


#%%Initialize global constants
FPS = 60
MAXSPEED = 60/FPS
MAXSPEED_SQUARED = MAXSPEED**2
MISSILE_SPEED = 5*60/FPS
RIGHT, UP, LEFT, DOWN = range(4)
direction = {pygame.K_UP: UP, pygame.K_DOWN: DOWN,
             pygame.K_LEFT: LEFT, pygame.K_RIGHT: RIGHT}
missile_direction = {None: (0, 0), UP: (0, -MISSILE_SPEED), DOWN: (0, MISSILE_SPEED),
                     LEFT: (-MISSILE_SPEED, 0), RIGHT: (MISSILE_SPEED, 0)}

EMOTYPES = dict(Broccoli="broccoli_8px.bmp",
				Robot = "robot_8px.bmp",
				SUW = "startupweekend_8px.bmp",
				Factory = "factory_8px.bmp",
)

EMOTYPE_COLORS = dict(Broccoli=(120,170,71),
				Robot = (255,30,30),
				SUW = (149,96,255),
				Factory = (30,185,234),
)

EMOTYPES_FINAL = dict(Broccoli="broccoli_64px.bmp",
				Robot = "robot_64px.bmp",
				SUW = "startupweekend_64px.bmp",
				Factory = "factory_64px.bmp",
)



#Scene constants
INGAME = True #first screen is Ingame

#some colors
GREY = (90,90,90)
DARK_GREY = (30,30,30)



#%% create in game objects
class AllActiveSprites(pygame.sprite.Sprite):
    allactivesprites = pygame.sprite.RenderUpdates()
    fps = None

class Counter(AllActiveSprites):
    def __init__(self, total_time, pos, font_size=16):
        super().__init__()
        self.color = (250,250,255)
        self.time_left = total_time * self.fps
        font = pygame.font.Font(None, font_size)
        text = font.render(
                    str((self.time_left // self.fps) + 1), False, self.color)
        
        
        
        self.image = text
        self.rect = text.get_rect()
        self.rect.center = pos
        self.paused = False

    def update(self):
        font = pygame.font.Font(None, 8)
        if not self.paused:
            self.time_left -= 1
            
        
        text = font.render(
                    str((self.time_left // self.fps) + 1), False, self.color)
        self.image = text
        if self.respawnTime < 1:
            self.kill()
            
    def set_timer(self, time_s):
        """
        set time in seconds
        """
        self.time_left= time_s * self.fps
        
    def switch_pause(self,set_it = None):
        """
        pause or resume the counter. If set_it is None, it will swap the state.
        If set_it is True, it will pause. In case of False, it will resume.      
        """
        if set_it is None:
            self.paused = not self.paused
        else:
            self.paused = set_it
        
               
        
           
class Final_Image(AllActiveSprites):
    def __init__(self, emoticon, position, max_size):
        super().__init__()
        self.speed_of_growth = 1.1
        self.size_float = 8.
        self.max_size = max_size
        
    def update(self):
        if self.size_float < self.max_size:
            self.size_float *= self.speed_of_growth
            
        
        


class Emoticon(AllActiveSprites):
    pool = pygame.sprite.Group()
    active = pygame.sprite.Group()
    score = dict(zip(EMOTYPES.keys(),[0]*4))
    def __init__(self, start_position, emotype):
        """
        """
        
        
        super().__init__()
        image_path = os.path.join('images',EMOTYPES[emotype])
        self.image = pygame.image.load(image_path)
        self.add_score(emotype)
        self.emotype = emotype
        
        self.rect = self.image.get_rect()
        self.rect.center = start_position
           
        
    @classmethod
    def add_score(cls, emotype):
        cls.score[emotype] += 1    
    

    def update(self):
        self.rect.centery += 1
        self.rect.centerx += random.choice((-1,1))
        
    def kill_it(self):
        self.kill()
        return EMOTYPE_COLORS(self.emotype)
        
    

#%% Make the murapix class
class PitchCounter(Murapix):
    
    def __init__(self):
        super(PitchCounter, self).__init__()
        self.gamepad = os.path.join(os.path.dirname(__file__),
                                    'gamepad4btn.svg')
        self.admin = 0
        
    
    def setup(self):
        self.SCREENRECT = self.scratch.get_rect()
        pygame.display.set_caption('Pitch Counter')
        
        # game constants
        self.fps = FPS
        
        
        self.setup_ingame()
        self.setup_winner()
        self.setup_comm()
        
        #scene status for while loops
        self.current_scene = 0
        self.scene_select = {
                0: self.ingame_loop,
                1: self.winner_loop,
                2: self.comm_loop
                }
        
    def setup_ingame(self):
        """
        setup the in game screen
        """
        #initialization of sprites
        AllActiveSprites.fps = FPS
        
        
        #Prepare the joysticks
        pygame.joystick.init()
        self.joysticks = None
        if pygame.joystick.get_count() > 0:
            self.NoP = pygame.joystick.get_count()#number of players (use joystick)
            self.joysticks = [pygame.joystick.Joystick(x) 
                         for x in range(self.NoP)]            
        else:
            self.NoP = 1 #1 player (keyboard)
                
        #prepare background    
        self.background = pygame.Surface(
                (self.SCREENRECT.size[0],
                 self.SCREENRECT.size[1]+1)
                ).convert(self._screen)
        
        self.background.fill((0, 0, 0))  
        
        self.scratch.blit(self.background, (0, 0))
        self.sprites = pygame.sprite.RenderUpdates()
        self.counter = Counter()
        self.sprites.add()
        AllActiveSprites.allactivesprites = self.sprites
        
        
    def setup_winner(self):
        """
        setup the second screen once a winner is selected
        """
        self.winnertime = FPS*4  
        self.wevegotawinner = self.winnertime#how many seconds it shows the winner
        self.winner_radius = max(self.height,self.width)
        self.now = time.time()
        
    def setup_comm(self):
        """
        setup the third screen showing the ad once the game is finished.
        """
        self.dude = 0
        self.dude_2 = 0
        self.dude_3 = 0
        self.dude_4 = 0
        
        self.background2 = pygame.Surface((self.SCREENRECT.size[0],
                                           self.SCREENRECT.size[1])).convert(self._screen)
        self.background2.fill((0, 0, 0))        
        
        self.font = pygame.font.Font(None, self.height//3)
        self.text = self.font.render(
                    "MURAPIX", False, (128,204,240))
        self.font2 = pygame.font.Font(None, self.height//4)
        self.text2 = self.font2.render(
                    "soon on your", False, (128,204,240))
        self.text3 = self.font2.render(
                    "favorite places'", False, (128,204,240))
        self.text4 = self.font.render(
                    "Walls", False, (128,204,240))
    
    def logic_loop(self):
        clock = self.clock
        self.scene_select[self.current_scene]()
        msg = "\r Raw time: {0}, tick time: {1}, fps: {2}".format(clock.get_rawtime(),
                                                            clock.get_time(),
                                                            clock.get_fps())
        print(msg, end="")
    def graphics_loop(self):
        pass



    def ingame_loop(self):
        self.focus = True
        for event in pygame.event.get():
            if ((event.type == pgl.QUIT) 
                or ((event.type == pgl.KEYDOWN) 
                    and (event.key == pgl.K_ESCAPE))):
                self.RUNNING = False
            if ((event.type == pygame.KEYDOWN)
                  and (event.key in direction.keys())):
                cannon_dir = direction[event.key]
                for admiral in Admiral.active:
                    admiral.shoot_cannon(cannon_dir)
                    
            if (self.joysticks and (event.type == pgl.JOYBUTTONDOWN)):
                for admiral in Admiral.active:
                    playernumber = admiral.playernumber
                    
                    joystick = self.joysticks[playernumber]
                    pressed = []
                    for i in range(joystick.get_numbuttons()):
                        if joystick.get_button(i):
                            pressed.append(i)
                        
                    cannon_dir=None
                    if joystick.get_button(0):
                        cannon_dir = UP
                    if joystick.get_button(1):
                        cannon_dir = RIGHT
                    if joystick.get_button(2):
                        cannon_dir = DOWN
                    if joystick.get_button(3):
                        cannon_dir = LEFT
                    if cannon_dir is not None:
                        admiral.shoot_cannon(cannon_dir)
                        
            if (event.type == pgl.ACTIVEEVENT):
                print(event)
                
        #interaction between admirals, their missiles and other objects
        for admiral in Admiral.active:
            playernumber = admiral.playernumber
            if self.joysticks:
                joystick = self.joysticks[playernumber]
                joystick.init()
                x_axis, y_axis = handle_joystick(joystick)
            else:
                keys = pygame.key.get_pressed()
                x_axis = keys[pgl.K_d] - keys[pgl.K_q]
                y_axis = keys[pgl.K_s] - keys[pgl.K_z]
            for obstacle in pygame.sprite.spritecollide(admiral,self.obstacles,False):
                m_pos = Vector2(obstacle.rect.center)
                a_pos = Vector2(admiral.rect.center)
                new_speed = a_pos-m_pos
                new_speed.scale_to_length(
                            max(1,admiral.current_speed.length())
                                         )
                admiral.current_speed = new_speed
                admiral.move(0, 0)
            if not self.SCREENRECT.contains(admiral.rect):
                new_speed = - admiral.current_speed
                new_speed.scale_to_length(
                            max(1,new_speed.length())
                                         )
                admiral.current_speed = new_speed
                admiral.move(0, 0)
                admiral.rect = admiral.rect.clamp(self.SCREENRECT)
                
            else:
                admiral.move(x_axis, y_axis)                
                
            for missile in admiral.active_missile:
                for ad2 in pygame.sprite.spritecollide(missile, Admiral.active,False):
                    if ad2 != admiral and not ad2.invincible:
                        explosion = missile.table()
                        explosion.add(self.alldrawings)
                        counter = ad2.table()
                        counter.add(self.sprites)
                        admiral.score +=1
                if pygame.sprite.spritecollideany(missile, self.obstacles):
                    explosion = missile.table()
                    explosion.add(self.alldrawings)
                
                if not self.SCREENRECT.contains(missile.rect):
                    missile.table()
                
        #animate background
        self.bg_t +=1
        if self.bg_t>=self.bg_period:
            self.bg_t = 0
        self.scratch.blit(self.background, (0, 2*self.bg_t//(self.bg_period)))#add 1 pixel or not in vertical axis
        self.sprites.update()
        self.sprites.draw(self.scratch)
        self.alldrawings.update()
        
        global INGAME
        if not INGAME:
            self.current_scene +=1
        
        
    def winner_loop(self):
        for event in pygame.event.get():
            if ((event.type == pgl.QUIT) 
                or ((event.type == pgl.KEYDOWN) 
                    and (event.key == pgl.K_ESCAPE))):
                self.RUNNING = False
        
        winnertime = self.winnertime
        self.wevegotawinner -= 1
        if self.wevegotawinner < (winnertime-FPS) and self.wevegotawinner > 2*FPS:
            
            
            self.winner_radius -= max(self.height,self.width)/(winnertime - 3*FPS)
            surface = pygame.Surface(self.scratch.get_size(), depth=24)
            key = (255,255,255)#pure white for transparency
            surface.fill((0,0,0))
            if self.winner_radius > 18:
                pygame.draw.circle(surface,
                                   key,
                                   WINNER.rect.center,
                                   int(self.winner_radius))
            else:                
                pygame.draw.circle(surface,
                                   key,
                                   WINNER.rect.center,
                                   18)
            surface.set_colorkey(key)
            self.scratch.blit(surface, (0,0))
        elif self.wevegotawinner < 2*FPS:
            font = pygame.font.Font(None, self.height//3)
            text = font.render(
                        "WINNER", False, (255,255,255))
            
            self.scratch.blit(text,(self.width//4, self.height//2))
        
        
        if self.wevegotawinner < 1:
            self.current_scene +=1
        
        
        
        
    
    def comm_loop(self):
        
        for event in pygame.event.get():
            if ((event.type == pgl.QUIT) 
                or ((event.type == pgl.KEYDOWN) 
                    and (event.key == pgl.K_ESCAPE))):
                self.RUNNING = False
        
        background = self.background2
        
        self.scratch.blit(background, (0,0))
        
        if self.dude < self.width-(self.width//2 - self.text.get_width()//2):
            self.dude +=2*60/FPS
        elif self.dude_2 < self.width-(self.width//2 - self.text2.get_width()//2):
            self.dude_2 += 2*60/FPS
        elif self.dude_3 < self.width-(self.width//2 - self.text3.get_width()//2):
            self.dude_3 += 2*60/FPS
        elif self.dude_4 < self.width-(self.width//2 - self.text4.get_width()//2):
            self.dude_4 += 2*60/FPS
        self.scratch.blit(self.text,
                          (self.width-int(self.dude), 
                           self.height//8))
        self.scratch.blit(self.text2,
                          (self.width-int(self.dude_2), 
                           3*self.height//8))
        self.scratch.blit(self.text3,
                          (self.width-int(self.dude_3), 
                           4.5*self.height//8))
        self.scratch.blit(self.text4,
                          (self.width-int(self.dude_4), 
                           6*self.height//8))
        
        

def main():

  Amiral_8btn().run()

if __name__ == '__main__':
  main()
