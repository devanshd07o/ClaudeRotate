import json
import subprocess
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'accounts_config.json')

with open(CONFIG_FILE, encoding='utf-8') as f:
    data = json.load(f)

chrome = data.get('chrome_exe', r'C:\Program Files\Google\Chrome\Application\chrome.exe')
accounts = [a for a in data['accounts'] if a.get('active', True)]

print(f'Opening {len(accounts)} Chrome profiles...')
for i, acc in enumerate(accounts):
    profile = acc['chrome_profile']
    cmd = [chrome, f'--profile-directory={profile}', '--new-window', 'https://claude.ai/new']
    print(f'  Opening {profile}')
    subprocess.Popen(cmd)
    time.sleep(1)

print('All profiles opened! Please configure the extension.')
