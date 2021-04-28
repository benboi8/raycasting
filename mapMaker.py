import random
import pygame as pg
from pygame import gfxdraw
import math	
import numpy as np
from PIL import Image
import os
import sys
from os import listdir
from os.path import isfile, join
import json

pg.init()

FPS = 60
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

allBounds = np.array([])
allButtons = []
allBuildMenuObj = []
allInputBoxs = []
allLabels = []
loadObjs = []
saveObjs = []

firstPoint, lastPoint = (-1, -1), (-1, -1)

Font = pg.font.SysFont("arial", 8 * SF)

rootDirectory = os.getcwd()
saveFolderName = "Maps"
savesDirectoryCreated = False
namePrefix = "Map-"

loadScreen = True
saveScreen = False
running = True

destroyMode = False
destroyPointStart, destroyPointEnd = (-1, -1), (-1, -1)
destroyedBounds = []

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
		elif x1 > x2:
			self.position = ((x2, y2), (x1, y1))
		else:
			self.position = ((x1, y1), (x2, y2))

	def __del__(self):
		print("bound destroyed")

	def Draw(self):
		pg.draw.aaline(screen, self.color, self.position[0], self.position[1], 1)

	def Destroy(self):
		global allBounds
		if self in allBounds:
			bounds = []
			for bound in allBounds:
				bounds.append(bound)
			bounds.remove(self)
			allBounds = np.array(bounds)

		if self in destroyedBounds:
			destroyedBounds.remove(self)
		del self


