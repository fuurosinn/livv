from PIL import Image # こいつでデータ弄る
import numpy as np # とりあえずimportしとけ
import os # os.path.join()とか色々使う
import math # ネイピア数とかを使用した関数で部品を動かす角度指定しているから必須
from scipy import integrate # 積分して角の変位を決める
import json # 動作設定ファイルが.jsonだから, こいつ無いと読み込めない

from random import randint

import pyglet
from pyglet import app
from pyglet.window import Window

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

class mooven:
  def __init__(self, this_parts_name, setting_dir, parts_image_dir_path, bat=None, pxyr=[0, 0, 0]): # pxyr ==> previous_part_xyr.
    if bat != None:
      global batch
      batch = bat
    self.this_parts_name = this_parts_name # この部品の名前
    self.setting_dir = setting_dir
    self.parts_image_dir_path = parts_image_dir_path
    self.parts_image_path = os.path.join(self.parts_image_dir_path, self.this_parts_name) + ".png" # 画像のパス
    self.parents_xyr = [270, 270, 0] # 親部品のxy座標及び回転.
    self.previous_part_xyr = pxyr # この部品の前のフレームでのxy座標及び回転.
    with open(os.path.join(self.setting_dir, self.this_parts_name)+".json", mode="r") as f:
      self.parts_data = json.load(f)
    self.main_load()
    self.test_flag = True

  def main_load(self):
    """
各部品の親部品(接続元)を原点として自分の相対座標と角度を計算して親部品に結果を返す
親部品の座標基準でどこに接続しているのかを確認する必要がある。
    """
    self.parts_img = pyglet.image.load(self.parts_image_path) # 画像読み込み
    self.property = self.parts_data["property"]

    self.base_point = self.property["connection_in_parent"] # 親部品での接続座標
    self.origin_point = self.property["origin_point"] # x, y
    self.parts_img.anchor_x = self.origin_point[0]
    self.parts_img.anchor_y = self.origin_point[1]
    self.children_parts_name = self.property["children_parts_name"] # 子パーツのリスト

    self.move = self.parts_data["move"]
    self.rotate = self.move["t0"] # 初期の角度読み込み
    self.movement = self.move["movement"]
    self.act_name_list = dict(zip(list(self.movement.keys()), list(range(len(self.movement)))))
    self.movement = list(self.movement.values()) # 式の情報だけになる.
    self.movement_data_integral_lower = [i[0] for i in self.movement] # 動作の秒数開始時刻.
    self.movement_data_integral_upper = [i[1] for i in self.movement] # 動作の終了時刻.
    self.movement = [i[2] for i in self.movement] # 関数のみ.
    self.acting_time = [0 for i in range(len(self.act_name_list))] # 実行中の動作の経過時間
    self.acting_movement = [False for i in range(len(self.act_name_list))] # 実行中の動作
# Sprite
    self.part = pyglet.sprite.Sprite(self.parts_img, x=self.previous_part_xyr[0], y=self.previous_part_xyr[1], batch=batch)
    self.part.rotation += self.previous_part_xyr[2]

    self.children_execution = [] # 子のデータ実行.
    for name in self.children_parts_name:
      self.children_execution.append(mooven(name, self.setting_dir, self.parts_image_dir_path, batch))

  def children_exe(self):
    r = self.part.rotation - self.previous_part_xyr[2]
    x = self.part.x - self.previous_part_xyr[0]
    y = self.part.y - self.previous_part_xyr[1]
    for i in self.children_execution:
      i.draw(self.dt, x, y, r)

  def d_rotation(self, movement=[]):
    """
movementに指定されたやつの動作を開始する
その後現在動作中の動きを処理する
    """
    def reset_movement():
      self.acting_time[i] = self.movement_data_integral_lower[i]
      self.acting_movement[i] = False

    def do_integral():
      def func_open(x):
        return eval(self.movement[i])
      res, _ = integrate.quad(func=func_open, a=self.acting_time[i], b=execute_integral_upper) # 積分して角の変位を割り出す.
      return res

    delta_omega = 0 # 角の変位.
    for start_mov_name in movement:
      i = self.act_name_list[start_mov_name] # iは数値.
      if not self.acting_movement[i]:
        self.acting_movement[i] = True
      self.acting_time[i] = 0

    for i in range(len(self.acting_movement)):
      if not self.acting_movement[i]:
        continue
      execute_integral_upper = self.acting_time[i] + self.dt # 積分範囲の上限を超えるかどうか確認.
      if execute_integral_upper >= self.movement_data_integral_upper[i]:
        execute_integral_upper = self.movement_data_integral_upper[i]
        delta_omega += do_integral()
        reset_movement()
      else:
        delta_omega += do_integral()
        self.acting_time[i] += self.dt
    self.previous_part_xyr[2] = delta_omega
    return delta_omega

  def move_new_xy(self):
    self.part.x += self.parents_xyr[0] + self.base_point[0]*math.cos(self.parents_xyr[0])
    self.part.y += self.parents_xyr[1] + self.base_point[1]*math.sin(self.parents_xyr[1])

  def receive_move(self):
    if self.test_flag:
      self.test_flag = False
      self.part.rotation += self.d_rotation(movement=["test_2_rotate"])
    else:
      self.part.rotation += self.d_rotation(movement=[])
    self.children_exe()

  def draw(self, dt, px, py, pr): # px, py, pr, 親の部品のx, y座標, 角の変位.
    self.dt = dt # このフレームでのΔtが何秒か, 親部品のx, y座標, 角度.
    self.parents_xyr[0] += px
    self.parents_xyr[1] += py
    self.parents_xyr[2] += pr
    self.part.x += self.parents_xyr[0] + self.base_point[0]*math.cos(self.parents_xyr[0])
    self.part.y += self.parents_xyr[1] + self.base_point[1]*math.sin(self.parents_xyr[1])
    self.part.rotation += pr
    self.receive_move()