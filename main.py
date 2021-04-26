import random
import pygame as pg
import math	
import numpy as np

pg.init()

FPS = 20
clock = pg.time.Clock()

pg.mouse.set_visible(False)

SF = 2
width, height = 640 * SF, 360 * SF
screen = pg.display.set_mode((width, height))

black = (0, 0, 0)
gray = (55, 55, 55)
white = (255, 255, 255)
red = (255, 0, 0)
blue = (0, 255, 255)
green = (0, 255, 0)

color = {
	0: white,
}

class Boundary:
	def __init__(self, position, color, size=1):
		self.color = color
		self.size = size * SF
		
		x1, y1 = position[0]
		x2, y2 = position[1]
		x1 *= SF
		y1 *= SF
		x2 *= SF
		y2 *= SF
		if x1 < x2:
			self.position = ((x1, y1), (x2, y2))
		if x1 > x2:
			self.position = ((x2, y2), (x1, y1))

	def Draw(self):
		pg.draw.aaline(screen, self.color, self.position[0], self.position[1], 1)


class Point:
	def __init__(self, position, color, rayLength=100, size=1, numOfRays=360, speed=1, mouseMovement=False):
		self.position = (position[0] * SF, position[1] * SF)
		self.color = color
		self.size = size * SF
		self.numOfRays = numOfRays
		self.rayLength = rayLength * 2
		self.rays = []
		self.speed = speed
		self.newPosition = self.position
		self.direction = [0, 0]
		self.velocity = 0
		self.mouseMovement = mouseMovement

		self.CreateRays()

	def Draw(self):
		pg.draw.circle(screen, self.color, self.position, self.size)

		for ray in self.rays:
			ray.Update(self.position, self)

	def CreateRays(self):
		directions = []

		for x in range(-self.numOfRays, self.numOfRays):
			for y in range(-self.numOfRays, self.numOfRays):
				directions.append((x * self.rayLength, y * self.rayLength))

		for i in range(len(directions)):
			self.rays.append(Ray(self.position, self.color, self, directions[i]))

	def Move(self):
		if self.mouseMovement:
			self.position = pg.mouse.get_pos()
		else:
			x, y = self.position

			x += self.speed * self.direction[0]
			y += self.speed * self.direction[1]

			self.position = (x, y)


class Ray:
	def __init__(self, startPos, color, point, direction):
		self.startPos = startPos
		self.endPos = startPos
		self.color = color
		self.direction = direction
		self.draw = False
		self.drawColor = color

	def Update(self, position, point):
		self.Cast(position)
		self.Collide(point)
		self.Draw()

	def Cast(self, startPos):
		self.startPos = startPos
		self.endPos = (self.startPos[0] + self.direction[0], self.startPos[1] + self.direction[1])

	def Collide(self, point):
		self.draw = False
		for bound in allBounds:
			x1, y1 = self.startPos
			x2, y2 = self.endPos
			x3, y3 = bound.position[0]
			x4, y4 = bound.position[1]

			den = ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))

			if den != 0:
				t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den

				if 0 <= t <= 1:
					L1 = ((x1 + t * (x2 - x1)), (y1 + t * (y2 - y1)))
					if (L1 > (x3, y3)):
						if (L1 < (x4, y4)):
							self.endPos = L1
							self.draw = True
							self.drawColor = bound.color

	def Draw(self):
		# pg.draw.aaline(screen, self.color, self.startPos, self.endPos)

		if self.draw:
			pg.draw.circle(screen, self.drawColor, self.endPos, 1)


def MovePoint(event, point):
	if event.type == pg.KEYDOWN:
		if event.key == pg.K_a:
			point.direction[0] = -1
		if event.key == pg.K_d:
			point.direction[0] = 1

		if event.key == pg.K_w:
			point.direction[1] = -1
		if event.key == pg.K_s:
			point.direction[1] = 1

	if event.type == pg.KEYUP:
		if event.key == pg.K_a:
			if point.direction[0] == -1: 
				point.direction[0] = 0
		if event.key == pg.K_d:
			if point.direction[0] == 1: 
				point.direction[0] = 0

		if event.key == pg.K_w:
			if point.direction[1] == -1: 
				point.direction[1] = 0
		if event.key == pg.K_s:
			if point.direction[1] == 1: 
				point.direction[1] = 0


def MakeBoundaries():
	global allBounds
	bounds = []
	numOfBoundries = 20

	for i in range(numOfBoundries):
		x1 = random.randint(0, width // SF)
		y1 = random.randint(0, width // SF)
		x2 = random.randint(0, height // SF)
		y2 = random.randint(0, height // SF) 
		col = random.randint(0, len(color) - 1)
		bounds.append(Boundary(((x1, y1), (x2, y2)), color[col]))

	allBounds = np.array(bounds)


point = Point(((width // SF) // 2, (height // SF) // 2), white, rayLength=2, numOfRays=30, mouseMovement=True)


MakeBoundaries()
running = True
drawBounds = False
while running:
	clock.tick(FPS)
	screen.fill(gray)

	for event in pg.event.get():
		if event.type == pg.QUIT:
			running = False	
		if event.type == pg.KEYDOWN:
			if event.key == pg.K_ESCAPE:
				running = False

			if event.key == pg.K_SPACE:
				drawBounds = not drawBounds
			if event.key == pg.K_r:
				MakeBoundaries()

		MovePoint(event, point)

	if drawBounds:
		for bound in allBounds:
			bound.Draw()

	point.Move()
	point.Draw()

	pg.display.flip()