import pyglet
from pyglet import app
from pyglet.window import Window
from MidMooven import MidMooven

display = Window(width=540, height=540) # 1920x1080
display.set_location(270, 270)

batch = pyglet.graphics.Batch()

x = MidMooven(move_setting_dir=r"./Setting/", obj_name="obj_A", img_dir=r"./Images/base/", bat=batch)

@display.event
def update(dt):
  display.clear()
  x.draw(dt)
  batch.draw()
#  print(dt)

pyglet.clock.schedule_interval(update, 1 / 60)

app.run()