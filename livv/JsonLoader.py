import json
from os.path import join

def Loader(dir="./setting", pn=None):
    """
pn:parts name
いちいち部品の情報の読み込み記述するのがめんどいので関数にした。
    """
    try:
        with open(join(dir, pn)) as f:
            temp = json.load(f)
    except:
        return False
    return temp