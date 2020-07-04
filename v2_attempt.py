import pygame
from math import sin, cos, sqrt
from dataclasses import dataclass
import numpy as np

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

@dataclass
class Point():
    x: int = 0
    y: int = 0

    @property
    def coord(self):
        return (self.x, self.y)

map = [list(line) for line in map.split('\n')[:-1]]

for line in map:
    print(line)

height = len(map) 
width = len(map[0])

tile_size = 32

player = Point()

for i in range(height):
    for j in range(width):
        if map[i][j] == 'P':
            player.x = j*tile_size + tile_size//2
            player.y = i*tile_size + tile_size//2

pygame.init()

screen_width = width*tile_size + 500
screen_height = height*tile_size + 700

screen = pygame.display.set_mode([screen_width, screen_height])


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

font = pygame.font.Font(None, 30)
clock = pygame.time.Clock()

running = True
while running:

    mouse = Point(*pygame.mouse.get_pos())
    

    fps = font.render(str(int(clock.get_fps())), True, pygame.Color('white'))
    screen.blit(fps, (800, 100))
    pygame.display.flip()
    clock.tick(-1)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                player.x -= 1 * tile_size
            if event.key == pygame.K_RIGHT:
                player.x += 1 * tile_size
            if event.key == pygame.K_UP:
                player.y -= 1 * tile_size
            if event.key == pygame.K_DOWN:
                player.y += 1 * tile_size
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4: #scroll up
                player.x -= 2
            if event.button == 5: #scroll down
                player.x += 2
    

    screen.fill((0, 0, 0)) # clear the screen
    
    # draw a 2D map in the top left corner of the screen
    for i in range(height):
        for j in range(width):
            if map[i][j] == 'X':
                pygame.draw.rect(screen, (255, 255, 255), (j*tile_size, i*tile_size, tile_size, tile_size))

    #draw player
    pygame.draw.circle(screen, (255, 0, 0), player.coord, tile_size//3)
    
    #draw line of sight
    pygame.draw.line(screen, (255, 0, 0), player.coord, mouse.coord, 2)

    raycast_end_coordinates = []

    # find all target raycasting coordinates
    for theta in range(-120, 120, 2):
        #https://math.stackexchange.com/questions/1687901/how-to-rotate-a-line-segment-around-one-of-the-end-points

        theta /= 100

        A = np.array([[cos(theta), -sin(theta)], [sin(theta), cos(theta)]])
        B = np.array([[mouse.x - player.x], [mouse.y - player.y]])
        C = np.array([[player.x], [player.y]])
        xy_matrix = np.dot(A, B) + C

        raycast_end_coordinates.append([int(xy_matrix[0][0]), int(xy_matrix[1][0])])

        # vision_points = bresenham(player.x, player.y, int(xy_matrix[0][0]), int(xy_matrix[1][0]))
        # for vp in vision_points:
        #     draw_sight_orb(vp[0], vp[1])

    vision_list = []
    for ray_end_coordinates in raycast_end_coordinates:

        real_ray_end = Point()
        ray_end_is_wall = False
        for ray_pixel_x, ray_pixel_y in bresenham(*player.coord, *ray_end_coordinates):

            # pixel coordinate to map coordinate
            on_map = Point(ray_pixel_x // tile_size, ray_pixel_y // tile_size)

            real_ray_end = Point(ray_pixel_x, ray_pixel_y)
            if on_map.x <= width-1 and on_map.y <= height-1 and map[on_map.y][on_map.x] == 'X':
                ray_end_is_wall = True
                break

        draw_sight_orb(real_ray_end.x, real_ray_end.y)

        distance_to_ray_end = sqrt((real_ray_end.x - player.x)**2 + (real_ray_end.y - player.y)**2)

        vision_list.append((distance_to_ray_end, ray_end_is_wall))
        # pygame.draw.rect(screen, (255, 255, 255), (j*tile_size, i*tile_size, tile_size, tile_size)

    for i, (object_distance, object_is_wall) in enumerate(vision_list):
        color = (0, 0, 0)
        if object_is_wall:
            color_hexa = int(50 * (255/(object_distance+1)))
            color_hexa = 0 if color_hexa < 0 else 255 if color_hexa > 255 else color_hexa
            color = (color_hexa, color_hexa, color_hexa)

        wall_height = int(
            40 * (255/(object_distance+1))
        )

        pygame.draw.rect(screen, color,
            (i*(screen_width / len(vision_list))//1.2,
            600 - wall_height//2,
            screen_width / len(vision_list),
            wall_height)
        )


        pygame.draw.circle(screen, color, (i*16, 270), 3)


    pygame.display.flip()




pygame.quit()