class ToggleButton:
	def __init__(self, surface, rect, buttonType, colorData, textData, actionData=[], lists=[allButtons], extraText=[], imageData=[None]):
		"""
		Parameters: 
			buttonType: button action
			colorData: tuple of active color and inactive color
			textData: tuple of text and text color
			actionData: list of any additional button action data
			lists: list of lists to add self too
			extraText: list of tuples containing the text and the rect
			imageData: list of image path and scaled image path
		"""
		self.surface = surface
		self.originalRect = rect
		self.action = buttonType
		self.activeColor = colorData[0]
		self.inactiveColor = colorData[1]
		self.currentColor = self.inactiveColor
		self.text = textData[0]
		self.textColor = textData[1]
		self.active = False
		self.textSurface = Font.render(self.text, True, self.textColor) 
		self.actionData = actionData
		self.extraTextSurfaces = []
		self.extraText = extraText

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

		if self.hasImage:
			ScaleImage(self.imageData[0], (self.rect.w, self.rect.h), self.imageData[1])
			self.image = pg.image.load(self.imageData[1])
			self.image.convert()

	def Draw(self):
		if not self.hasImage:
			pg.draw.rect(self.surface, self.currentColor, self.rect)
			self.surface.blit(self.textSurface, self.rect)
		else:
			self.surface.blit(self.image, self.rect)

		for textSurfaceData in self.extraTextSurfaces:
			self.surface.blit(textSurfaceData[0], textSurfaceData[1])

	def HandleEvent(self, event):
		# check for left mouse button down
		if event.type == pg.MOUSEBUTTONUP:
			if event.button == 1: # left mouse button
				if self.rect.collidepoint(pg.mouse.get_pos()):
					self.active = not self.active

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
	def __init__(self, rect, colors, textData, drawData=[False, False, True], lists=[allLabels], extraText=[], extraData=[], resize=False):
		"""
		Parameters:
			gameStateType: Which gameState to be drawn in
			colors: tuple of border color, background color
			textData: tuple of text, text color, font size, how to align text
			drawData: tuple of rounded edges, addititve, filled
			extraText: any additional text
			extraData: any additional data
		"""
		self.surface = screen
		self.originalRect = rect
		self.borderColor = colors[0]
		self.backgroundColor = colors[1]
		self.text = str(textData[0])
		self.textColor = textData[1]
		self.fontSize = textData[2]
		self.alignText = textData[3]

		self.resize = resize

		self.roundedEdges = drawData[0]
		self.additive = drawData[1]
		self.filled = drawData[2]

		self.extraText = extraText
		self.extraData = extraData

		self.Rescale()

		for listToAppend in lists:
			listToAppend.append(self)

	# rescale all elements
	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)
		self.font = pg.font.SysFont("arial", self.fontSize * SF)
		self.textSurface = self.font.render(self.text, True, self.textColor)
		if self.resize:
			width = max(25 * SF, self.textSurface.get_width()+5*SF)
			height = max(13.5 * SF, self.textSurface.get_height()+5*SF)
			self.rect.w = width
			self.rect.h = height
		
		if self.alignText == "center-center":
			self.textRect = pg.Rect((self.rect[0] + self.rect[2] // 2) - self.textSurface.get_width() // 2, (self.rect[1] + self.rect[3] // 2) - self.textSurface.get_height() // 2, self.rect[2], self.rect[3])
		elif self.alignText == "top-center":
			self.textRect = pg.Rect((self.rect[0] + self.rect[2] // 2) - self.textSurface.get_width() // 2, self.rect[1] + 3 * SF, self.rect[2], self.rect[3])
		elif self.alignText == "top-left":
			self.textRect = (self.rect.x + 5 * SF, self.rect.y + 5 * SF)
		else:
			self.textRect = (self.rect.x + 5 * SF, self.rect.y + 5 * SF)

		self.extraTextSurfaces = []
		for textData in self.extraText:
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			x, y = textData[1][0] * SF, textData[1][1] * SF
			alignText = textData[2]
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			if alignText == "center-center":
				textRect = (x + self.rect.w // SF // 2) - self.textSurface.get_width() // 2, (y + self.rect.h // 2) - self.textSurface.get_height() // 2, self.rect.w, self.rect.h
			elif alignText == "top-center":
				textRect = (x + self.rect.w // SF // 2) - self.textSurface.get_width() // 2, y
			elif alignText == "top-left":
				textRect = x, y


			self.extraTextSurfaces.append((textSurface, textRect))

	def Draw(self):
		if self.roundedEdges:
			DrawObround(self.surface, self.backgroundColor, self.rect, self.filled, self.additive)
			DrawObround(self.surface, colDarkGray, (self.rect.x + 3, self.rect.y + 3, self.rect.w - 6, self.rect.h - 6), self.filled, self.additive)
		else:
			pg.draw.rect(self.surface, self.backgroundColor, self.rect)
			if self.borderColor != False:
				DrawRectOutline(self.surface, self.borderColor, self.rect, 1.5 * SF)
		self.surface.blit(self.textSurface, self.textRect)

		for textSurface in self.extraTextSurfaces:
			self.surface.blit(textSurface[0], textSurface[1])

	def UpdateText(self, text):
		if self.resize:
			width = max(25 * SF, self.textSurface.get_width()+5*SF)
			height = max(13.5 * SF, self.textSurface.get_height()+5*SF)
			self.rect.w = width
			self.rect.h = height

		self.textSurface = self.font.render(text, True, self.textColor)
		if self.alignText == "center-center":
			self.textRect = pg.Rect((self.rect[0] + self.rect[2] // 2) - self.textSurface.get_width() // 2, (self.rect[1] + self.rect[3] // 2) - self.textSurface.get_height() // 2, self.rect[2], self.rect[3])
		elif self.alignText == "top-center":
			self.textRect = pg.Rect((self.rect[0] + self.rect[2] // 2) - self.textSurface.get_width() // 2, self.rect[1] + 3 * SF, self.rect[2], self.rect[3])
		elif self.alignText == "top-left":
			self.textRect = (self.rect.x + 5 * SF, self.rect.y + 5 * SF)
		else:
			self.textRect = (self.rect.x + 5 * SF, self.rect.y + 5 * SF)

	def UpdateExtraText(self, text):
		self.extraText = text
		self.extraTextSurfaces = []
		for textData in self.extraText:
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			x, y = textData[1][0] * SF, textData[1][1] * SF
			alignText = textData[2]
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			if alignText == "center-center":
				textRect = (self.rect.x + self.rect.w // 2) - textSurface.get_width() // 2, (y + self.rect.h // 2) - self.textSurface.get_height() // 2, self.rect.w, self.rect.h
			elif alignText == "top-center":
				textRect = (self.rect.x + self.rect.w // 2) - textSurface.get_width() // 2, y
			elif alignText == "top-left":
				textRect = (x + 5 * SF, y + 5 * SF)
			else:
				textRect = (x + 5 * SF, y + 5 * SF)


			self.extraTextSurfaces.append((textSurface, textRect))


def MakeNewBoundary(event):
	global firstPoint, lastPoint, makingBoundary, allBounds
	bounds = [] 
	for bound in allBounds:
		bounds.append(bound)

	if event.type == pg.MOUSEBUTTONDOWN:
		if event.button == 1:
			firstPoint = pg.mouse.get_pos()

	if event.type == pg.MOUSEBUTTONUP:
		if event.button == 1:
			lastPoint = pg.mouse.get_pos()

			if firstPoint[0] != -1 and firstPoint != lastPoint:
				bounds.append(Boundary(((firstPoint[0] // SF, firstPoint[1] // SF), (lastPoint[0] // SF, lastPoint[1] // SF)), white))
				firstPoint, lastPoint = (-1, -1), (-1, -1)
				allBounds = np.array(bounds)


def Save(saveData):
	global savesDirectoryCreated
	# check if folder called Maps exists
	filesInDirectory = [file for file in listdir(rootDirectory)]
	saveFolderExists = False

	for file in filesInDirectory:
		if saveFolderName in file:
			saveFolderExists = True

	# make folder if Maps doesn't exist
	if not saveFolderExists: 
		os.mkdir(saveFolderName)

	# change current working directory to Maps
	if not savesDirectoryCreated:
		os.chdir(saveFolderName)
		savesDirectoryCreated = True

	currentWorkingDirectory = os.getcwd()
	directory = [file for file in listdir(currentWorkingDirectory)]

	# create save
	fileName = namePrefix + saveName.text + ".json"
	with open(fileName, "w+") as saveFile:
		json.dump(saveData, fp=saveFile, indent=2)
		saveFile.close()

	print(saveName.text)

	os.chdir(rootDirectory)


def GetSaveData():
	saveData = {
		"positions": [],
		"colors": []
	}

	for bound in allBounds:
		saveData["positions"].append(((bound.position[0][0] // SF, bound.position[0][1] // SF), (bound.position[1][0] // SF, bound.position[1][1] // SF)))
		saveData["colors"].append(bound.color)

	Save(saveData)


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
	if loadName != "":
		filesInDirectory = [file for file in listdir(rootDirectory)]
		saveFolderExists = False

		for file in filesInDirectory:
			if saveFolderName in file:
				saveFolderExists = True

		if not savesDirectoryCreated:
			os.chdir(saveFolderName)

		currentWorkingDirectory = os.getcwd()
		directory = [file for file in listdir(currentWorkingDirectory)]

		for file in directory:
			if loadName in file:
				loadCheck = True

		os.chdir(rootDirectory)

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

			if button.action == "save game":
				allButtons.remove(button)
				saveScreen = False
				GetSaveData()
				for obj in saveObjs:
					if obj in allInputBoxs:
						allInputBoxs.remove(obj)
					if obj in allButtons:
						allButtons.remove(obj)
				saveObjs = []

			if button.action == "cancel":
				allButtons.remove(button)
				saveScreen = False
				for obj in saveObjs:
					if obj in allInputBoxs:
						allInputBoxs.remove(obj)
					if obj in allButtons:
						allButtons.remove(obj)
				saveObjs = []


def CreateLoadingScreen():
	global loadLabel, loadName, loadSave, newSave
	loadLabel = Label((((width // SF) // 2) - 150, ((height // SF) // 2) - 70, 100, 20), (lightGray, gray), ("Choose map to load", lightGray, 32, "center-center"), lists=[loadObjs], resize=True)
	loadName = InputBox((((width // SF) // 2) - 100, ((height // SF) // 2) - 10, 200, 20), "Load name: ", characterLimit=30, lists=[loadObjs, allInputBoxs])
	loadSave = HoldButton(screen, (((width // SF) // 2) - 75, ((height // SF) // 2) + 20, 150, 40), "load save", (lightGray, lightGray), ("Load Save", black), lists=[loadObjs, allButtons])
	newSave = HoldButton(screen, (((width // SF) // 2) - 75, ((height // SF) // 2) + 70, 150, 40), "new save", (lightGray, lightGray), ("New Save", black), lists=[loadObjs, allButtons])

	allLoadNamesTitle = Label((((width // SF) // 2) + 185, ((height // SF) // 2) - 170, 100, 20), (lightGray, gray), ("Load names", lightGray, 16, "top-center"), lists=[loadObjs])
	allLoadNamesCont = Label((((width // SF) // 2) + 150, ((height // SF) // 2) - 140, 165, 310), (lightGray, gray), ("", lightGray, 8, "center-center"), lists=[loadObjs])
	# add slider
	names = GetLoadingNames()
	if len(names) != 0:
		for i, name in enumerate(names):
			loadingName = Label((((width // SF) // 2) + 155, ((height // SF) // 2) - 135 + (i * 22), 145, 20), (lightGray, gray), (name, lightGray, 8, "top-left"), lists=[loadObjs])
	else:
		allLoadNamesCont.UpdateText("No saved data found.")


def GetLoadingNames():
	names = []

	try:
		# check if folder called Maps exists
		filesInDirectory = [file for file in listdir(rootDirectory)]
		saveFolderExists = False

		for file in filesInDirectory:
			if saveFolderName in file:
				saveFolderExists = True

		# make folder if Maps doesn't exist
		if not saveFolderExists: 
			os.mkdir(saveFolderName)

		# change current working directory to Maps
		os.chdir(saveFolderName)

		currentWorkingDirectory = os.getcwd()
		directory = [file for file in listdir(currentWorkingDirectory)]

		for file in directory:
			name = file[len(namePrefix):-5]
			if name != "":
				names.append(name)

		os.chdir(rootDirectory)
	except:
		pass

	return names


def CreateSaveScreen():
	global saveLabel, saveName, saveGame, cancel
	saveLabel = Label((((width // SF) // 2) - 150, ((height // SF) // 2) - 70, 100, 20), (lightGray, gray), ("Choose a save name.", lightGray, 26, "center-center"), lists=[saveObjs], resize=True)
	saveName = InputBox((((width // SF) // 2) - 100, ((height // SF) // 2) - 10, 200, 20), "Save name: ", characterLimit=30, lists=[saveObjs, allInputBoxs])
	saveGame = HoldButton(screen, (((width // SF) // 2) - 75, ((height // SF) // 2) + 20, 150, 40), "save game", (lightGray, lightGray), ("Save map", black), lists=[saveObjs, allButtons])
	cancel = HoldButton(screen, (((width // SF) // 2) - 75, ((height // SF) // 2) + 70, 150, 40), "cancel", (lightGray, lightGray), ("Cancel", black), lists=[saveObjs, allButtons])

	allSaveNamesTitle = Label((((width // SF) // 2) + 185, ((height // SF) // 2) - 170, 100, 20), (lightGray, gray), ("Load names", lightGray, 16, "top-center"), lists=[loadObjs])
	allSaveNamesCont = Label((((width // SF) // 2) + 150, ((height // SF) // 2) - 140, 165, 310), (lightGray, gray), ("", lightGray, 8, "center-center"), lists=[loadObjs])
	# add slider
	names = GetLoadingNames()
	if len(names) != 0:
		for i, name in enumerate(names):
			loadingName = Label((((width // SF) // 2) + 155, ((height // SF) // 2) - 135 + (i * 22), 145, 20), (lightGray, gray), (name, lightGray, 8, "top-left"), lists=[loadObjs])
	else:
		allSaveNamesCont.UpdateText("No saved data found.")


def Destroy(event):
	global destroyPointStart, destroyPointEnd, destroyedBounds
	if event.type == pg.MOUSEBUTTONDOWN:
		if event.button == 1:
			destroyPointStart = pg.mouse.get_pos()

	if event.type == pg.MOUSEBUTTONUP:
		if event.button == 1:
			destroyPointEnd = pg.mouse.get_pos()

			if destroyPointStart[0] != -1 and destroyPointStart != destroyPointEnd:
				destroy = pg.Rect(destroyPointStart[0], destroyPointStart[1], destroyPointStart[0] + destroyPointEnd[1], destroyPointStart[1] + destroyPointEnd[1])
				destroyPointStart, destroyPointEnd = (-1, -1), (-1, -1)

			for bound in destroyedBounds:
				bound.Destroy()
			destroyedBounds = []


def DrawDestroy():
	global destroyedBounds
	x1, y1, x2, y2 = destroyPointStart[0], destroyPointStart[1], pg.mouse.get_pos()[0], pg.mouse.get_pos()[1]

	if x1 > x2:
		x2, x1 = destroyPointStart[0], pg.mouse.get_pos()[0]

	if y1 > y2:
		y2, y1 = destroyPointStart[1], pg.mouse.get_pos()[1]

	line1 = (x1, y1)
	line2 = (x1, y2)
	line3 = (x2, y2)
	line4 = (x2, y1)

	# line line intersection + point rect intersection
	pg.draw.aalines(screen, white, True, [line1, line2, line3, line4])
	for bound in allBounds:
		for line in bound.position:
			if line[0] > x1 and line[0] < x2:
				if line[1] > y1 and line[1] < y2:
					pg.draw.aaline(screen, red, bound.position[0], bound.position[1])
					destroyedBounds.append(bound)
				else:
					if bound in destroyedBounds:
						destroyedBounds.remove(bound)
			else:
				if bound in destroyedBounds:
					destroyedBounds.remove(bound)
					
		x1, y1, x2, y2, x3, y3, x4, y4 = line1[0], line1[1], line3[0], line3[1], bound.position[0][0], bound.position[0][1], bound.position[1][0], bound.position[1][1]
		den = ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
		if den != 0:
			t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
			if 0 <= t <= 1:
				L1 = ((x1 + t * (x2 - x1)), (y1 + t * (y2 - y1)))
				if (L1 > (x3, y3)):
					if (L1 < (x4, y4)):
						pg.draw.aaline(screen, red, bound.position[0], bound.position[1])
						destroyedBounds.append(bound)
					else:
						if bound in destroyedBounds:
							destroyedBounds.remove(bound)
				else:
					if bound in destroyedBounds:
						destroyedBounds.remove(bound)
			else:
				if bound in destroyedBounds:
					destroyedBounds.remove(bound)

if __name__ == "__main__":
	CreateLoadingScreen()
	while running:
		clock.tick(FPS)
		screen.fill(gray)

		for event in pg.event.get():
			if event.type == pg.QUIT:
				if not saveScreen and not loadScreen:
					saveScreen = True
					if not loadScreen:
						CreateSaveScreen()
				else:
					running = False
			if event.type == pg.KEYDOWN:
				if event.key == pg.K_ESCAPE:
					if not saveScreen and not loadScreen:
						saveScreen = True
						if not loadScreen:
							CreateSaveScreen()
					else:
						running = False

				if event.key == pg.K_d:
					if not saveScreen and not loadScreen:
						destroyMode = not destroyMode

			if destroyMode:
				Destroy(event)

			ButtonPress(event)

			for inputBox in allInputBoxs:
				inputBox.HandleEvent(event)

			if not loadScreen and not saveScreen and not destroyMode:
				MakeNewBoundary(event)

		for obj in allBuildMenuObj:
			obj.Draw()

		if not saveScreen:
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

		for obj in saveObjs:
			obj.Draw()

		if destroyPointStart[0] != -1 and destroyPointStart != lastPoint and destroyMode:
			DrawDestroy()


		if firstPoint[0] != -1 and firstPoint != lastPoint and not destroyMode:
			pg.draw.aaline(screen, white, firstPoint, pg.mouse.get_pos(), 1)	

		pg.display.flip()
