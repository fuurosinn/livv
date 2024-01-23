import os
import json
from PyMooven import mooven

class MidMooven:
    def __init__(self, move_setting_dir, obj_name, img_dir, bat):
        self.move_setting_dir = os.path.join(move_setting_dir, obj_name)
        with open(self.move_setting_dir+r"./parts.json", mode="r") as f:
            self.based = json.load(f) # 全ての部品のデータ読み込み.
        self.based_parts_name = self.based["based_parts_name"] # 一番最初に配置される部品名を読み込み.
        self.based_parts_xyr = self.based["based_parts_xyr"] # 初期座標と回転読み込み.
        self.parts_img_dir_path = os.path.join(img_dir, obj_name) # オブジェクトの画像ディレクトリの位置.
        self.based_parts_execution = mooven(this_parts_name=self.based_parts_name, setting_dir=self.move_setting_dir, parts_image_dir_path=self.parts_img_dir_path, bat=bat, pxyr=self.based_parts_xyr)

    def draw(self, dt):
        self.based_parts_execution.draw(dt, 0, 0, 0)