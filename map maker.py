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

firstPoint, lastPoint = (-1, -1), (-1, -1)

Font = pg.font.SysFont("arial", 8 * SF)

rootDirectory = os.getcwd()
saveFolderName = "Maps"
savesDirectoryCreated = False

loadScreen = True
running = True

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

	def Draw(self):
		pg.draw.aaline(screen, self.color, self.position[0], self.position[1], 1)


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

	# check if there are already existing saves
	allSaves = []
	saveName = ""
	for file in directory:
		for char in file[4:]:
			if char == ".":
				break
			else:
				saveName += char
		allSaves.append(int(saveName))
		saveName = ""

	if len(allSaves) > 0:
		# find the largest save and add 1 to get new save number
		largestNumberSave = max(allSaves)
		saveNumber = int(largestNumberSave) + 1
	else:
		# no save exist so start at 0 
		saveNumber = 0	
	saveNumber = str(saveNumber)

	# create save
	fileName = "Map-" + saveNumber + ".json"
	with open(fileName, "w+") as saveFile:
		json.dump(saveData, fp=saveFile, indent=2)
		saveFile.close()

	os.chdir(rootDirectory)


def GetSaveData():
	saveData = {
		"positions": [],
		"colors": []
	}

	for bound in allBounds:
		saveData["positions"].append(bound.position)
		saveData["colors"].append(bound.color)

	print(saveData)

	return saveData


def Load():
	saveData = {
		"positions": [],
		"colors": []
	}

	print("load")

	return saveData


def CheckLoad():
	global loadNumber
	loadCheck = False
	if loadNumber.text != "":
		filesInDirectory = [file for file in listdir(rootDirectory)]
		saveFolderExists = False

		for file in filesInDirectory:
			if saveFolderName in file:
				saveFolderExists = True

		# change current working directory to Maps
		if saveFolderExists:
			os.chdir(saveFolderName)

		currentWorkingDirectory = os.getcwd()
		directory = [file for file in listdir(currentWorkingDirectory)]

		for file in directory:
			if loadNumber.text in file:
				loadCheck = True

	return loadCheck


def ButtonPress(event):
	global loadObjs, loadScreen
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
				loadCheck = CheckLoad()
				if loadCheck:
					loadScreen = False
					allButtons.remove(button)
					for obj in loadObjs:
						if obj in allInputBoxs:
							allInputBoxs.remove(obj)
						if obj in allButtons:
							allButtons.remove(obj)
					loadObjs = []
					Load()


loadLabel = Label((((width // SF) // 2) - 150, ((height // SF) // 2) - 70, 100, 20), "Choose map to load", fontSize=32, lists=[loadObjs])
loadNumber = InputBox((((width // SF) // 2) - 100, ((height // SF) // 2) - 10, 200, 20), "Load Number: ", characterLimit=30, lists=[loadObjs, allInputBoxs])
loadSave = HoldButton(screen, (((width // SF) // 2) - 75, ((height // SF) // 2) + 20, 150, 40), "load save", (lightGray, lightGray), ("Load Save", black), lists=[loadObjs, allButtons])
newSave = HoldButton(screen, (((width // SF) // 2) - 75, ((height // SF) // 2) + 70, 150, 40), "new save", (lightGray, lightGray), ("New Save", black), lists=[loadObjs, allButtons])

while running:
	clock.tick(FPS)
	screen.fill(gray)

	for event in pg.event.get():
		if event.type == pg.QUIT:
			running = False	
		if event.type == pg.KEYDOWN:
			if event.key == pg.K_ESCAPE:
				running = False

			if event.key == pg.K_s:
				Save(GetSaveData())

		ButtonPress(event)

		for inputBox in allInputBoxs:
			inputBox.HandleEvent(event)

		if not loadScreen:
			MakeNewBoundary(event)

	for obj in allBuildMenuObj:
		obj.Draw()

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

	if firstPoint[0] != -1 and firstPoint != lastPoint:
		pg.draw.aaline(screen, white, firstPoint, pg.mouse.get_pos(), 1)	

	pg.display.flip()
