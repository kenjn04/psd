#!/usr/bin/env python3

import glob, os, re, shutil, sys
from psd_tools import PSDImage
from psd_tools.api.layers import Group
from psd_tools.api.layers import PixelLayer as Pixel
from psd_tools.api.layers import ShapeLayer as Shape
from psd_tools.api.layers import SmartObjectLayer as SmartObject
from psd_tools.api.layers import TypeLayer as Type
import xml.etree.ElementTree as etree

DUMMY_COLON = "___"
ANDROID_ID     = "android:id"
ANDROID_WIDTH  = "android:layout_width"
ANDROID_HEIGHT = "android:layout_height"
ANDROID_LEFT   = "android:layout_marginLeft"
ANDROID_TOP    = "android:layout_marginTop"
ANDROID_IMAGE  = "app:srcCompat"
PROHIBIT_CHARACTORS = '%|#|\(|\)'
INDENT_SPACE = "    "

outputFile = '../app/src/main/res/layout/activity_main.xml'
drawableDirectory = '../app/src/main/res/drawable'
remaindDrawableFiles = [
	'ic_launcher_background.xml'
]

class Layer(object):
	def __init__(self, layer, level):
		self.layer = layer
		self.level = level

	def scan(self):
		pass

	def dump(self, left, top, parent):
		pass

	def addChildElement(self, parent):
		return etree.SubElement(parent, self.elementName)

	def setIdAttribute(self, element, val):
		val = '@+id/' + val
		self.setAttribute(element, ANDROID_ID, val)

	def setWidthAttribute(self, element, val):
		if isinstance(val, int):
			val = str(val) + 'dp'
		self.setAttribute(element, ANDROID_WIDTH, val)

	def setHeightAttribute(self, element, val):
		if isinstance(val, int):
			val = str(val) + 'dp'
		self.setAttribute(element, ANDROID_HEIGHT, val)

	def setLeftAttribute(self, element, val):
		val = str(val) + 'dp'
		self.setAttribute(element, ANDROID_LEFT, val)

	def setTopAttribute(self, element, val):
		val = str(val) + 'dp'
		self.setAttribute(element, ANDROID_TOP, val)

	def setImageAttribute(self, element, val):
		val = '@drawable/' + str(val)
		self.setAttribute(element, ANDROID_IMAGE, val)

	def setAttribute(self, element, attr, val):
		indent = "\n" + (self.level + 1) * INDENT_SPACE
		element.set(indent + attr.replace(':', DUMMY_COLON), val)

	def updateCoordinte(self, left, top):
		offset = self.layer.offset
		x = offset[0] - left
		y = offset[1] - top
		return (x, y)

class NodeLayer(Layer):
	def __init__(self, layer, level):
		super().__init__(layer, level)
		self.elementName = "FrameLayout"
		self.layers = []
		self.scan()

	def scan(self):
		for child in self.layer:
			if isinstance(child, Group):
				self.layers.append(GroupLayer(child, self.level + 1))
#			elif isinstance(child, Pixel):
#				self.layers.append(PixelLayer(child, self.level + 1))
			elif isinstance(child, Shape):
				self.layers.append(ShapeLayer(child, self.level + 1))
			elif isinstance(child, SmartObject):
				self.layers.append(SmartObjectLayer(child, self.level + 1))
			elif isinstance(child, Type):
				self.layers.append(TypeLayer(child, self.level + 1))
			else:
				print("Ignore at this moment: %s" % child)

