from PIL import Image # こいつでデータ弄る
import numpy as np # とりあえずimportしとけ
import os # os.path.join()とか色々使う
import math # ネイピア数とかを使用した関数で部品を動かす角度指定しているから必須
from scipy import integrate # 積分して角の変位を決める
import json # 動作設定ファイルが.jsonだから, こいつ無いと読み込めない

import pyglet

from time import sleep

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
#    self.test_flag = False
    if self.this_parts_name == "parts_0":
      self.test_flag = 0
    elif self.this_parts_name == "parts_0_1":
      self.test_flag = 1
    else:
      self.test_flag = -1

  def main_load(self):
    """
各部品の親部品(接続元)を原点として自分の相対座標と角度を計算して親部品に結果を返す
親部品の座標基準でどこに接続しているのかを確認する必要がある。
    """
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
    self.act_name_list = dict(zip(list(self.movement.keys()), list(range(len(self.movement)))))
    self.movement = list(self.movement.values()) # 式の情報だけになる.
    self.movement_data_integral_lower = [i[0] for i in self.movement] # 動作の秒数開始時刻.
    self.movement_data_integral_upper = [i[1] for i in self.movement] # 動作の終了時刻.
    self.movement = [i[2] for i in self.movement] # 関数のみ.
    self.acting_time = [0 for i in range(len(self.act_name_list))] # 実行中の動作の経過時間
    self.acting_movement = [False for i in range(len(self.act_name_list))] # 実行中の動作
    self.inum_connection = complex(self.base_point[0] - self.parents_anchor[0], self.base_point[1] - self.parents_anchor[1]) # cal_xyで使う.
    self.previous_part_xyr = list(self.cal_xy(self.first_parents_xyr[0], self.first_parents_xyr[1], self.first_parents_xyr[2]))
    self.previous_part_xyr.append(self.first_parents_xyr[2] + self.rotate)
# Sprite
    self.part = pyglet.sprite.Sprite(self.parts_img, x=self.previous_part_xyr[0], y=self.previous_part_xyr[1], batch=batch)
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
    self.rotate += delta_omega # 親部品の角と合成されていないこの部品のみの角.
    self.rotate %= 360
    self.part.rotation = self.rotate + self.parents_xyr[2]
    self.part.rotation %= 360

  def receive_move(self):
    if self.test_flag == 0:
      self.test_flag = -1
      self.d_rotation(movement=["test_0_rotate"])
    elif self.test_flag == 1:
      self.test_flag = -1
      self.d_rotation(movement=["test_0_rotate"])
    else:
      self.d_rotation(movement=[])
    self.children_exe()

  def cal_xy(self, px, py, pr):
    """
  prをラジアンに変換してないやん…(n時間消滅)
  jsonの階層ミス(13時間), 致命的なクラス継承のバグ(8時間), ラジアンに変換してない(?日)
    """
#    print(f"{self.this_parts_name}:{pr}")
    pr = math.radians(-pr)
    inum_parents_rotate = complex(math.cos(pr), math.sin(pr))
    xy = self.inum_connection * inum_parents_rotate + complex(px, py)
    return xy.real, xy.imag

  def draw(self, dt, pxyr): # pxyr, 親の部品のx, y座標, 角.
    self.dt = dt # このフレームでのΔtが何秒か, 親部品のx, y座標, 角度.
    self.parents_xyr = pxyr
    self.part.x, self.part.y = self.cal_xy(self.parents_xyr[0], self.parents_xyr[1], self.parents_xyr[2])
    self.receive_move()