#--------------------------------------------------------------------------------|
# Name:        Image Crop Tool GUI					         |
# Purpose:     Crop images for Object detection & Computer Vision		 |
# Author:      Syrine Ben Amor						 |
# Email:       syrine.benamor76@gmail.com					 |
# Created:     1/12/2017							 |
#--------------------------------------------------------------------------------|
from __future__ import division
from Tkinter import *
import tkMessageBox
from PIL import Image, ImageTk
import os
import glob
import random
import cv2
import numpy as np
import math
# colors for the bboxes
COLORS = ['red', 'blue', 'pink', 'cyan', 'green', 'black']
SIZE=1054,682
Hueoffset = 20
Satoffset = 20
datatype = ".jpg"
class LabelTool():
	def RGB2HSV(self,r, g, b):
		r,g,b = r/255.0,g/255.0,b/255.0
		mx = max(r, g, b)
		mn = min(r, g, b)
		df = mx-mn
		if mx == mn:
			h = 0
		elif mx == r:
			h = (60 * ((g-b)/df) + 360) % 360
		elif mx == g:
			h = (60 * ((b-r)/df) + 120) % 360
		elif mx == b:
			h = (60 * ((r-g)/df) + 240) % 360
		if mx == 0:
			s = 0
		else:
			s = df/mx
		v = mx
		s *= 100
		h = int (round(h))
		s = int(round(s))
		return h, s, v

	def __init__(self, master):
		# set up the main frame
		self.parent = master
		self.parent.title("CropTool")
		self.frame = Frame(self.parent)
		self.frame.pack(fill=BOTH, expand=1)
		self.parent.resizable(width = FALSE, height = FALSE)

		# initialize global state
		self.imageDir = ''
		self.imageList= []
		self.outDir = ''
		self.cur = 0
		self.total = 0
		self.category = 0
		self.imagename = ''
		self.tkimg = None

		# initialize mouse state
		self.STATE = {}
		self.STATE['click'] = 0
		self.STATE['x'], self.STATE['y'] = 0, 0

		# reference to bbox
		self.bboxIdList = []
		self.bboxId = None
		self.bboxList = []
		self.hl = None
		self.vl = None

		# ----------------- GUI stuff ---------------------
		# dir entry & load
		self.label = Label(self.frame, text = "Image Dir:")
		self.label.grid(row = 0, column = 0, sticky = E)
		self.entry = Entry(self.frame)
		self.entry.grid(row = 0, column = 1, sticky = W+E)
		self.ldBtn = Button(self.frame, text = "Load", command = self.loadDir)
		self.ldBtn.grid(row = 0, column = 2, sticky = W+E)

		# main panel for Selecting
		self.mainPanel = Canvas(self.frame, cursor='tcross')
		self.mainPanel.bind("<Button-1>", self.mouseClick)
		self.mainPanel.bind("<Motion>", self.mouseMove)
		#self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
		#self.parent.bind("s", self.cancelBBox)
		self.parent.bind("a", self.prevImage) # press 'a' to go backforward
		self.parent.bind("d", self.nextImage) # press 'd' to go forward
		self.mainPanel.grid(row = 1, column = 1, rowspan = 4, sticky = W+N)

		# showing boxes info & delete boxes
		self.lb1 = Label(self.frame, text = 'Cropping boxes:')
		self.lb1.grid(row = 1, column = 2,  sticky = W+N)
		self.listbox = Listbox(self.frame, width = 22, height = 12)
		self.listbox.grid(row = 2, column = 2, sticky = N)
		self.btnDel = Button(self.frame, text = 'Transform', command = self.Transform)
		self.btnDel.grid(row = 4, column = 2, sticky = W+E+N)
		self.btnClear = Button(self.frame, text = 'Reset', command = self.Reset)
		self.btnClear.grid(row = 3, column = 2, sticky = W+E+N)

		# control panel for image navigation
		self.ctrPanel = Frame(self.frame)
		self.ctrPanel.grid(row = 5, column = 1, columnspan = 2, sticky = W+E)
		self.prevBtn = Button(self.ctrPanel, text='<< Prev', width = 10, command = self.prevImage)
		self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
		self.nextBtn = Button(self.ctrPanel, text='Next >>', width = 10, command = self.nextImage)
		self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)
		self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
		self.progLabel.pack(side = LEFT, padx = 5)
		self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
		self.tmpLabel.pack(side = LEFT, padx = 5)
		self.idxEntry = Entry(self.ctrPanel, width = 5)
		self.idxEntry.pack(side = LEFT)
		self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
		self.goBtn.pack(side = LEFT)


		# display mouse position
		self.disp = Label(self.ctrPanel, text='')
		self.disp.pack(side = RIGHT)

		self.frame.columnconfigure(1, weight = 1)
		self.frame.rowconfigure(4, weight = 1)

		# for debugging
