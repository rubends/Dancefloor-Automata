
import pygame
import sys
import random
import numpy as np
import time
from mqtt import mqtt

SIZE = WIDTH, HEIGHT = 500, 500
RECTWIDTH = 10
grid = []

pygame.init()
mqttclient = mqtt("broker.mqttdashboard.com",1883)

class GridRect: #agent
    def __init__(self, x, y):
        self.xLoc = x
        self.yLoc = y
        likes = np.random.uniform(0, 1, 3) #0: Rock, 1: Goa, 2: Blues
        sum = likes[0] + likes[1] + likes[2]
        self.likeRates = [likes[0]/sum, likes[1]/sum, likes[2]/sum] # apart/sum is on 1

        #self.nbLikeRate = np.random.uniform(0, 1, 4)

    def update(self):
        self.genre = self.likeRates.index(max(self.likeRates))

def drawRect(gridRect):
    rect = pygame.Rect(gridRect.xLoc, gridRect.yLoc, RECTWIDTH, RECTWIDTH)
    pygame.draw.rect(screen, (255*gridRect.likeRates[0], 255*gridRect.likeRates[1], 255*gridRect.likeRates[2]), rect)
    

def drawGrid():
    screen.fill((255,255,255))
    pygame.display.set_caption("Cellular Automota")

    for recx in range(lineSize):
        for recy in range(lineSize):
            gridRect = GridRect(recx*RECTWIDTH, recy*RECTWIDTH)
            gridRect.update()
            grid.append(gridRect)
            drawRect(gridRect)

    pygame.display.update()  
   
def startInteractions():
    while 1:
        for rec in range(len(grid)):
            gridRect = grid[rec]
            if rec == 0:
                neighbours = [grid[rec + 1], grid[rec + lineSize]]
            elif rec < 50:
                neighbours = [grid[rec - 1], grid[rec + 1], grid[rec + lineSize]]
            elif rec == (lineSize*lineSize)-1:
                neighbours = [grid[rec - 1], grid[rec - lineSize]]
            elif rec >= (lineSize*lineSize)-lineSize:
                neighbours = [grid[rec - 1], grid[rec + 1], grid[rec - lineSize]]
            else:
                neighbours = [grid[rec - 1], grid[rec + 1], grid[rec - lineSize], grid[rec + lineSize]] #left, right, up, down neighbours

            random.shuffle(neighbours) #otherwise flow direction to the left
            for neighbour in range(len(neighbours)):
                nb = neighbours[neighbour]
                influenceFactor = 0.25*nb.likeRates[nb.genre] + 0.25*random.uniform(0,1)
                for genre in range(3):
                    if genre == nb.genre:
                        newLike = 0.5*gridRect.likeRates[genre] + influenceFactor
                    else:
                        newLike = gridRect.likeRates[genre] - (0.5 * influenceFactor)

                    if newLike > 1:
                        newLike = 1
                    elif newLike < 0:
                        newLike = 0
                    gridRect.likeRates[genre] = newLike

            gridRect.update()
            drawRect(gridRect)

        pygame.display.update()  

def startDjListener():
    mqttclient.connect()
    mqttclient.add_listener_func(onDjMessage)

def onDjMessage(msg):
    msg = msg[2:-1] # "b'Genre'" to "Genre"
    print("Song genre: " + msg)
    if msg == "Rock":
        genre = 0
    elif msg == "Goa":
        genre = 1
    elif msg == "Blues":
        genre = 2
    for rec in range(len(grid)):
        if genre < 3:
            gridRect = grid[rec]
            if gridRect.genre == genre:
                reply = "Like"
            else:
                reply = "Dislike"
        else:
            reply = "Unkown genre"
        mqttclient.publish("dancefloor/dancer/ruben", reply)
    
screen = pygame.display.set_mode(SIZE)
lineSize = int(WIDTH/RECTWIDTH)
startDjListener()
drawGrid()
time.sleep(1)
startInteractions()