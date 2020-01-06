import pygame
import neat
import time
import os
import random
import graphviz
pygame.font.init()

##########################################################################

# Constants including all imgs for animation

WIN_WIDTH = 500
WIN_HEIGHT = 800
FLOOR = 730
STAT_FONT = pygame.font.SysFont('comicsans', 50)

pygame.display.set_caption('Flappy Bird')

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join('flappy-imgs', 'bird1.png'))), pygame.transform.scale2x(pygame.image.load(
    os.path.join('flappy-imgs', 'bird2.png'))), pygame.transform.scale2x(pygame.image.load(os.path.join('flappy-imgs', 'bird3.png')))]
PIPE_IMG = pygame.transform.scale2x(
    pygame.image.load(os.path.join('flappy-imgs', 'pipe.png')))
BASE_IMG = pygame.transform.scale2x(
    pygame.image.load(os.path.join('flappy-imgs', 'base.png')))
BG_IMG = pygame.transform.scale2x(
    pygame.image.load(os.path.join('flappy-imgs', 'bg.png')))

STAT_FONT = pygame.font.SysFont('comicsans', 50)

##########################################################################

# Bird class


class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25  # how much the bird will tilt during animation
    ROT_VEL = 20  # how much the bird will rotate each frame
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0            #
        self.tick_count = 0  # physics of the bird...
        self.vel = 0  # velocity
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

# The orgin is top left of the screen. meaning up is negative, down is positive

    def do_jump(self):
        self.vel = -10.5
        self.tick_count = 0  # keeping track of when we last jumped
        self.height = self.y

    def move(self):
        self.tick_count += 1  # keeping track of how many times you moved

        # displacement,
        # **2 is expotential.
        displacement = self.vel * (self.tick_count) + \
            0.5 * (3) * (self.tick_count)**2
        # -10.5 + 1.5 = -9 pixles
        # if not (self.jump):
        if displacement >= 16:  # Terminal velocity
            displacement = (displacement / abs(displacement)) * 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:  # tilt up
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:  # tilt down
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

    def draw(self, win):  # animation
        self.img_count += 1

        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        # rotation an image around it's center
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(
            center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    # collition with bird and objects
    def get_mask(self):
        return pygame.mask.from_surface(self.img)  # look up pygame.mask

##########################################################################


class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(
            PIPE_IMG, False, True)  # flips pipe for top pipe
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False  # for collitions
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

        # offsets tells how far away the 2 top left hand corners are
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # bottom pipe colliton point
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        # top pipe colliton point
        t_point = bird_mask.overlap(top_mask, top_offset)

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


def draw_window(win, birds, pipes, base, score):  # setting up the window
    win.blit(BG_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render('Score: ' + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    base.draw(win)

    for bird in birds:
        bird.draw(win)

    pygame.display.update()

##########################################################################

# Inputs <-- Bird Y, Top Pipe, Bottom Pipe
# Outpus <-- Jump or not
# Activation Function <-- TanH (-1, [don't jump] 0, [jump 1]) (hyperbolic Tangent function)
# Population Size <-- 100
# Fitness Function <-- Every frame advancement =  + 1 fitness
# Max genertaions <-- 30


# acts as our main function to allocate fitness with genomes (nural networks)
def fitness(genomes, config):
    nets = []  # a list of each nural network
    ge = []  # keeping track of where the birds are
    birds = []

    # setting up a nural network for each bird genome
    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()  # setting the frame rate of the game

    score = 0

    run = True
    while run and len(birds) > 0:
        # the Game loop. Runs till you hit something
        clock.tick(30)
        for event in pygame.event.get():
                                                 # Keeps track of clicks
            if event.type == pygame.QUIT:        # quits game
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            # if any bird is past the first pipe change that pipe to in the list
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break

        # having the birds jump & rewarding them each second they're alive
        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            # createing the output from how close the bird is from the top of the pipe and bottom of the pipe

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.do_jump()

        # 	if event.type == pygame.KEYDOWN:
        # 		if event.key == pygame.K_SPACE:
        # 			bird.do_jump()

        # bird.move()

        # This loop checks if the bird collides with the pipe, also removes the pipe to the remove list
        # if when the pipe reaches the end of the screen. the 3rd if statement checks if the bird has passed
        # a pipe. If so then we need to add a new pipe. Finnaly we move the pipes.

        add_pipe = False
        remove = []
        for pipe in pipes:
            pipe.move()

            for x, bird in enumerate(birds):
                # if a bird dies, its fully removed from the network
                if pipe.collide(bird):
                    # lowering the fitness if a bird hits a pipe
                    ge[x].fitness -= 1
                    birds.remove(bird)
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                remove.append(pipe)


        if add_pipe:
            score += 1
            for g in ge:  # adding fitness if a bird makes it through a pipe
                g.fitness += 5

            pipes.append(Pipe(630))

        for r in remove:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            # if bird hits the floor or hits celing remove it
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()

        draw_window(win, birds, pipes, base, score)

##########################################################################


def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,  # pulls configurations from NEAT config file
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    p = neat.Population(config)  # creates first population

    p.add_reporter(neat.StdOutReporter(True))  # sets up a reporter in terminal
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # setting fitness function with how many generations we're going to run
    winner = p.run(fitness, 50)


if __name__ == "__main__":  # opens and reads the neat config file from local directory
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'NEAT-Configuration.txt')
    run(config_path)
