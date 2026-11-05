#!/usr/bin/env python3
"""Prepare a self-contained offline Planet Vikler Android game.

The engine/Android JNI implementation is fexed/Pinball-on-Android (MIT).
All bundled game-data files come from andrewnakas/open-cadet (CC0).
No original Microsoft bitmaps or sound files are included.
"""
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import wave
import math
import struct

root=Path("port")
data=Path("open-cadet")
assets=root/"app/src/main/assets"
assert (data/"PINBALL.DAT").stat().st_size > 500000
assert (root/"app/src/main/java/com/fexed/spacecadetpinball/MainActivity.java").exists()

# Do not accidentally redistribute the original Windows XP binary data
# historically bundled in the upstream Android source.
if assets.exists():
    shutil.rmtree(assets)
assets.mkdir(parents=True)
shutil.copy2(data/"PINBALL.DAT",assets/"PINBALL.DAT")
sound_files=sorted(data.glob("sound*.wav"))
assert len(sound_files)>=40, f"Expected CC0 sounds: found {len(sound_files)}"
for f in sound_files:
    shutil.copy2(f, assets/f.name.upper())
print("Copied CC0 assets:", len(sound_files), "WAV sounds and PINBALL.DAT")

# Standalone original ambient music composed algorithmically (not original
# Space Cadet soundtrack). Make it optional in settings; 47 CC0 SFX always work.
music=Path("music.wav")
sample_rate=22050
duration=18
with wave.open(str(music),"wb") as out:
    out.setnchannels(1);out.setsampwidth(2);out.setframerate(sample_rate)
    buf=bytearray()
    for i in range(duration*sample_rate):
        t=i/sample_rate
        env=min(1.0,t/1.0,(duration-t)/1.2)
        wobble=0.65+0.35*math.sin(2*math.pi*0.23*t)**2
        tone=(math.sin(2*math.pi*110*t)+0.26*math.sin(2*math.pi*165*t)
              +0.19*math.sin(2*math.pi*220*t)
              +0.11*math.sin(2*math.pi*440*t))
        buf.extend(struct.pack("<h",int(2400*env*wobble*tone)))
    out.writeframes(buf)
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
    "-i",str(music),"-codec:a","libmp3lame","-q:a","8",
    str(assets/"PINBALL.mp3")],check=True)
music.unlink()
print("Created original offline ambient MP3")

app_gradle=root/"app/build.gradle"
s=app_gradle.read_text()
s=s.replace("id 'com.google.gms.google-services'","")
s=s.replace('applicationId "com.fexed.spacecadetpinball"',
            'applicationId "com.planetvikler.offlinecadet"')
s=s.replace('versionName "2.5"','versionName "1.0.0"')
s=s.replace('versionCode 13','versionCode 1')
s=re.sub(r"(?m)^\s*implementation\s+platform\('com\.google\.firebase:.*\)\s*\n","",s)
s=re.sub(r"(?m)^\s*implementation\s+'com\.google\.firebase:.*'\s*\n","",s)
app_gradle.write_text(s)
top=root/"build.gradle"
top.write_text(re.sub(r"(?m)^\s*classpath 'com\.google\.gms:google-services:.*'\s*\n","",top.read_text()))
(root/"app/google-services.json").unlink(missing_ok=True)

java=root/"app/src/main/java/com/fexed/spacecadetpinball/MainActivity.java"
s=java.read_text()
s=s.replace("import com.google.firebase.analytics.FirebaseAnalytics;","")
s=s.replace("private FirebaseAnalytics firebaseAnalytics;","")
s=s.replace("firebaseAnalytics = FirebaseAnalytics.getInstance(this);","")
s=s.replace("firebaseAnalytics.logEvent(FirebaseAnalytics.Event.APP_OPEN, null);","")
s=s.replace("runOnUiThread(() -> firebaseAnalytics.logEvent(FirebaseAnalytics.Event.LEVEL_START, null));","")
s=s.replace("runOnUiThread(() -> firebaseAnalytics.logEvent(FirebaseAnalytics.Event.LEVEL_END, null));","")
s=s.replace("bndl.putInt(FirebaseAnalytics.Param.SCORE, score);","")
s=s.replace("runOnUiThread(() -> firebaseAnalytics.logEvent(FirebaseAnalytics.Event.POST_SCORE, bndl));","")
# Upstream also logs cheat usage and session totals; keep everything local.
s=re.sub(r"(?m)^.*firebaseAnalytics\\.logEvent\\(.*;\\s*$","",s)
assert "firebaseAnalytics" not in s and "FirebaseAnalytics" not in s
java.write_text(s)
# Keep high scores local, do not submit player data to the upstream scoreboard.
rank=root/"app/src/main/java/com/fexed/spacecadetpinball/HighScoreHandler.java"
s=rank.read_text().replace(
    "if (PrefsHelper.getHighScore() > 0) postScore(context, true);",
    "// Offline edition: local high scores only.")
rank.write_text(s)
manifest=root/"app/src/main/AndroidManifest.xml"
s=manifest.read_text()
s=s.replace('<uses-permission android:name="android.permission.INTERNET" />',"")
s=s.replace('android:allowBackup="true"','android:allowBackup="false"')
s=s.replace('android:icon="@mipmap/icon"','android:icon="@drawable/planet_vikler_icon"')
s=s.replace('android:roundIcon="@mipmap/icon"','android:roundIcon="@drawable/planet_vikler_icon"')
manifest.write_text(s)
values=root/"app/src/main/res/values/strings.xml"
s=values.read_text()
s=s.replace('<string name="app_name">Space Cadet Pinball</string>',
            '<string name="app_name">Planet Vikler</string>')
s=s.replace('<string name="left">Left</string>','<string name="left">LEVO</string>')
s=s.replace('<string name="right">Right</string>','<string name="right">DESNO</string>')
s=s.replace('<string name="plunger">Plunger</string>',
            '<string name="plunger">LANSIRAJ</string>')
s=s.replace('<string name="highscore">High Score</string>',
            '<string name="highscore">Rekord</string>')
s=s.replace('<string name="leaderboard">Online Leaderboard</string>',
            '<string name="leaderboard">Lokalni rekord</string>')
values.write_text(s)

# An original vector game icon: blue planet / pale ring / gold star.
draw=root/"app/src/main/res/drawable"
draw.mkdir(exist_ok=True)
(draw/"planet_vikler_icon.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
 android:width="108dp" android:height="108dp"
 android:viewportWidth="108" android:viewportHeight="108">
 <path android:fillColor="#07162D" android:pathData="M0,0h108v108h-108z"/>
 <path android:fillColor="#125B7A" android:pathData="M54,19a35,35 0,1 0,0 70a35,35 0,1 0,0 -70z"/>
 <path android:fillColor="#41C9EC" android:pathData="M54,25a29,29 0,1 0,0 58a29,29 0,1 0,0 -58z"/>
 <path android:fillColor="#07162D" android:pathData="M54,32a22,22 0,1 0,0 44a22,22 0,1 0,0 -44z"/>
 <path android:strokeColor="#F4D59A" android:strokeWidth="5"
  android:strokeLineCap="round" android:fillColor="#00000000"
  android:pathData="M7,70 C24,90 78,73 100,38"/>
 <path android:fillColor="#F6DCA1"
  android:pathData="M76,14l3,8l8,3l-8,3l-3,8l-3,-8l-8,-3l8,-3z"/>
</vector>""")
# No internet permissions, no remote host, and content is embedded in APK.
assert "android.permission.INTERNET" not in manifest.read_text()
assert (assets/"PINBALL.DAT").is_file()
print("PLANET VIKLER native offline source prepared")
