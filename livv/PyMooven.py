from PIL import Image # こいつでデータ弄る
import numpy as np # とりあえずimportしとけ
import os # os.path.join()とか色々使う
import math # ネイピア数とかを使用した関数で部品を動かす角度指定しているから必須
from decimal import Decimal, ROUND_HALF_UP
from scipy import integrate # 積分して角の変位を決める
import json # 動作設定ファイルが.jsonだから, こいつ無いと読み込めない

import pyglet

"""
imgは全てpngで統一しておく(.jpgとかは一旦無視して、pngで動くようにする)
パーツは全部まとめて基底ファイルに入れる
例えば (obj == object) obj_A, obj_B, obj_Cの3つの物体を動かしたいときに
obj_base
{
obj_A
{parts_1, parts_2,...}
obj_B
{parts_1,...}
obj_C
{...}
}
みたいな感じにファイルを配置する。
obj_Aの部品をobj_Bで流用する考えはあるけど、まずは受験勉強と本体の骨格ができてからにする。

settingファイルのディレクトリ
Setting
{
obj_A
{parts_1.txt, parts_2.txt,...}
obj_B
{...}
}
"""

CONST_MOVEMENTS_KEYS = ("integral", "formula", "assign")

class mooven:
  def __init__(self, this_parts_name, setting_dir, parts_image_dir_path, bat=None, pxy=[0, 0, 0], parents_anchor=[0, 0]):
    if bat != None:
      global batch
      batch = bat
    self.this_parts_name = this_parts_name # この部品の名前
    self.setting_dir = setting_dir
    self.parts_image_dir_path = parts_image_dir_path
    self.parts_image_path = os.path.join(self.parts_image_dir_path, self.this_parts_name) + ".png" # 画像のパス
    self.first_parents_xyr = pxy # 最初の親部品の座標.
    self.first_parents_xyr[2] *= -1 # 補正。なぜかマイナス掛けないとバグる。まぁどっか見落としているんでしょうな。 checkA
    self.parents_anchor = parents_anchor # 親のアンカー座標.
    try:
      with open(os.path.join(self.setting_dir, self.this_parts_name)+".json", mode="r") as f:
        self.parts_data = json.load(f)
      self.tf = True
    except:
      self.tf = False
      return
    self.main_load()
    self.counter = 0
    if self.this_parts_name == "parts_0":
      self.test_flag = 0
    elif self.this_parts_name == "parts_0_1":
      self.test_flag = 1
    else:
      self.test_flag = -1

  def main_load(self):
    def make_act_name_dict(l): # lにリスト突っ込んでact_name_listを生成。
      return dict(zip(list(l.keys()), list(range(len(l)))))
    self.property = self.parts_data["property"]
    self.base_point = self.property["connection_in_parent"] # 親部品での接続座標
    self.origin_point = self.property["origin_point"] # アンカー座標.

    self.parts_img = pyglet.image.load(self.parts_image_path) # 画像読み込み
    self.parts_img.anchor_x = self.origin_point[0]
    self.parts_img.anchor_y = self.origin_point[1]

    self.children_parts_name = self.property["children_parts_name"] # 子パーツのリスト

    self.move = self.parts_data["move"]
    self.rotate = -self.move["t0"] # 初期の角度読み込み checkA
    self.movement = self.move["movement"]
    self.movement_all = [self.movement[i] for i in CONST_MOVEMENTS_KEYS]
    self.act_name_list = [make_act_name_dict(self.movement[i]) for i in CONST_MOVEMENTS_KEYS]
    self.movement_all = [list(self.movement_all[i].values()) for i in range(len(CONST_MOVEMENTS_KEYS))]
    self.movement_funcs = [[i[ia] for ia in range(len(i))] for i in self.movement_all]

    self.acting_time = [[0 for ia in range(len(self.act_name_list[i]))] for i in range(len(CONST_MOVEMENTS_KEYS))] # 実行中の動作の経過時間
    self.acting_movement = [[False for ia in range(len(self.act_name_list[i]))] for i in range(len(CONST_MOVEMENTS_KEYS))] # 実行中の動作

    self.delta_omega = 0
    self.delta_const_omega = 0

    self.inum_connection = complex(self.base_point[0] - self.parents_anchor[0], self.base_point[1] - self.parents_anchor[1]) # cal_xyで使う.
    self.previous_part_xyr = list(self.cal_xy(self.first_parents_xyr[0], self.first_parents_xyr[1], self.first_parents_xyr[2]))
    self.previous_part_xyr.append(self.first_parents_xyr[2] + self.rotate)
    try: # レイヤー番号読み込み
      self.layer = self.property["layer"]
      print(f"Loaded the layer number of {self.this_parts_name};")
    except:
      self.layer = 0
      print(f"Failed to load the layer number of {self.this_parts_name};")

