import pygame
import neat
import time
import os
import random
pygame.font.init()

##########################################################################

#Constants including all imgs for animation

WIN_WIDTH = 500
WIN_HEIGHT = 800
FLOOR = 730
STAT_FONT = pygame.font.SysFont('comicsans', 50)

pygame.display.set_caption('Flappy Bird')

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join('flappy-imgs', 'bird1.png'))), pygame.transform.scale2x(pygame.image.load(os.path.join('flappy-imgs', 'bird2.png'))), pygame.transform.scale2x(pygame.image.load(os.path.join('flappy-imgs', 'bird3.png')))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join('flappy-imgs', 'pipe.png')))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join('flappy-imgs', 'base.png')))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join('flappy-imgs', 'bg.png')))

STAT_FONT = pygame.font.SysFont('comicsans', 50)

##########################################################################

#Bird class

class Bird:
	IMGS = BIRD_IMGS
	MAX_ROTATION = 25    #how much the bird will tilt during animation
	ROT_VEL = 20         #how much the bird will rotate each frame
	ANIMATION_TIME = 5   

	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.tilt = 0            #
		self.tick_count = 0      #physics of the bird...
		self.vel = 0             #velocity
		self.height = self.y
		self.img_count = 0
		self.img = self.IMGS[0]

#The orgin is top left of the screen. meaning up is negative, down is positive

	def do_jump(self):
		self.vel = -10.5
		self.tick_count = 0      #keeping track of when we last jumped
		self.height = self.y

	def move(self):
		self.tick_count += 1     #keeping track of how many times you moved

		# displacement, 
		displacement = self.vel*(self.tick_count) + 0.5*(3)*(self.tick_count)**2   # **2 is expotential.
		# -10.5 + 1.5 = -9 pixles
		#if not (self.jump):
		if displacement >= 16:       #Terminal velocity
			displacement = (displacement/abs(displacement)) * 16

		if displacement < 0:
			displacement -= 2

		self.y = self.y + displacement

		if displacement < 0 or self.y < self.height + 50: #tilt up
			if self.tilt < self.MAX_ROTATION:
				self.tilt = self.MAX_ROTATION
		else:                             #tilt down
			if self.tilt > -90:
				self.tilt -= self.ROT_VEL

		# 		if keys[pygame.K_SPACE]:
		# 			self.jump = True
		# else:
		# 		if self.jump_count >= -10:
		# 			self.y -= (self.jump_count * abs(self.jump_count)) * 0.5
		# 			self.jump_count -= 1
		# 		else:
		# 			self.jump_count = 10
		# 			self.jump = False

	def draw(self, win):         #animation
		self.img_count += 1

		if self.img_count <= self.ANIMATION_TIME:
			self.img = self.IMGS[0]
		elif self.img_count <= self.ANIMATION_TIME*2:
			self.img = self.IMGS[1]
		elif self.img_count <= self.ANIMATION_TIME*3:
			self.img = self.IMGS[2]
		elif self.img_count <= self.ANIMATION_TIME*4:
			self.img = self.IMGS[1]
		elif self.img_count == self.ANIMATION_TIME*4 + 1:
			self.img = self.IMGS[0]
			self.img_count = 0

		if self.tilt <= -80:
			self.img = self.IMGS[1]
			self.img_count = self.ANIMATION_TIME*2

	
		rotated_image = pygame.transform.rotate(self.img, self.tilt) #rotation an image around it's center
		new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center)
		win.blit(rotated_image, new_rect.topleft)

	#collition with bird and objects
	def get_mask(self):
		return pygame.mask.from_surface(self.img) #look up pygame.mask

##########################################################################