class RootLayer(NodeLayer):
	def __init__(self, psdPath):
		psd = PSDImage.open(psdPath)
		super().__init__(psd, 0)
		if os.path.isdir(drawableDirectory):
			for file in glob.glob(drawableDirectory + '/*'):
				if os.path.basename(file) in remaindDrawableFiles:
					continue
				os.remove(file)
		else:
			os.mkdir(drawableDirectory)

	def dump(self, left, top, parent = None):
		root = etree.Element(self.elementName)
		for l in self.layers:
			l.dump(0, 0, root)
		self.setAttribute(root, "xmlns:android", "http://schemas.android.com/apk/res/android")
		self.setAttribute(root, "xmlns:app", "http://schemas.android.com/apk/res-auto")
		self.setAttribute(root, "xmlns:tools", "http://schemas.android.com/tools"'root')
		self.setIdAttribute(root, 'root')
		self.setWidthAttribute(root, 'match_parent')
		self.setHeightAttribute(root, 'match_parent')
		self.__writeXml(root)

	def __writeXml(self, root):
		self.__indent(root)
		tree = etree.ElementTree(root)
		tree.write('aaa.xml', encoding="utf-8", xml_declaration=True)
		content = '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n'
		content += etree.tostring(root).decode('utf-8').replace(DUMMY_COLON, ':').replace(' \n', '\n')
		with open(outputFile, mode='w') as f:
    			f.write(content)

	def __indent(self, elem, level = 0):
		n = len(elem)
		if n:
			elem.text = '\n\n' + (level + 1) * INDENT_SPACE
			for i in range(0, n):
				if (i + 1) == n:
					elem[i].tail = '\n' + level * INDENT_SPACE
				else:
					elem[i].tail = '\n\n' + (level + 1) * INDENT_SPACE
				self.__indent(elem[i], level + 1)
		else:
			elem.text = '\n' + level * INDENT_SPACE

class GroupLayer(NodeLayer):
	def __init__(self, group, level):
		super().__init__(group, level)

	def dump(self, left, top, parent):
		x, y = self.updateCoordinte(left, top)
		if len(self.layers) == 0:
			return
		node = self.addChildElement(parent)
		for l in self.layers:
			l.dump(x, y, node)
		width = self.layer.size[0]
		height = self.layer.size[1]
		self.setIdAttribute(node, self.layer.name.lower().replace(' ', '_'))
		self.setWidthAttribute(node, width)
		self.setHeightAttribute(node, height)
		self.setLeftAttribute(node, x)
		self.setTopAttribute(node, y)

class LeafLayer(Layer):
	def __init__(self, layer, level):
		super().__init__(layer, level)
		self.elementName = 'ImageView'

	def dump(self, left, top, parent):
		image = self.__createImage()
		if image == "":
			return
		leaf = self.addChildElement(parent)
		x, y = self.updateCoordinte(left, top)
		width = self.layer.size[0]
		height = self.layer.size[1]
		self.updateElement(leaf, width, height, x, y, image)

	def updateElement(self, leaf, width, height, x, y, image):
		self.setIdAttribute(leaf, image)
		self.setWidthAttribute(leaf, width)
		self.setHeightAttribute(leaf, height)
		self.setLeftAttribute(leaf, x)
		self.setTopAttribute(leaf, y)
		self.setImageAttribute(leaf, image)

	def __createImage(self):
		if self.layer.is_group():
			return
		imageName = re.sub(PROHIBIT_CHARACTORS, '', self.layer.name.lower().replace(' ', '_'))
		if not re.search('^[a-z].+', imageName):
			imageName = "image_" + imageName
		imageFilePath = drawableDirectory + '/' + imageName + '.png'
		suffix = 0
		while True:
			if not os.path.isfile(imageFilePath):
				break
			imageName = imageName.rstrip('_' + str(suffix))
			suffix = suffix + 1
			imageName = "%s_%s" % (imageName, suffix)
			imageFilePath = drawableDirectory + '/' + imageName + '.png'

		image = self.layer.topil()
		if image == None:
			print("%s is empty." % imageName)
			return ""
		image.save(imageFilePath)
		return imageName

class PixelLayer(LeafLayer):
	def __init__(self, layer, level):
		super().__init__(layer, level)

class ShapeLayer(LeafLayer):
	def __init__(self, layer, level):
		super().__init__(layer, level)

class SmartObjectLayer(LeafLayer):
	def __init__(self, layer, level):
		super().__init__(layer, level)

class TypeLayer(LeafLayer):
	def __init__(self, layer, level):
		super().__init__(layer, level)

def main(argv):
	psdPath = './3074963.psd'
	RootLayer(psdPath).dump(0, 0)

if __name__ == '__main__':
	sys.exit(main(sys.argv))