# pyinstaller code/main.py code/camera.py code/game_data.py code/player.py code/level.py code/spawn.py code/support.py code/tiles.py code/trigger.py --onefile --noconsole
# Raycaster vid: https://www.youtube.com/watch?v=O_J8jRq6lBw
# Git original code: https://github.com/Gpopcorn/raycasting/blob/main/raycasting.pyw

# screen resizing tut, dafluffypotato: https://www.youtube.com/watch?v=edJZOQwrMKw

import pygame, sys, math, time
from text import Font
from game_data import *
from support import resource_path

# General setup
pygame.mixer.pre_init(44100, 16, 2, 4096)
pygame.init()
clock = pygame.time.Clock()
game_speed = 60

# window and screen Setup ----- The window is the real pygame window. The screen is the surface that everything is
# placed on and then resized to blit on the window. Allowing larger pixels (art pixel = game pixel)
# https://stackoverflow.com/questions/54040397/pygame-rescale-pixel-size

precision = 0.01
scaling_factor = 1  # how much the screen is scaled up before bliting on display

# https://www.pygame.org/docs/ref/display.html#pygame.display.set_mode
# https://www.reddit.com/r/pygame/comments/r943bn/game_stuttering/
# vsync only works with scaled flag. Scaled flag will only work in combination with certain other flags.
# although resizeable flag is present, window can not be resized, only fullscreened with vsync still on
# vsync prevents screen tearing (multiple frames displayed at the same time creating a shuddering wave)
# screen dimensions are cast to int to prevent float values being passed (-1 is specific to this game getting screen multiple of 16)
window = pygame.display.set_mode((int(screen_width * scaling_factor) - 1, int(screen_height * scaling_factor)), pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.SCALED, vsync=True)

# all pixel values in game logic should be based on the screen!!!! NO .display FUNCTIONS!!!!!
screen = pygame.Surface((screen_width, screen_height))  # the display surface, re-scaled and blit to the window
screen_rect = screen.get_rect()  # used for camera scroll boundaries

# caption and icon
pygame.display.set_caption('Raycasting Test')
# TODO icon
#pygame.display.set_icon(pygame.image.load(resource_path('../icon/app_icon.png')))

# controller
pygame.joystick.init()
joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
print(f"joy {len(joysticks)}")
for joystick in joysticks:
    joystick.init()

# font
font = Font(fonts['small_font'], 'white')

# asset load
sky = pygame.image.load(resource_path('../assets/sky.jpeg'))


def main_menu():
    game()


def movement(pos, rot_r, vertical_pan, dt):
    # TODO add velocity for movement
    rot_sensitivity = math.pi / 60  # change what pi is divided by to speed up or slow down

    pan_sensitivity = 20
    pan_down_limit = -400
    pan_up_limit = 500

    norm_speed = 0.03
    sprint_speed = 0.06
    move_speed = norm_speed

    keys = pygame.key.get_pressed()

    # rotation
    if keys[pygame.K_RIGHT]:
        rot_r += rot_sensitivity * dt
    if keys[pygame.K_LEFT]:
        rot_r -= rot_sensitivity * dt

    # pan up/down
    if keys[pygame.K_UP]:
        vertical_pan += pan_sensitivity
    if keys[pygame.K_DOWN]:
        vertical_pan -= pan_sensitivity

    if vertical_pan > pan_up_limit:
        vertical_pan = pan_up_limit
    elif vertical_pan < pan_down_limit:
        vertical_pan = pan_down_limit

    # sprint
    if keys[pygame.K_LSHIFT]:
        move_speed = sprint_speed
    else:
        move_speed = norm_speed

    # directional movement
    x, y = pos
    if keys[pygame.K_w]:
        x, y = (x + move_speed * math.cos(rot_r) * dt, y + move_speed * math.sin(rot_r) * dt)
    if keys[pygame.K_s]:
        x, y = (x - move_speed * math.cos(rot_r) * dt, y - move_speed * math.sin(rot_r) * dt)
    if keys[pygame.K_a]:
        x, y = (x + move_speed * math.cos(rot_r-math.pi/2) * dt, y + move_speed * math.sin(rot_r-math.pi/2) * dt)
    if keys[pygame.K_d]:
        x, y = (x - move_speed * math.cos(rot_r-math.pi/2) * dt, y - move_speed * math.sin(rot_r-math.pi/2) * dt)

    pos = (x, y)
    return pos, rot_r, vertical_pan