##        self.setImage()
##        self.loadDir()

	def loadDir(self, dbg = False):
		if not dbg:
			s = self.entry.get()
			self.parent.focus()
			self.category = s
		if self.category =="" : self.category = "tof"
		print s
		if not os.path.isdir(r'./Images/%s' %s):
			tkMessageBox.showerror("Error!", message = "The specified dir doesn't exist!")
			return
		# get image list
		self.imageDir = os.path.join(r'./Images', '%s' %(self.category))
		print "-" + str(self.imageDir)
		self.imageList = glob.glob(os.path.join(self.imageDir, "*"+datatype))
		#print "+" + str(len(self.imageList))
		if len(self.imageList) == 0:
			print 'No ' + datatype+' images found in the specified dir!'
			return

		# default to the 1st image in the collection
		self.cur = 1
		self.total = len(self.imageList)

		 # set up output dir
		self.outDir = os.path.join(r'./Crops', '%s' %(self.category))
		if not os.path.exists(self.outDir):
			os.mkdir(self.outDir)
		self.loadImage()
		print '%d images loaded from %s' %(self.total, s)

	def loadImage(self):
		# load image
		self.imagepath = self.imageList[self.cur - 1]
		#print imagepath
		self.img 		  = Image.open(self.imagepath)
		self.original_img = Image.open(self.imagepath)
		new_size = self.img.size
		self.r = 1
		if new_size[0] > SIZE[0] | new_size[1] > SIZE[1] :
			self.r = min(SIZE[0] / self.img.size[0],SIZE[1] / self.img.size[1])
			print self.r
			new_size = int(self.r * self.img.size[0]), int(self.r * self.img.size[1])
		self.tkimg = ImageTk.PhotoImage(self.img.resize(new_size, Image.ANTIALIAS))
		self.mainPanel.config(width = min(self.tkimg.width(), SIZE[0]), height = min(self.tkimg.height(), SIZE[1]))
		self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
		self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))


	def mouseClick(self, event):
		if self.STATE['click'] == 0:
			self.STATE['x'], self.STATE['y'] = event.x, event.y
			self.bboxList.append((self.STATE['x'], self.STATE['y']))
			self.bboxIdList.append(self.bboxId)
			self.bboxId = None
			self.listbox.insert(END, '(%d, %d)' %(self.STATE['x'], self.STATE['y']))
			self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
		

	def mouseMove(self, event):
		self.disp.config(text = 'x: %d, y: %d' %(event.x, event.y))
		if self.tkimg:
			if self.hl:
				self.mainPanel.delete(self.hl)
			self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
			if self.vl:
				self.mainPanel.delete(self.vl)
			self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)
		if 1 == self.STATE['click']:
			if self.bboxId:
				self.mainPanel.delete(self.bboxId)
			self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
															event.x, event.y, \
															width = 2, \
															outline = COLORS[len(self.bboxList) % len(COLORS)])

	def clearBBox(self):
		for idx in range(len(self.bboxIdList)):
			self.mainPanel.delete(self.bboxIdList[idx])
		self.listbox.delete(0,len(self.bboxList))
		self.bboxIdList=[]
		self.bboxList  =[]

	def Transform(self):
		x,y=self.STATE['x'], self.STATE['y']
		print "x= "+ str(x) + "  y= "+str(y)
		Red,Green,Blue = self.img.getpixel((x,y))
		Hue,Sat,Value = self.RGB2HSV(Red,Green,Blue)
		print "Hue= "+ str(Hue) + "  Sat= " + str(Sat) + "  Value= " + str(Value) 
		
		if Hue-Hueoffset < 0 :
			Hueinterval= range((Hue-Hueoffset)%360,360) + range(0,(Hue+Hueoffset)%360)
		elif Hue+Hueoffset >=360 :
			Hueinterval= range((Hue-Hueoffset)%360,360) + range(0,(Hue+Hueoffset)%360)
		else :
			Hueinterval= range(Hue-Hueoffset,Hue+Hueoffset)

		if Sat-Satoffset <0 :
			Satinterval= range((Sat-Satoffset)%100,100) + range(0,(Sat+Satoffset)%100)
		elif  Sat+Satoffset >=100 :
			Satinterval= range((Sat-Satoffset)%100,100) + range(0,(Sat+Satoffset)%100)
		else :
			Satinterval= range(Sat-Satoffset,Sat+Satoffset)
		
		for i in xrange(1,self.img.size[0]):
			for j in xrange(1,self.img.size[1]):
				r,g,b = self.img.getpixel((i,j))
				h,s,_ = self.RGB2HSV(r,g,b)
				condition = (h in Hueinterval and (s in Satinterval))
				if not condition :
					self.img.putpixel((i,j),(0,0,0))
					#print i, j
		new_size = self.img.size
		self.r = 1
		if new_size[0] > SIZE[0] | new_size[1] > SIZE[1] :
			self.r = min(SIZE[0] / self.img.size[0],SIZE[1] / self.img.size[1])
			print self.r
			new_size = int(self.r * self.img.size[0]), int(self.r * self.img.size[1])
		self.tkimg = ImageTk.PhotoImage(self.img.resize(new_size, Image.ANTIALIAS))
		self.mainPanel.config(width = min(self.tkimg.width(), SIZE[0]), height = min(self.tkimg.height(), SIZE[1]))
		self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
				


	def Reset(self):
		self.clearBBox()
		self.img = Image.open(self.imagepath)
		new_size = self.img.size
		self.r = 1
		if new_size[0] > SIZE[0] | new_size[1] > SIZE[1] :
			self.r = min(SIZE[0] / self.img.size[0],SIZE[1] / self.img.size[1])
			print self.r
			new_size = int(self.r * self.img.size[0]), int(self.r * self.img.size[1])
		self.tkimg = ImageTk.PhotoImage(self.img.resize(new_size, Image.ANTIALIAS))
		self.mainPanel.config(width = min(self.tkimg.width(), SIZE[0]), height = min(self.tkimg.height(), SIZE[1]))
		self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)

	def prevImage(self, event = None):
		if self.cur > 1:
			self.cur -= 1
			self.loadImage()

	def nextImage(self, event = None):
		if self.cur < self.total:
			self.cur += 1
			self.loadImage()

	def gotoImage(self):
		idx = int(self.idxEntry.get())
		if 1 <= idx and idx <= self.total:
			#self.saveImage()
			self.cur = idx
			self.loadImage()

if __name__ == '__main__':
	root = Tk()
	tool = LabelTool(root)
	root.resizable(width =  True, height = True)
	root.mainloop()
