import random
import pygame as pg
from pygame import gfxdraw
import math	
import numpy as np
import os
from os import listdir
from os.path import isfile, join
import json

pg.init()

FPS = 20
clock = pg.time.Clock()

SF = 2
width, height = 640 * SF, 360 * SF
screen = pg.display.set_mode((width, height))

black = (0, 0, 0)
gray = (55, 55, 55)
lightGray = (205, 205, 205)
white = (255, 255, 255)
red = (255, 0, 0)
blue = (0, 255, 255)
green = (0, 255, 0)

Font = pg.font.SysFont("arial", 8 * SF)

allBounds = np.array([])
allButtons = []
allInputBoxs = []
allLabels = []
loadObjs = []

rootDirectory = os.getcwd()
saveFolderName = "Maps"
namePrefix = "Map-"

loadScreen = True

color = {
	0: white, 
}

allowedKeys = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", " "]


def ScaleImage(imagePath, imageScale, newImagePath):
	image = Image.open(imagePath)
	image = image.resize((imageScale[0], imageScale[1]))
	image.save(newImagePath)


def DrawRectOutline(surface, color, rect, width=1):
	x, y, w, h = rect
	width = max(width, 1)  # Draw at least one rect.
	width = min(min(width, w//2), h//2)  # Don't overdraw.

	# This draws several smaller outlines inside the first outline
	# Invert the direction if it should grow outwards.
	for i in range(int(width)):
		pg.gfxdraw.rectangle(surface, (x+i, y+i, w-i*2, h-i*2), color)


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
		if x1 >= x2:
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


class HoldButton:
	def __init__(self, surface, rect, buttonType, colorData, textData, actionData=[], lists=[allButtons], extraText=[], extraData=[], imageData=[None]):
		"""
		Parameters: 
			buttonType: tuple of gameState type and button action
			colorData: tuple of active color and inactive color
			textData: tuple of text and text color
			actionData: list of any additional button action data
			lists: list of lists to add self too
			extraText: list of tuples containing the text and the rect
			imageData: list of image path and scaled image path
		"""
		self.surface = surface
		self.originalRect = rect
		self.rect = pg.Rect(rect[0] * SF, rect[1] * SF, rect[2] * SF, rect[3] * SF)
		self.action = buttonType
		self.active = False
		self.activeColor = colorData[0]
		self.inactiveColor = colorData[1]
		self.currentColor = self.inactiveColor
		self.text = textData[0]
		self.textColor = textData[1]
		self.textSurface = Font.render(self.text, True, self.textColor)
		self.extraText = extraText
		self.extraData = extraData
		self.actionData = actionData
		for listToAppend in lists:
			listToAppend.append(self)
		
		self.imageData = imageData
		if self.imageData[0] != None:
			self.hasImage = True
		else:
			self.hasImage = False

		self.Rescale()

	# rescale all elements
	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)
		self.extraTextSurfaces = [] 
		for textData in self.extraText:
			textSurface = Font.render(str(textData[0]), True, self.textColor)
			self.extraTextSurfaces.append((textSurface, ((textData[1][0] * SF) - textSurface.get_width() // 2, (textData[1][1] * SF) - textSurface.get_height() // 2)))
		try:
			if self.hasImage:
				ScaleImage(self.imageData[0], (self.rect.w, self.rect.h), self.imageData[1])
				self.image = pg.image.load(self.imageData[1])
				self.image.convert()
		except:
			print("{} has no image".format(self.action))
			self.hasImage = False

	def Draw(self):
		if not self.hasImage:
			pg.draw.rect(self.surface, self.currentColor, self.rect)
			self.surface.blit(self.textSurface, self.rect)
		else:
			self.surface.blit(self.image, self.rect)

		for textSurfaceData in self.extraTextSurfaces:
			self.surface.blit(textSurfaceData[0], textSurfaceData[1])

	def HandleEvent(self, event):
		# check for left mouse down
		if event.type == pg.MOUSEBUTTONDOWN:
			if event.button == 1:
				if self.rect.collidepoint(pg.mouse.get_pos()):
					self.active = True

		# check for left mouse up
		if event.type == pg.MOUSEBUTTONUP:
			if event.button == 1:
				self.active = False

		# change color
		if self.active:
			self.currentColor = self.activeColor
		else:
			self.currentColor = self.inactiveColor

	def ChangeRect(self, newRect):
		self.rect = pg.Rect(newRect)
		self.extraTextSurfaces = [] 
		for textData in self.extraText:
			textSurface = Font.render(str(textData[0]), True, self.textColor)
			self.extraTextSurfaces.append((textSurface, ((self.rect.x + self.rect.w // 2) - textSurface.get_width() // 2, (self.rect.y + self.rect.h // 2) - textSurface.get_height() // 2)))

	def UpdateText(self, text):
		self.textSurface = Font.render(str(text), True, self.textColor)

	def UpdateExtraText(self, extraText):
		self.extraTextSurfaces = []
		for textData in extraText:
			textSurface = Font.render(str(textData[0]), True, self.textColor)
			self.extraTextSurfaces.append((textSurface, ((textData[1][0] * SF) - textSurface.get_width() // 2, (textData[1][1] * SF) - textSurface.get_height() // 2)))


class InputBox:
	def __init__(self, rect, displayText='', text="", inactiveColor=lightGray, activeColor=white, characterLimit=3, lists=[allInputBoxs]):
		self.surface = screen
		self.rect = pg.Rect(rect[0] * SF, rect[1] * SF, rect[2] * SF, rect[3] * SF)
		self.inactiveColor = inactiveColor
		self.activeColor = activeColor
		self.currentColor = self.inactiveColor
		self.displayText = displayText	
		self.startText = text
		self.text = self.startText
		self.characterLimit = characterLimit
		self.displayTextSurface = Font.render(self.displayText, True, self.currentColor)
		self.textSurface = Font.render(self.text, True, self.currentColor)
		self.active = False

		for listToAppend in lists:
			listToAppend.append(self)

	def Draw(self):
		self.textSurface = Font.render(self.text, True, self.currentColor)
		self.surface.blit(self.displayTextSurface, (self.rect.x+2.5 * SF, self.rect.y+2.5 * SF))
		self.surface.blit(self.textSurface, (self.rect.x+self.displayTextSurface.get_width()+5 * SF, self.rect.y+2.5 * SF))
		pg.draw.rect(self.surface, self.currentColor, self.rect, 2)

	def HandleEvent(self, event):
		if event.type == pg.MOUSEBUTTONUP:
			if event.button == 1:
				# If the user clicked on the input box rect.
				if self.rect.collidepoint(pg.mouse.get_pos()):
					# Toggle the active variable.
					self.active = not self.active
				else:
					self.active = False
				# Change the current color of the input box.
				if self.active:
					self.currentColor = self.activeColor
				else:
					self.currentColor = self.inactiveColor
				# change display text color
				self.displayTextSurface = Font.render(self.displayText, True, self.currentColor)

		# get key inputs 
		if event.type == pg.KEYDOWN:
			if self.active:
				if event.key == pg.K_BACKSPACE:
					self.text = self.text[:-1]
				else:
					self.FilterText(event.unicode)
				# make empty text = 0
				if self.text == "":
					self.text = self.startText
				# Re-render the text.
				self.textSurface = Font.render(self.text, True, self.currentColor)

	def FilterText(self, key):
		# check if new text will surpass characterLimit
		if len(self.text) + 1 <= self.characterLimit:
			# clear the box when user starts typing
			if self.text == "0":
				self.text = ""
			# check if key is within allowed keys and add it to the text
			if key in allowedKeys:
				self.text += key


class Label:
	def __init__(self, rect, text="", fontName="arial", fontSize=8, color=lightGray, lists=[allLabels]):
		self.surface = screen
		self.rect = pg.Rect(rect[0] * SF, rect[1] * SF, rect[2] * SF, rect[3] * SF)
		self.text = text
		self.color = color
		self.font = pg.font.SysFont(fontName, fontSize * SF)
		self.textSurface = self.font.render(self.text, True, self.color)
		width = max(25 * SF, self.textSurface.get_width()+5*SF)
		height = max(13.5 * SF, self.textSurface.get_height()+5*SF)
		self.rect.w = width
		self.rect.h = height

		for listToAppend in lists:
			listToAppend.append(self)

	def Draw(self, width=3):
		self.surface.blit(self.textSurface, (self.rect.x + 2.5 * SF, self.rect.y + 2.5 * SF))
		DrawRectOutline(self.surface, self.color, self.rect, width)

	def UpdateText(self, newText):
		self.text = newText
		self.textSurface = self.font.render(self.text, True, self.color)
		# change with and height for text
		width = max(25 * SF, self.textSurface.get_width()+5*SF)
		height = max(13.5 * SF, self.textSurface.get_height()+5*SF)
		self.rect.w = width
		self.rect.h = height


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


def CreateLoadingScreen():
	global loadLabel, loadName, loadSave, newSave
	loadLabel = Label((((width // SF) // 2) - 150, ((height // SF) // 2) - 70, 100, 20), "Choose map to load", fontSize=32, lists=[loadObjs])
	loadName = InputBox((((width // SF) // 2) - 100, ((height // SF) // 2) - 10, 200, 20), "Load name: ", characterLimit=30, lists=[loadObjs, allInputBoxs])
	loadSave = HoldButton(screen, (((width // SF) // 2) - 75, ((height // SF) // 2) + 20, 150, 40), "load save", (lightGray, lightGray), ("Load Save", black), lists=[loadObjs, allButtons])
	newSave = HoldButton(screen, (((width // SF) // 2) - 75, ((height // SF) // 2) + 70, 150, 40), "new save", (lightGray, lightGray), ("New Save", black), lists=[loadObjs, allButtons])


def Load(loadName):
	global allBounds
	fileName = namePrefix + loadName + ".json"
	os.chdir(saveFolderName)
	with open(fileName, "r") as loadFile:
		loadFileData = json.load(loadFile)
		loadFile.close()
	os.chdir(rootDirectory)

	bounds = []
	for i, line in enumerate(loadFileData["positions"]):
		bounds.append(Boundary(line, loadFileData["colors"][i]))

	allBounds = np.array(bounds)


def CheckLoad(loadName):
	loadCheck = False
	try:
		if loadName != "":
			filesInDirectory = [file for file in listdir(rootDirectory)]
			saveFolderExists = False

			for file in filesInDirectory:
				if saveFolderName in file:
					saveFolderExists = True

			os.chdir(saveFolderName)

			currentWorkingDirectory = os.getcwd()
			directory = [file for file in listdir(currentWorkingDirectory)]

			for file in directory:
				if loadName in file:
					loadCheck = True

			os.chdir(rootDirectory)
	except:
		pass

	return loadCheck


def ButtonPress(event):
	global loadObjs, loadScreen, saveScreen, saveObjs
	loadingName = loadName.text
	for button in allButtons:
		button.HandleEvent(event)

		if button.active:
			if button.action == "new save":
				allButtons.remove(button)
				loadScreen = False
				for obj in loadObjs:
					if obj in allInputBoxs:
						allInputBoxs.remove(obj)
					if obj in allButtons:
						allButtons.remove(obj)
				loadObjs = []
				MakeBoundaries()

			if button.action == "load save":
				loadCheck = CheckLoad(loadingName)
				if loadCheck:
					loadScreen = False
					allButtons.remove(button)
					for obj in loadObjs:
						if obj in allInputBoxs:
							allInputBoxs.remove(obj)
						if obj in allButtons:
							allButtons.remove(obj)
					loadObjs = []
					Load(loadingName)

point = Point(((width // SF) // 2, (height // SF) // 2), white, rayLength=2, numOfRays=30, mouseMovement=True)

CreateLoadingScreen()
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

			if not loadScreen:
				if event.key == pg.K_SPACE:
					drawBounds = not drawBounds

		ButtonPress(event)
	
		for inputBox in allInputBoxs:
			inputBox.HandleEvent(event)
		
		if not loadScreen:
			pg.mouse.set_visible(False)
			MovePoint(event, point)

	if drawBounds:
		for bound in allBounds:
			bound.Draw()

	for button in allButtons:
		button.Draw()

	for inputBox in allInputBoxs:
		inputBox.Draw()

	for label in allLabels:
		label.Draw()

	for obj in loadObjs:
		obj.Draw() 

	if not loadScreen:
		point.Move()
		point.Draw()

	pg.display.flip()