def collisions(pos, player_radius, map):
    for y in range(len(map)):
        for x in range(y):
            if pos == y:
                pos -= player_radius


def game():
    click = False

    map = [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
           [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
           [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
           [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
           [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1],
           [1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1],
           [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
           [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
           [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
           [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]

    # player
    fov = 80
    pos = (2, 2)
    player_radius = 10
    rot_r = 0  # rotation in radians
    vertical_pan = 0  # player look up/down value

    max_render_dist = 1000
    shadow_amount = 2  # lower numbers increase shadows

    # dt
    previous_time = time.time()
    dt = (time.time() - previous_time) * 60
    previous_time = time.time()
    fps = clock.get_fps()

    running = True
    while running:
        # delta time  https://www.youtube.com/watch?v=OmkAUzvwsDk
        dt = (time.time() - previous_time) * 60  # keeps units such that movement += 1 * dt means add 1px if at 60fps
        previous_time = time.time()
        fps = clock.get_fps()

        # x and y mouse pos
        mx, my = pygame.mouse.get_pos()

        # -- Input --
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_COMMA or event.key == pygame.K_ESCAPE:
                    running = False
                    pygame.quit()
                    sys.exit()
                # TODO Test only, remove
                elif event.key == pygame.K_x:
                    global game_speed
                    if game_speed == 60:
                        game_speed = 6
                    else:
                        game_speed = 60
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == controller_map['left_analog_press']:
                    running = False
                    pygame.quit()
                    sys.exit()

        pos, rot_r, vertical_pan = movement(pos, rot_r, vertical_pan, dt)

        # -- Checks --
        collisions(pos, player_radius, map)

        # -- Update --
        screen.fill((15, 0, 34))

        for vslice in range(fov):  # goes through vertical slices based on size of pov
            x, y = pos
            rot_d = rot_r + math.radians(vslice - fov/2)  # angle (radians) of vertical slice (based on player rotation)
            sin, cos = (precision*math.sin(rot_d), precision*math.cos(rot_d))
            #                          1                          0

            distance = 0  # increases as distance of vslice from player increases (used for height of rendered line creating depth)
            # raycasting
            # casts until hit or until max render distance exceeded
            for i in range(max_render_dist):
                # ----- GOOD TO HERE ----
                x, y = (x + cos, y + sin)
                distance += 1
                if map[int(x)][int(y)]:
                    shadow = distance  # shadow increases as distance increases
                    distance = distance * math.cos(math.radians(vslice-fov/2))  # <-- prevents fisheyeing
                    height = (10/distance * 2500)  # *arbitrary numbers*???
                    break

            # used for shading
            shadow /= shadow_amount
            if shadow > 255:
                shadow = 255
            # -------------------------
            # render vertical slice
            wheight = window.get_height()
            wwidth = window.get_width()
            pygame.draw.line(screen, (255 - shadow, 255 - shadow, 255 - shadow),  # colour and shading
                             (vslice*(wwidth/fov), wheight/2 + vertical_pan + height),  # pos 1 (2 is arbitrary)
                             (vslice*(wwidth/fov), wheight/3 + vertical_pan - height),  # pos 2 (3 is arbitrary)
                             int(wwidth/fov))  # line width based on screen width and fov

        window.blit(pygame.transform.scale(screen, window.get_rect().size), (0, 0))  # scale screen to window

        # -- Render --
        pygame.display.update()
        clock.tick(game_speed)


main_menu()
