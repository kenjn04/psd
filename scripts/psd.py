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
		self.scan()

	def scan(self):
		layers = []
		for child in self.layer:
			if isinstance(child, Group):
				layers.extend(GroupLayer(child, self.level + 1).scan())
#			elif isinstance(child, Pixel):
#				self.layers.append(PixelLayer(child, self.level + 1))
			elif isinstance(child, Shape):
				layers.append(ShapeLayer(child, self.level + 1))
			elif isinstance(child, SmartObject):
				layers.append(SmartObjectLayer(child, self.level + 1))
			elif isinstance(child, Type):
				layers.append(TypeLayer(child, self.level + 1))
			else:
				print("Ignore at this moment: %s" % child)
		return layers

srcDirectory = "../app/src/main/java"
bindingDirectory = 'com/sample/myapplication/binding'
bindingInterface = "SampleBinding"
bindingName = "binding"
bindingInterfacePath = "%s/%s/%s.kt" % (srcDirectory, bindingDirectory, bindingInterface)
bindingClass = ("%s/%s" % (bindingDirectory, bindingInterface)).replace('/', '.')
bindingImportBase = "androidx.databinding"
bindingImport = {
	"string": "ObservableField"
}
bindingType = {
	"string": "ObservableField<String>"
}
enumDirectory = 'com/sample/myapplication/enums'
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
		self.layers = self.scan()

	def dump(self, left, top, parent = None):
		layout = etree.Element('layout')
		self.__dumpBinding(layout)
		self.__dumpLayout(layout)
		self.__writeBindingInterface()
		self.__writeEnum()
		self.__writeXml(layout)

	def __dumpBinding(self, layout):
		data = etree.SubElement(layout, 'data')
		variable = etree.SubElement(data, 'variable')
		variable.set("name", bindingName)
		variable.set("type", bindingClass)
		import1 = etree.SubElement(data, 'import')
		import1.set("type", "%s.%s" % (enumDirectory.replace('/', '.'), "Test"))
		import2 = etree.SubElement(data, 'import')
		import2.set("type", "android.view.View")

	def __dumpLayout(self, layout):
		root = etree.SubElement(layout, self.elementName)
		for l in self.layers:
			l.dump(0, 0, root)
		self.setAttribute(layout, "xmlns:android", "http://schemas.android.com/apk/res/android")
		self.setAttribute(layout, "xmlns:app", "http://schemas.android.com/apk/res-auto")
		self.setAttribute(layout, "xmlns:tools", "http://schemas.android.com/tools")
		self.setIdAttribute(root, 'root')
		self.setWidthAttribute(root, 'match_parent')
		self.setHeightAttribute(root, 'match_parent')

	def __writeXml(self, root):
		self.__indent(root)
		tree = etree.ElementTree(root)
		content = '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n'
		content += etree.tostring(root).decode('utf-8').replace(DUMMY_COLON, ':').replace(' \n', '\n')
		with open(outputFile, mode='w') as f:
    			f.write(content)

	def __indent(self, elem, level = 0):
		n = len(elem)
		if n:
			if elem.tag == 'data':
				elem.text = '\n' + (level + 1) * INDENT_SPACE
			else:
				elem.text = '\n\n' + (level + 1) * INDENT_SPACE
			for i in range(0, n):
				if (i + 1) == n:
					elem[i].tail = '\n' + level * INDENT_SPACE
				else:
					if elem.tag == 'data':
						elem[i].tail = '\n' + (level + 1) * INDENT_SPACE
					else:
						elem[i].tail = '\n\n' + (level + 1) * INDENT_SPACE
				self.__indent(elem[i], level + 1)

	def __writeBindingInterface(self):
		with open(bindingInterfacePath, mode='w') as f:
			f.write("package %s\n\n" % bindingDirectory.replace('/', '.'))
			f.write("import %s.%s\n" % (bindingImportBase, bindingImport['string']))
			f.write("import %s.%s\n" % (enumDirectory.replace('/', '.'), "Test"))
			f.write("\ninterface %s {\n\n" % bindingInterface)
			f.write("%sval %s: %s\n" % (INDENT_SPACE, "name", bindingType['string']))
			f.write("%sval %s: %s\n" % (INDENT_SPACE, "mode", "Test"))
			f.write("\n}")

	def __writeEnum(self):
		enumConfig = {
			"name": "Test",
			"elems": ["AAA", "BBB", "CCC"]
		}
		name = enumConfig['name']
		elems = enumConfig['elems']
		enumFilePath = "%s/%s/%s.kt" % (srcDirectory, enumDirectory, name)
		with open(enumFilePath, mode='w') as f:
			f.write("package %s\n\n" % enumDirectory.replace('/', '.'))
			f.write("enum class %s {\n" % name)
			f.write("%s%s\n" % (INDENT_SPACE, ", ".join(elems)))
			f.write("}")

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