class Pipe:
	GAP = 200
	VEL = 5

	def __init__(self, x):
		self.x = x
		self.height = 0

		self.top = 0
		self.bottom = 0
		self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True) #flips pipe for top pipe
		self.PIPE_BOTTOM = PIPE_IMG

		self.passed = False            #for collitions
		self.set_height()

	def set_height(self):
		self.height = random.randrange(50, 450)
		self.top = self.height - self.PIPE_TOP.get_height()
		self.bottom = self.height + self.GAP

	def move(self):
		self.x -= self.VEL

	def draw(self, win):
		win.blit(self.PIPE_TOP, (self.x, self.top))
		win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

	'''
	Masks are an array of all the pixles that make up a image inside a 'box'. Pygame using this for collitons
	for example. Pixel Perfect collistions are better to use than regualr box around object collitions.
	The mask will determine if the pixles are transparent or not. making an 2d array 
	[    ].  as many rows as pixles going down 
	[.   ]   as many collums as pixles going arcoss

	This code will compare the bird array to pipe array
	'''
	def collide(self, bird):
		bird_mask = bird.get_mask()
		top_mask = pygame.mask.from_surface(self.PIPE_TOP)
		bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

		top_offset = (self.x - bird.x, self.top - round(bird.y))       #offsets tells how far away the 2 top left hand corners are
		bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

		b_point = bird_mask.overlap(bottom_mask, bottom_offset)  #bottom pipe colliton point
		t_point = bird_mask.overlap(top_mask, top_offset)  #top pipe colliton point

		if t_point or b_point:
			return True

		return False

##########################################################################

class Base:
	VEL = 5
	WIDTH = BASE_IMG.get_width()
	IMG = BASE_IMG

	def __init__(self, y):
		self.y = y
		self.x1 = 0
		self.x2 = self.WIDTH

# drawing 2 images for the base. We are going to move each image to the left
# once one image moves to the end of the screen we cycle to the right of the screen
# the base moves at the same VEL as the pipes at 5

	def move(self):
		self.x1 -= self.VEL
		self.x2 -= self.VEL

		if self.x1 + self.WIDTH < 0:
			self.x1 = self.x2 + self.WIDTH

		if self.x2 + self.WIDTH < 0:
			self.x2 = self.x1 + self.WIDTH

	def draw(self, win):
		win.blit(self.IMG, (self.x1, self.y))
		win.blit(self.IMG, (self.x2, self.y))

##########################################################################

def draw_window(win, bird, pipes, base):   #setting up the window
	win.blit(BG_IMG, (0,0))

	for pipe in pipes:
		pipe.draw(win)

	#text = STAT_FONT.render('Score: ' + str(score), 1, (255, 255, 255))
	#win.blit(text, (WIN_WIDTH - 10 - text.get_width()))

	base.draw(win)

	bird.draw(win)
	pygame.display.update()

##########################################################################

def main():
	bird = Bird(230, 350)
	base = Base(FLOOR)
	pipes = [Pipe(630)]
	win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
	clock = pygame.time.Clock()  #setting the frame rate of the game

	score = 0

	run = True
	while run:  
		clock.tick(50)                           # the Game loop. Runs till you hit something
		for event in pygame.event.get():
			print(event.type)                   # Keeps track of clicks
			if event.type == pygame.QUIT:
				run = False 
				                    # quits game
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_SPACE:
					bird.do_jump()              


		#keys = pygame.key.get_pressed()

		bird.move()

		

		# print(event.type)

		# This loop checks if the bird collides with the pipe, also removes the pipe to the remove list
		# if when the pipe reaches the end of the screen. the 3rd if statement checks if the bird has passed
		# a pipe. If so then we need to add a new pipe. Finnaly we move the pipes.

		add_pipe = False
		remove = []
		for pipe in pipes:
			if pipe.collide(bird):
				pass

			if pipe.x + pipe.PIPE_TOP.get_width() < 0:
				remove.append(pipe)

			if not pipe.passed and pipe.x < bird.x:
				pipe.passed = True
				add_pipe = True

			pipe.move()

		if add_pipe:
			score += 1
			pipes.append(Pipe(630))

		for r in remove:
			pipes.remove(r)

		if bird.y + bird.img.get_height() >= 730:
			pass

		base.move()

		draw_window(win, bird, pipes, base)

	pygame.quit()
	quit()

##########################################################################

main()



