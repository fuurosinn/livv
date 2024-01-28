import os
import json
from PyMooven import mooven

from copy import deepcopy
from random import randint

class MidMooven:
    def __init__(self, move_setting_dir, obj_name, img_dir, bat):
        self.move_setting_dir = os.path.join(move_setting_dir, obj_name)
        with open(self.move_setting_dir+r"./parts.json", mode="r") as f:
            self.based = json.load(f) # 全ての部品のデータ読み込み.
        self.based_parts_name = self.based["based_parts_name"] # 一番最初に配置される部品名を読み込み.
        self.based_parts_xyr = self.based["based_parts_xyr"] # 初期座標と回転読み込み.
        self.move_base = deepcopy(self.based_parts_xyr)
        self.parts_img_dir_path = os.path.join(img_dir, obj_name) # オブジェクトの画像ディレクトリの位置.
        self.based_parts_execution = mooven(this_parts_name=self.based_parts_name, setting_dir=self.move_setting_dir, parts_image_dir_path=self.parts_img_dir_path, bat=bat, pxy=self.based_parts_xyr, parents_anchor=[0, 0])

    def draw(self, dt):
        self.move_base = [i + randint(-5, 5) for i in self.based_parts_xyr] 
        self.based_parts_execution.draw(dt, self.move_base)
#        self.based_parts_execution.draw(dt, self.based_parts_xyr)