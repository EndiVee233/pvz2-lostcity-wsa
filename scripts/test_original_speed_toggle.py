"""WSA integration check; requires the v9 test game already inside an active level."""
from pathlib import Path
import json
import subprocess
import time
from read_game_speed import read_speed

base=Path(__file__).resolve().parents[1]
folder=base/'rebuild_project/logs/wsa/original-speed'
adb=['K:/pvz2-tools/platform-tools/adb.exe','-s','127.0.0.1:58526']
def call(*args):return subprocess.check_output([*adb,*args],timeout=30)
values=[read_speed()]
assert values==[1.0]
for target,name in [(2.0,'v9-speed-2x.png'),(1.0,'v9-speed-1x.png')]:
    call('shell','input','tap','1239','480')
    value=read_speed()
    for _ in range(10):
        if value==target:break
        time.sleep(0.1);value=read_speed()
    assert value==target,(value,target)
    values.append(value)
    (folder/name).write_bytes(call('exec-out','screencap','-p'))
call('shell','input','tap','1319','479')
record=dict(actual_game_speed_sequence=values,read_only_process_observation=True,
            changed_via_real_touch_events=True,game_left_paused=True)
(base/'native_analysis/original_speed_button/toggle-wsa-validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
