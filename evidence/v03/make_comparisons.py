"""Evidence-only layout of original PNGs: labels and resizing, no retouching.

Uses the already installed Pillow for report boards; not a runtime dependency.
"""
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
font=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',22)
small=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',16)
report={}
for scene,old_iteration,title in [('crystal-mine',2,'礦洞'),('woodwork-shop',1,'工作坊')]:
    old=ROOT/'output/v02'/scene/f'iteration-{old_iteration}'
    new=ROOT/'output/v03'/scene/'iteration-2'
    before=json.loads((old/'scene_plan.json').read_text(encoding='utf-8'))
    after=json.loads((new/'scene_plan.json').read_text(encoding='utf-8'))
    changed={key:before[key]!=after[key] for key in ['assets','objects','materials','lights']}
    cameras={role:before['cameras'][i]==after['cameras'][i] for i,role in enumerate(['hero','three_quarter','top'])}
    board=Image.new('RGB',(1536,3*815+50),(24,29,35));draw=ImageDraw.Draw(board)
    draw.text((18,8),title+'｜左：v0.2　右：v0.3　原始渲染並排，無調色或修圖',font=font,fill='white')
    pixel_changes={}
    for row,view in enumerate(['hero','three_quarter','top']):
        for col,folder in enumerate([old,new]):
            img=Image.open(folder/'previews'/(view+'.png')).convert('RGB')
            board.paste(img,(col*768,50+row*815+36))
        left=Image.open(old/'previews'/(view+'.png')).tobytes();right=Image.open(new/'previews'/(view+'.png')).tobytes()
        pixel_changes[view]=hashlib.sha256(left).hexdigest()!=hashlib.sha256(right).hexdigest()
        label=view+('｜相同鏡頭／相同 768px、48 samples' if cameras[view] else '｜次視角已改，非相同鏡頭比較')
        draw.text((18,50+row*815+4),label,font=small,fill='white')
    destination=OUT/(scene+'-comparison.png')
    if destination.exists():raise ValueError('Do not overwrite comparison evidence')
    board.save(destination)
    board.crop((0,0,1536,865)).save(OUT/(scene+'-hero-comparison.png'))
    report[scene]={'substantive_plan_changes':changed,'same_cameras':cameras,
                   'all_three_pixel_payloads_changed':all(pixel_changes.values()),'views':pixel_changes,
                   'before_blend':str(old/'scene.blend'),'after_blend':str(new/'scene.blend'),
                   'retouching':False,'board':str(destination)}
(OUT/'comparison-evidence.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
