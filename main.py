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
from collections import deque

murapix_path = os.path.join(os.path.dirname(__file__),'..','..')
sys.path.append(murapix_path)
from murapix.murapix import Murapix, get_panel_adresses, get_deadzone_addresses, get_largest_rect_add


#%%Initialize global constants
FPS = 26
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


EMOTYPES_BTN = {4 : 'SUW',
                5 : 'Broccoli',
                6 : 'Robot',
                7 : 'Factory'}

UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3
SUW = 4
BROCCOLI = 5
ROBOT = 6
FACTORY = 7

PWD = [0,0,2,2,1,3,1,3]



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
        self.font = pygame.font.Font(None, font_size)
        
        self.set_counter_image()
               
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.paused = True

    def update(self):
        if not self.paused:
            self.time_left -= 1           
            self.set_counter_image()

            
        if self.time_left < 1:
            self.kill()
            
    def set_timer(self, time_s):
        """
        set time in seconds
        """
        self.time_left= time_s * self.fps
        self.set_counter_image()
        
    def switch_pause(self,set_it = None):
        """
        pause or resume the counter. If set_it is None, it will swap the state.
        If set_it is True, it will pause. In case of False, it will resume.      
        """
        if set_it is None:
            self.paused = not self.paused
        else:
            self.paused = set_it
        
        if self.paused:
            w, h= self.image.get_size()
            pygame.draw.rect(self.image,self.color,(w//5,0,w//5,h))
            pygame.draw.rect(self.image,self.color,(3*w//5,0,w//5,h))
        else:
            self.set_counter_image()
            
            
    def set_counter_image(self):
        text = self.font.render(
                    str((self.time_left // self.fps)), False, self.color)
        self.image = text     
            
        
class Show_Admin(AllActiveSprites):
    def __init__(self,playernumber,pos):
        super().__init__()
        self.color = (150,10,10)
        self.time_left = 2 * self.fps
        self.font = pygame.font.Font(None, 10)
        text = self.font.render(
                    str(playernumber), False, self.color)
        
        
        
        self.image = text
        self.rect = text.get_rect()
        self.rect.center = pos
        
    def update(self):
        self.time_left -= 1
        print('Hello show admin!{0}'.format(self.rect))
        if self.time_left < 1:
            self.kill()
        
           
class Final_Image(AllActiveSprites):
    def __init__(self, emotype, start_x, end_position, max_size):
        super().__init__()
        
        
        image_path = os.path.join('images',EMOTYPES_FINAL[emotype])
        self.image = pygame.image.load(image_path)
        self.emotype = emotype
        self.end_position = end_position
        
        self.rect = self.image.get_rect()
        self.rect.topleft = (start_x, end_position[1])
        
        
    def update(self):
        if self.rect.x > self.end_position[0]+10:
            self.rect.x -= 10
        else:
            self.rect.x = self.end_position[0]
            
        
        


class Emoticon(AllActiveSprites):
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
        
        self.add(self.active)
        
        
    @classmethod
    def reset_score(cls):
        cls.score = dict(zip(EMOTYPES.keys(),[0]*4))
    
        
    @classmethod
    def add_score(cls, emotype):
        cls.score[emotype] += 1    
    

    def update(self):
        self.rect.centery -= 1
        self.rect.centerx += random.choice((-1,1))
        
    def kill_it(self):
        self.kill()
        return EMOTYPE_COLORS[self.emotype]
        
    

#%% Make the murapix class
class PitchCounter(Murapix):
    
    def __init__(self):
        super(PitchCounter, self).__init__()
        self.gamepad = os.path.join(os.path.dirname(__file__),
                                    'gamepad4btn.svg')
        self.admin = 0
        
        pygame.joystick.init()
        self.NoP = 0#number of players (use joystick)
        self.loop = 0

    def set_gamepads(self):  
        
        NoJS = [x.startswith('js') for x in os.listdir("/dev/input")].count(True)
        if self.NoP != NoJS:
            print('New players! {0} => {1}'.format(self.NoP, NoJS))
            pygame.joystick.quit()
            pygame.joystick.init()
            self.NoP = pygame.joystick.get_count()#number of players (use joystick)
            self.joysticks = [pygame.joystick.Joystick(x) 
                         for x in range(self.NoP)]   
            self.btn_queue = [dict(antispam = 0,
                              queue = deque(maxlen=8)
                              ) for x in range(self.NoP)]
            for joy in self.joysticks:
                joy.init()
        
    
    def setup(self):
        self.SCREENRECT = self.scratch.get_rect()
        pygame.display.set_caption('Pitch Counter')
        
        # game constants
        self.fps = FPS
        
        
        self.setup_ingame()
        
        #scene status for while loops
        self.current_scene = 0
        self.scene_select = {
                0: self.ingame_loop,
                1: self.winner_loop
                }
        
    def setup_ingame(self):
        """
        setup the in game screen
        """
        print('Setting up voting screen')
        #initialization of sprites
        AllActiveSprites.fps = FPS
        Emoticon.reset_score()#reset scores to 0
        self.emo_count = 0 #number of votes casted
        
        
        #Prepare the joysticks
        pygame.joystick.init()
        self.joysticks = None
        self.set_gamepads()
        
                
        #prepare background    
        self.background = pygame.Surface(
                (self.SCREENRECT.size[0],
                 self.SCREENRECT.size[1]+1)
                ).convert(self._screen)
        
        self.background.fill((0, 0, 0))  
        
        self.scratch.blit(self.background, (0, 0))
        self.sprites = pygame.sprite.RenderUpdates()
        self.counter = Counter(60*3,
                               self.SCREENRECT.center,
                               min(
                                   self.SCREENRECT.height//2,
                                   self.SCREENRECT.width//2
                                   ))
        self.sprites.add(self.counter)
        AllActiveSprites.allactivesprites = self.sprites
        
        
    def setup_winner(self):
        """
        setup the second screen once a winner is selected
        """
        print('setting up emoticons that won')
        self.sprites.empty()
        NoPannels = self.max_number_of_panels
        self.winnertime = FPS*(NoPannels + 3)
        
        emonames, scores = zip(*Emoticon.score.items())
        emonames, scores = list(emonames), list(scores)
        
        if sum(scores)==0:
            scores = 1,1,1,1
        
        temp_scores = scores
        if sum(scores) > NoPannels:
            for i in range(len(scores)):
                temp_scores[i] = round((scores[i]/sum(scores))*NoPannels)
            scores = temp_scores
        
        score = dict(zip(emonames,scores))      
        self.winners = []
        
        panadd = get_panel_adresses(self.mapping,self.led_rows)
        
        
        
        for k, v in score.items():
            for i in range(v):
                try:
                    (x,y),(w,h) = next(panadd)
                    self.winners.append(Final_Image(k,self.SCREENRECT.width, (x,y), self.led_rows))
                except StopIteration:
                    return
        
        
    
    
    def logic_loop(self):
        clock = self.clock
        self.scene_select[self.current_scene]()
        msg = "\r Raw time: {0}, tick time: {1}, fps: {2}".format(clock.get_rawtime(),
                                                            clock.get_time(),
                                                            clock.get_fps())
        print(msg, end="")
        
        
        
    def graphics_loop(self):
        pass


    def do_admin_stuff(self,joy):
        if joy != self.admin:
            return
        
        last_keys = self.btn_queue[self.admin]['queue']
        
        if last_keys[-1] == ROBOT:
            self.counter.switch_pause()
        if len(last_keys) <2:
            return
        if (last_keys[-1] == FACTORY) and (last_keys[-2] ==SUW):
            self.counter.switch_pause(set_it=True)
            self.counter.set_timer(60*3)
                
        elif (last_keys[-1] == FACTORY) and (last_keys[-2] ==BROCCOLI):
            self.counter.switch_pause(set_it=True)
            self.counter.set_timer(60*1)
                
        
            
            
    def ingame_loop(self):
        self.focus = True
        for event in pygame.event.get():
            if ((event.type == pgl.QUIT) 
                or ((event.type == pgl.KEYDOWN) 
                    and (event.key == pgl.K_ESCAPE))):
                self.RUNNING = False
                
            if (event.type == pygame.JOYBUTTONUP):
                joy = event.joy
                btn = event.button
                status = self.btn_queue[joy]
                pressed = []
                
                status['queue'].append(btn)
                if btn >3:
                    #list of strings!
                    pressed.append(EMOTYPES_BTN[btn])
                if joy == self.admin:
                    #do admin stuff
                    self.do_admin_stuff(joy)
                else:
                    #if password entered, give admin role to that player
                    if list(status['queue']) == PWD:
                        self.admin = joy
                        self.sprites.add(Show_Admin(self.admin,
                                                        (self.SCREENRECT.right-32,
                                                         self.SCREENRECT.bottom-32))
                                        )
                    
                    if status['antispam'] < 1 and len(pressed)>0:
                        #do player stuff
                        status['antispam'] = self.fps
                        y_pos = self.SCREENRECT.bottom
                        
                        x_pos = random.randint(0,self.SCREENRECT.width)
                        
                        emo = Emoticon((x_pos,y_pos),pressed[0])#only first event registered
                        emo.rect = emo.rect.clamp(self.SCREENRECT)
                        self.sprites.add(emo)
                        
                        
        for status in self.btn_queue:
            #does nothing, reduce by one antispam countdown
            status['antispam'] = max(0,status['antispam'] -1)
                
        
        for emo in Emoticon.active:
            if not self.SCREENRECT.contains(emo):
                col = emo.kill_it()
                self.emo_count += 1
                bg_w, bg_h = self.background.get_size()
                x,y = self.emo_count%bg_w, self.emo_count//bg_w
                y = y - (y//bg_h)*bg_h
                self.background.set_at((x,y),col)
        
        
        
        self.scratch.blit(self.background,(0,0))#
        self.sprites.update()
        self.sprites.draw(self.scratch)
        
        
        if not self.counter.alive():
            print(Emoticon.score)            
            self.setup_winner()
            self.current_scene +=1
            
        self.loop +=1
        if (self.loop % self.fps) == 0:
            self.set_gamepads()
            self.loop = 0
        
        
        
    def winner_loop(self):
        for event in pygame.event.get():
            if ((event.type == pgl.QUIT) 
                or ((event.type == pgl.KEYDOWN) 
                    and (event.key == pgl.K_ESCAPE))):
                self.RUNNING = False
            if (event.type == pygame.JOYBUTTONUP):
                joy = event.joy
                btn = event.button
                status = self.btn_queue[joy]                
                status['queue'].append(btn)
                if joy == self.admin:
                    #do admin stuff
                    self.do_admin_stuff(joy)
                else:
                    #if password entered, give admin role to that player
                    if list(status['queue']) == PWD:
                        self.admin = joy
                        self.sprites.add(Show_Admin(self.admin))
        
        
        if self.winnertime % self.fps == 0:
            try:
                self.sprites.add(self.winners.pop(0))
            except IndexError:
                pass
        
        self.scratch.blit(self.background,(0,0))#
        self.sprites.update()
        self.sprites.draw(self.scratch)
        
        self.winnertime -= 1
        if self.winnertime < 1:
            self.setup_ingame()
            self.current_scene = 0
        
        

def main():

  PitchCounter().run()

if __name__ == '__main__':
  main()
