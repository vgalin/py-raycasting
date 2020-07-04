import pygame
from math import sin, cos, sqrt
import numpy as np

# python -m cProfile -s tottime thisfile.py > benchmark.txt # to evaluate code performance

map = """\
XXXXXXXXXXXXXXXXX
X        XX     X
XXX   X  XX XX  X
X               X
X     X X   XX  X
X     X         X
X  P            X
XXXXXXXXXXXXXXXXX
"""

map = [list(line) for line in map.split('\n')[:-1]] # map string to 2D array of chars

for line in map:
    print(line)

height = len(map) 
width = len(map[0])

tile_size = 32

player_pos = [0, 0]
for i in range(height):
    for j in range(width):
        if map[i][j] == 'P':
            player_pos = [j*tile_size + tile_size//2 , i*tile_size + tile_size//2]

pygame.init()

screen_width = width*tile_size + 500
screen_height = height*tile_size + 700
screen = pygame.display.set_mode([screen_width, screen_height])

font = pygame.font.Font(None, 30)
clock = pygame.time.Clock()


def draw_sight_orb(x, y):
    x = int(x)
    y = int(y)
    x_map = (x // tile_size)
    y_map = (y // tile_size)

    if y_map <= len(map)-1 and x_map <= len(map[0])-1 and map[y_map][x_map] == 'X':
        pygame.draw.circle(screen, (255, 0, 0), (x, y), 3)
    else:
        pygame.draw.circle(screen, (255, 0, 255), (x, y), 3)

    
# Bresenham's line algorithm https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm
def bresenham(x0, y0, x1, y1):
    ret = []

    dx =  abs(x1-x0)
    sx = 1 if (x0<x1) else -1
    dy = -abs(y1-y0)
    sy = 1 if (y0<y1) else -1
    err = dx+dy
    while (True):

        ret.append((x0, y0))
        if (x0==x1 and y0==y1):
            break
        e2 = 2*err
        if (e2 >= dy):
            err += dy
            x0 += sx
        if (e2 <= dx):
            err += dx
            y0 += sy

    return ret


running = True
while running:  # main loop

    mouse_pos = pygame.mouse.get_pos()
    
    fps = font.render(str(int(clock.get_fps())), True, (255, 255, 255))
    screen.blit(fps, (800, 50))
    pygame.display.flip()
    clock.tick(-1)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                player_pos[0] -= 1 * tile_size
            if event.key == pygame.K_RIGHT:
                player_pos[0] += 1 * tile_size
            if event.key == pygame.K_UP:
                player_pos[1] -= 1 * tile_size
            if event.key == pygame.K_DOWN:
                player_pos[1] += 1 * tile_size
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4: #scroll up
                player_pos[0] -= 2
            if event.button == 5: #scroll down
                player_pos[0] += 2
    

    screen.fill((0, 0, 0)) # clear the screen
    
    # draw a 2D map in the top left corner of the screen
    for i in range(height):
        for j in range(width):
            if map[i][j] == 'X':
                pygame.draw.rect(screen, (255, 255, 255), (j*tile_size, i*tile_size, tile_size, tile_size))

    #draw player
    pygame.draw.circle(screen, (255, 0, 0), player_pos, tile_size//3)
    
    #draw line of sight
    in_map_mouse_pos = list(mouse_pos)
    if mouse_pos[0] > width * tile_size:
        in_map_mouse_pos[0] = width * tile_size
    
    if mouse_pos[1] > height* tile_size:
        in_map_mouse_pos[1] = height * tile_size

    pygame.draw.line(screen, (255, 0, 0), player_pos, in_map_mouse_pos, 2)

    px, py = player_pos
    mx, my = in_map_mouse_pos

    # vision_points = bresenham(px, py, mx, my)
    # for vp in vision_points:
    #     draw_sight_orb(vp[0], vp[1])

    raycast_end_coordinates = []

    # find all end coordinates of the raycasts
    # increase (to 2 for example) the last number of the range for lower quality (but better performance)
    # bring the first two numbers of the range closer to lower Field Of View (better performance))
    for theta in range(-120, 120, 1): 
        
        theta /= 100 # with theta in [-120, 120] : 137.5 degree FOV (1.2 rad * 2)
        # formula from here https://math.stackexchange.com/questions/1687901/how-to-rotate-a-line-segment-around-one-of-the-end-points
        A = np.array([[cos(theta), -sin(theta)], [sin(theta), cos(theta)]])
        B = np.array([[mx - px], [my - py]])
        C = np.array([[px], [py]])
        xy_matrix = np.dot(A, B) + C

        raycast_end_coordinates.append([int(xy_matrix[0][0]), int(xy_matrix[1][0])])

        # vision_points = bresenham(px, py, int(xy_matrix[0][0]), int(xy_matrix[1][0]))
        # for vp in vision_points:
        #     draw_sight_orb(vp[0], vp[1])

    visible_objects = [] 
    # build a list of visible object and their distance
    for ray_end_x, ray_end_y in raycast_end_coordinates:

        real_ray_end = []
        object_is_wall = False
        for ray_pixel_x, ray_pixel_y in bresenham(px, py, ray_end_x, ray_end_y):

            # pixel coordinate to map coordinate
            map_x = ray_pixel_x // tile_size
            map_y = ray_pixel_y // tile_size

            real_ray_end = ray_pixel_x, ray_pixel_y
            if map_x <= width-1 and map_y <= height-1 and map[map_y][map_x] == 'X':
                object_is_wall = True
                break

        draw_sight_orb(real_ray_end[0], real_ray_end[1]) # draw an orb when a ray hits an object
        distance_to_object = sqrt((real_ray_end[0] - px)**2 + (real_ray_end[1] - py)**2)
        visible_objects.append((distance_to_object, object_is_wall))

    # draw all the objects (walls and voids) in the visible_objects list
    # their size is depending on their distance from the player
    for i, (object_distance, object_is_wall) in enumerate(visible_objects):
        color = (0, 0, 0)
        if object_is_wall:
            color_hexa = int(50 * (255/(object_distance+1))) # the farther the object the grayer
            color_hexa = 0 if color_hexa < 0 else 255 if color_hexa > 255 else color_hexa
            color = (color_hexa, color_hexa, color_hexa)

        # a few magic numbers from here, I just tweaked them until things displayed properly
        wall_height = int(40 * (255/(object_distance+1))) # the nearer the object the taller

        pygame.draw.rect(screen, color,
            (i*(screen_width / len(visible_objects))//1.2,
            600 - wall_height//2,
            screen_width / len(visible_objects),
            wall_height)
        )
        # pygame.draw.circle(screen, color, (i*16, 270), 3) # debug orbs, an alternative to walls

    pygame.display.flip()
pygame.quit()