# Sprite
    self.part = pyglet.sprite.Sprite(self.parts_img, x=self.previous_part_xyr[0], y=self.previous_part_xyr[1], batch=batch, group=pyglet.graphics.OrderedGroup(order=self.layer)) # pyglet v2.0.10ならgroup=pyglet.graphics.Group(order=self.layer)だったのがanacondaさんがv1.5.27インスコしたのでOrderedGroupを使ってる.
    self.part.rotation += self.previous_part_xyr[2]

    self.children_execution = [] # 子のデータ実行.
    for name in self.children_parts_name:
      self.children_execution.append(mooven(this_parts_name=name, setting_dir=self.setting_dir, parts_image_dir_path=self.parts_image_dir_path, bat=batch, pxy=self.previous_part_xyr, parents_anchor=self.origin_point))
      if self.children_execution[-1].tf:
        print(f"Expanded {name};")
      else:
        del self.children_execution[-1]
        print(f"Failed to expand {name};")
        del self.children_parts_name[self.children_parts_name.index(name)]

  def children_exe(self):
    xyr = [self.part.x, self.part.y, self.part.rotation]
    for i in self.children_execution:
      i.draw(self.dt, xyr)

  def d_rotation(self, movement=[[], [], []]):
    def reset_movement():
      self.acting_time[i][ia] = self.movement_all[i][ia][0]
      self.acting_movement[i][ia] = False
      print("End")
    """
    def deltaplus(x):
      if i == 0:
        self.delta_omega += x
      elif i == 1 or i == 2:
        self.delta_const_omega += x
    """
    def integral():
      def do_integral():
        def func_open(x):
          return eval(self.movement_funcs[i][ia][2])
        res, _ = integrate.quad(func=func_open, a=temp_acting, b=execute_integral_upper) # 積分して角の変位を割り出す.
        return res
      execute_integral_upper = temp_acting + self.dt # 積分範囲の上限を超えるかどうか確認.
      if execute_integral_upper >= self.movement_all[i][ia][1]:
        execute_integral_upper = self.movement_all[i][ia][1]
        self.delta_omega += do_integral()
        reset_movement()
      else:
        self.delta_omega += do_integral()
        self.acting_time[i][ia] += self.dt

    def formula():
      def func_open(x):
        return eval(self.movement_funcs[i][ia][2])
      if temp_acting + self.dt >= self.movement_funcs[i][ia][1]:
        self.delta_const_omega += func_open(self.movement_funcs[i][ia][1])
        reset_movement()
      else:
        self.delta_const_omega += func_open(temp_acting)
        self.acting_time[i][ia] += self.dt

    def assign():
      def adjust_time_arg(t):
        self.delta_const_omega += self.movement_funcs[i][ia][2][int(Decimal(str(t / self.movement_funcs[i][ia][3])).quantize(Decimal("0"), ROUND_HALF_UP))] # 四捨五入.
      if temp_acting + self.dt >= self.movement_funcs[i][ia][1]:
        adjust_time_arg(self.movement_funcs[i][ia][1])
        reset_movement()
      else:
        adjust_time_arg(temp_acting + self.dt)
        self.acting_time[i][ia] += self.dt

    funcs = [integral, formula, assign]
    self.delta_omega = 0 # 角の変位.
    self.delta_const_omega = 0
    for i in range(len(CONST_MOVEMENTS_KEYS)):
      for start_mov_name in movement[i]:
        ia = self.act_name_list[i][start_mov_name] # iは数値.
        print(f"Execute {self.this_parts_name}.{start_mov_name}")
        if not self.acting_movement[i][ia]:
          self.acting_movement[i][ia] = True
        self.acting_time[i][ia] = 0

      for ia in range(len(self.acting_movement[i])):
        if not self.acting_movement[i][ia]:
          continue
        temp_acting = self.acting_time[i][ia]
        funcs[i]()

    self.rotate += self.delta_omega # 親部品の角と合成されていないこの部品のみの角.
    self.rotate %= 360
    self.part.rotation = self.rotate + self.parents_xyr[2] + self.delta_const_omega
    self.part.rotation %= 360

  def receive_move(self):
    if self.counter <= 300:
      self.counter += 1
      if self.this_parts_name == "parts_0":
        print(self.counter)
    if self.test_flag == 0 and self.counter > 300:
      self.test_flag = -1
      self.d_rotation(movement=[[], ["0"], []])
    elif self.test_flag == 1 and self.counter > 300:
      self.test_flag = -1
      self.d_rotation(movement=[[], ["0"], []])
    else:
      self.d_rotation(movement=[[], [], []])
    self.children_exe()

  def cal_xy(self, px, py, pr):
    """
  prをラジアンに変換してないやん…(n時間消滅)
  jsonの階層ミス(13時間), 致命的なクラス継承のバグ(8時間), ラジアンに変換してない(?日)
    """
    pr = math.radians(-pr)
    inum_parents_rotate = complex(math.cos(pr), math.sin(pr))
    xy = self.inum_connection * inum_parents_rotate + complex(px, py)
    return xy.real, xy.imag

  def draw(self, dt, pxyr): # pxyr, 親の部品のx, y座標, 角.
    self.dt = dt # このフレームでのΔtが何秒か, 親部品のx, y座標, 角度.
    self.parents_xyr = pxyr
    self.part.x, self.part.y = self.cal_xy(self.parents_xyr[0], self.parents_xyr[1], self.parents_xyr[2])
    self.receive_move()