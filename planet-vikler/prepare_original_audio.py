#!/usr/bin/env python3
"""Prepare a self-contained offline Planet Vikler Android game.

The engine/Android JNI implementation is fexed/Pinball-on-Android (MIT).
Game-table artwork is from andrewnakas/open-cadet (CC0).
Audio assets for personal playback are copied from the public fexed Android port.
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

# Keep the user's working Open Cadet game table, replace only sound and music.
# Take the existing audio assets directly from the source port before clearing
# that tree. We do not commit audio bytes to our GitHub repository.
cache=Path("upstream_audio_cache")
if cache.exists():
    shutil.rmtree(cache)
cache.mkdir()
source_sounds=sorted(assets.glob("SOUND*.WAV"))
assert len(source_sounds) >= 60, f"Expected 60 source WAV files, got {len(source_sounds)}"
for f in source_sounds:
    shutil.copy2(f, cache/f.name)
source_music=assets/"PINBALL.mp3"
assert source_music.exists() and source_music.stat().st_size>10_000_000, "Expected soundtrack in upstream Android port"
shutil.copy2(source_music, cache/"PINBALL.mp3")
if assets.exists():
    shutil.rmtree(assets)
assets.mkdir(parents=True)
shutil.copy2(data/"PINBALL.DAT",assets/"PINBALL.DAT")
# CC0 fallback only for sound names absent in the source port; all 60 upstream
# WAVs override CC0 names. The CC0 geometry and gameplay remain unchanged.
for f in data.glob("sound*.wav"):
    shutil.copy2(f, assets/f.name.upper())
for f in source_sounds:
    shutil.copy2(cache/f.name, assets/f.name)
shutil.copy2(cache/"PINBALL.mp3", assets/"PINBALL.mp3")
print("Original port WAV effects:",len(source_sounds))
print("Total playable WAVs:",len(list(assets.glob("SOUND*.WAV"))))
print("Soundtrack bytes:", (assets/"PINBALL.mp3").stat().st_size)

app_gradle=root/"app/build.gradle"
s=app_gradle.read_text()
s=s.replace("id 'com.google.gms.google-services'","")
s=s.replace('applicationId "com.fexed.spacecadetpinball"',
            'applicationId "com.planetvikler.originaloffline"')
s=s.replace('versionName "2.5"','versionName "1.1.0"')
s=s.replace('versionCode 23','versionCode 1')
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
s="\n".join(line for line in s.split("\n") if "firebaseAnalytics.logEvent" not in line)
assert "firebaseAnalytics" not in s and "FirebaseAnalytics" not in s
# The upstream source only copied assets on the first installation.
# Versioned extraction ensures updates actually replace stale WAV files.
start=s.index("    private void copyAssets(File filesDir) {")
end=s.index("    private void setFullscreen()",start)
assert start>=0 and end>start, "Upstream copyAssets implementation moved; review manually"
replacement=r'''    private void copyAssets(File filesDir) {
        android.content.SharedPreferences versionPrefs =
                getSharedPreferences("planet_vikler_asset_version", Context.MODE_PRIVATE);
        final String version = "original_audio_v1";
        if (version.equals(versionPrefs.getString("installed", ""))) {
            return;
        }
        AssetManager assetManager = getAssets();
        try {
            String[] assetNames = assetManager.list("");
            if (assetNames == null) {
                throw new IOException("No packaged game audio assets");
            }
            for (String asset : assetNames) {
                if (!asset.equals("PINBALL.DAT") && !asset.endsWith(".WAV")) {
                    continue;
                }
                File destination = new File(filesDir, asset);
                try (InputStream in = assetManager.open(asset);
                     OutputStream out = new FileOutputStream(destination)) {
                    byte[] buffer = new byte[65536];
                    int n;
                    while ((n = in.read(buffer)) != -1) {
                        out.write(buffer, 0, n);
                    }
                }
            }
            versionPrefs.edit().putString("installed", version).apply();
            Log.i(TAG, "Planet Vikler original audio assets ready");
        } catch (IOException e) {
            Log.e(TAG, "Cannot extract packaged audio assets", e);
        }
    }

'''
s=s[:start]+replacement+s[end:]

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

# More polyphonic sound channels avoid silencing the oldest collisions during
# cascades of bumpers and ramp events. Keep audio hardware format unchanged.
opts=root/"SpaceCadetPinball/options.h"
s=opts.read_text()
assert "DefSoundChannels = 8" in s
opts.write_text(s.replace("DefSoundChannels = 8","DefSoundChannels = 24"))

# File-open check must be binary-safe for the original WAV assets.
sound_file=root/"SpaceCadetPinball/Sound.cpp"
s=sound_file.read_text()
assert 'fopen(lpName.c_str(), "r")' in s
sound_file.write_text(s.replace('fopen(lpName.c_str(), "r")','fopen(lpName.c_str(), "rb")'))

# A duplicated duration calculation in upstream loader reads an uninitialized
# WAV header when a file is missing; do not change collisions, only this guard.
loader=root/"SpaceCadetPinball/loader.cpp"
s=loader.read_text()
duplicate='''\t\t\t\tsound_list[soundIndex].Duration = duration;

\t\t\t\tauto sampleCount = wavHeader.data_size / (wavHeader.channels * (wavHeader.bits_per_sample / 8.0));
\t\t\t\tsound_list[soundIndex].Duration = static_cast<float>(sampleCount / wavHeader.sample_rate);
'''
assert duplicate in s, "Loader duration block changed; investigate before replacing"
s=s.replace(duplicate,'\t\t\t\tsound_list[soundIndex].Duration = duration;\n')
loader.write_text(s)

# Verify all final assets before invoking Gradle.
assert len(list(assets.glob("SOUND*.WAV")))>=60
assert (assets/"PINBALL.mp3").stat().st_size>10_000_000
print("Planet Vikler ORIGINAL AUDIO offline source prepared.")
