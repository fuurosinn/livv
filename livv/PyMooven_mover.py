import pyglet
from pyglet import app
from pyglet.window import Window
from MidMooven import MidMooven
from JsonLoader import Loader
import os

display = Window(width=720, height=720) # 1920x1080
display.set_location(256, 64)

batch = pyglet.graphics.Batch()

x = MidMooven(move_setting_dir=r"./Setting/", obj_name="obj_A", img_dir=r"./Images/base/", bat=batch)

"""
maxlayer = Loader(dir="./Setting/obj_A", pn="parts.json")["maxlayer"] # 例えばmaxlayer=2の時は、0, 1, 2でmaxlayerまで含めることに注意。
layers = [pyglet.graphics.Group(order=i) for i in range(maxlayer+1)] # なので+1する。
"""

@display.event
def update(dt):
  display.clear()
  x.draw(dt)
  batch.draw()

pyglet.clock.schedule_interval(update, 1 / 60)

app.run()