#!/usr/bin/env python3
"""Planet Vikler HD Remaster art/UI layer.
The verified Space Cadet gameplay remains untouched. Audio prepare uses the
same immutable source port as our prior stable Android release.
"""
from pathlib import Path
import runpy, re, struct, math, shutil
runpy.run_path("planet-vikler/prepare_original_audio.py", run_name="__main__")
from PIL import Image, ImageFilter, ImageDraw, ImageChops, ImageEnhance

ROOT=Path("port")
assets=ROOT/"app/src/main/assets"
base=(assets/"PINBALL.DAT").read_bytes()
assert base.startswith(b"PARTOUT(4.0)RESOURCE\0")
head=struct.unpack_from("<21s50s100siHiH",base,0)
group_count=head[4]
assert 500 < group_count < 1000
fields=[]
pos=183+head[6]
for g in range(group_count):
    count=base[pos]; pos+=1
    group=[]
    for j in range(count):
        typ=base[pos];pos+=1
        size=(2 if typ in (0,2) else (0 if typ==13 else None))
        if size is None:
            size=struct.unpack_from("<I",base,pos)[0];pos+=4
        group.append((typ,pos,size))
        pos+=size
    fields.append(group)
assert pos==len(base), ("DAT parser consumed",pos,len(base))
palettes=[item for group in fields for item in group if item[0]==5 and item[2]==1024]
assert len(palettes)==1, "Unexpected palette layout"
pal_start=palettes[0][1]

def pixel_palette(data,base_index):
    start=pal_start+base_index*4
    # Open Cadet uses B,G,R,A in its 32-bit SDL colors on little endian
    b,g,r,a=data[start:start+4]
    return r,g,b,a

def sprite(g):
    record=next((x for x in fields[g] if x[0]==1),None)
    assert record, g
    _,start,sz=record
    res,w,h,x,y,pixels,flags=struct.unpack_from("<BhhhhIB",base,start)
    stride=(w+3)//4*4
    assert pixels==stride*h
    raw=base[start+14:start+14+pixels]
    rgba=[]
    for row in range(h-1,-1,-1):
        rgba.extend(pixel_palette(base,raw[row*stride+i])[:3] for i in range(w))
    out=Image.new("RGB",(w,h))
    out.putdata(rgba)
    return out,(x,y,w,h)

table, (offx,offy,w,h)=sprite(107)
assert (w,h)==(365,470), "Table texture geometry changed"
# The overlay texture is an independent optical lighting layer, not a collider.
scale=3
sharp=table.resize((w*scale,h*scale),Image.Resampling.LANCZOS)
edges=sharp.convert("L").filter(ImageFilter.FIND_EDGES)
edges=edges.point(lambda p:max(0,min(118,(p-28)*2)))
cyan=Image.new("RGB",sharp.size,(25,183,255))
magenta=Image.new("RGB",sharp.size,(255,25,190))
edge_layer=Image.new("RGB",sharp.size,(0,0,0))
# Color position changes the glow, never the coordinates of walls/targets.
top=Image.new("L",sharp.size,0)
draw=ImageDraw.Draw(top)
draw.rectangle((0,0,sharp.width,sharp.height*.42),fill=128)
draw.rectangle((0,sharp.height*.73,sharp.width,sharp.height),fill=100)
colors=Image.composite(magenta,cyan,top)
edge_layer.paste(colors,(0,0),edges)
lamps=Image.new("RGB",sharp.size,(0,0,0))
d=ImageDraw.Draw(lamps)
# Actual component coordinates are obtained from the DAT sprite headers.
for group_id in (372,380,388,396,405,413,421):
    _,(x,y,tw,th)=sprite(group_id)
    cx=(x-offx+tw*.5)*scale
    cy=(y-offy+th*.5)*scale
    radius=(min(tw,th)*.39)*scale
    c=(27,213,255) if group_id%2==0 else (255,55,181)
    d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),outline=c,width=2*scale)
    core=radius*.20
    d.ellipse((cx-core,cy-core,cx+core,cy+core),fill=tuple(v//2 for v in c))
# Highlight only positions already occupied by physical lamp sprites.
for group_id in (115,116,119,122,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,152,153,154,155,156,157,158,159,160):
    rec=next((p for p in fields[group_id] if p[0]==1),None)
    if rec is None: continue
    _,(x,y,tw,th)=sprite(group_id)
    cx=(x-offx+tw*.5)*scale;cy=(y-offy+th*.5)*scale
    if 0<=cx<sharp.width and 0<=cy<sharp.height:
        r=max(1.5, min(tw,th)*.20)*scale
        c=(42,204,253) if group_id%3 else (254,86,224)
        d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=c)
haloA=lamps.filter(ImageFilter.GaussianBlur(radius=6*scale))
haloB=lamps.filter(ImageFilter.GaussianBlur(radius=16*scale))
edge_halo=edge_layer.filter(ImageFilter.GaussianBlur(radius=3*scale))
glow=ImageChops.add(lamps,ImageEnhance.Brightness(haloA).enhance(1.75))
glow=ImageChops.add(glow,ImageEnhance.Brightness(haloB).enhance(.9))
glow=ImageChops.add(glow,edge_halo)
glow=ImageChops.add(glow,ImageEnhance.Brightness(edge_layer).enhance(.25))
glow.save(assets/"HD_GLOW.BMP",format="BMP")
# This is an art-alignment preview, not a screenshot of running gameplay.
ImageChops.add(sharp,ImageEnhance.Brightness(glow).enhance(.65)).save("planet-vikler-hd-alignment.png")

# Palette-only color grade improves chrome and ambient metallic surfaces.
# Every byte outside the 1024-byte color palette is bit-identical to the
# stable CC0 table. Geometry/z-maps/physics/coordinates are unchanged.
out=bytearray(base)
for i in range(256):
    r,g,b,a=pixel_palette(base,i)
    if a==0: continue
    lum=max(r,g,b)
    # Preserve true black passages. Avoid turning empty holes into surfaces.
    if lum<19: continue
    sat=max(r,g,b)-min(r,g,b)
    if b>r+14 and b>g*.90:
        r=min(255,int(r*1.12+2))
        g=min(255,int(g*1.15+4))
        b=min(255,int(b*1.16+6))
    elif r>g+15 and r>b+12:
        r=min(255,int(r*1.18+5))
        b=min(255,int(b*1.34+7))
        g=int(g*.86)
    elif sat<36 and lum>=48:
        r=min(255,int(r*1.09+5))
        g=min(255,int(g*1.13+7))
        b=min(255,int(b*1.16+9))
    else:
        r=min(255,int(r*1.06)); g=min(255,int(g*1.09))
        b=min(255,int(b*1.08))
    out[pal_start+i*4:pal_start+i*4+4]=bytes([b,g,r,a])
assert out[:pal_start]==base[:pal_start]
assert out[pal_start+1024:]==base[pal_start+1024:]
(assets/"PINBALL.DAT").write_bytes(out)
print("DAT only palette changed:",sum(u!=v for u,v in zip(out,base)),"bytes /",len(base))
print("HD additive overlay:",(assets/"HD_GLOW.BMP").stat().st_size,"bytes")

# Surgical SDL postprocess: additive glow, table-only; no gameplay changes.
render=ROOT/"SpaceCadetPinball/render.cpp"
s=render.read_text()
assert "void render::PresentVScreen()" in s
assert "void render::init(" in s and "void render::uninit()" in s
s=s.replace('#include "winmain.h"','#include "winmain.h"\n#include "pinball.h"')
s=s.replace("std::vector<render_sprite_type_struct*> render::dirty_list",
    "static SDL_Texture* hdRemasterGlow = nullptr;\nstd::vector<render_sprite_type_struct*> render::dirty_list",1)
anchor="\trecreate_screen_texture();"
assert anchor in s
s=s.replace(anchor,'''    recreate_screen_texture();
    auto hdSurface = SDL_LoadBMP(pinball::make_path_name("HD_GLOW.BMP").c_str());
    if (hdSurface != nullptr) {
        hdRemasterGlow = SDL_CreateTextureFromSurface(winmain::Renderer, hdSurface);
        SDL_FreeSurface(hdSurface);
        if (hdRemasterGlow) SDL_SetTextureBlendMode(hdRemasterGlow, SDL_BLENDMODE_ADD);
    }
''',1)
anchor="\tSDL_DestroyTexture(vScreenTex);"
assert anchor in s
s=s.replace(anchor,'''    SDL_DestroyTexture(hdRemasterGlow);
    hdRemasterGlow = nullptr;
    SDL_DestroyTexture(vScreenTex);''',1)
start=s.index("void render::PresentVScreen()")
openbrace=s.index("{",start)
depth=0;end=None
for j in range(openbrace,len(s)):
    if s[j]=='{':depth+=1
    elif s[j]=='}':
        depth-=1
        if depth==0:end=j;break
assert end is not None
addition='''
    // Cosmetic HD LED pass. Same screen rectangle, no additional collider.
    if (hdRemasterGlow != nullptr && pb::MainTable && vscreen) {
        const float ratio = static_cast<float>(pb::MainTable->Width) / vscreen->Width;
        SDL_Rect tableRect = {
            DestinationRect.x + static_cast<int>(round(offset_x * fullscrn::ScaleX)),
            DestinationRect.y + static_cast<int>(round(offset_y * fullscrn::ScaleY)),
            static_cast<int>(round(DestinationRect.w * ratio)),
            DestinationRect.h
        };
        // Subtle LED pulse, stable on both GLES/desktop SDL.
        const float pulse=static_cast<float>(sin(SDL_GetTicks()*0.0014));
        SDL_SetTextureAlphaMod(hdRemasterGlow,static_cast<Uint8>(175+17*pulse));
        SDL_RenderCopy(winmain::Renderer,hdRemasterGlow,nullptr,&tableRect);
    }
'''
s=s[:end]+addition+s[end:]
render.write_text(s)

# Modern visual controls: original invisible touch hitboxes remain untouched.
java=ROOT/"app/src/main/java/com/fexed/spacecadetpinball/MainActivity.java"
s=java.read_text()
s=s.replace("original_audio_v1","hd_remaster_v1")
s=s.replace('!asset.equals("PINBALL.DAT") && !asset.endsWith(".WAV")',
            '!asset.equals("PINBALL.DAT") && !asset.endsWith(".WAV") && !asset.equals("HD_GLOW.BMP")')
anchor='mBinding.getRoot().bringToFront();'
assert anchor in s
s=s.replace(anchor,anchor+"\n        applyPlanetViklerHud();",1)
method=String_placeholder=""  # replaced by Java code below
# Add visual labels only; no touch listener or native key map is changed.
hud=r'''
    private android.graphics.drawable.GradientDrawable hdGlass(int a,int b,int c) {
        android.graphics.drawable.GradientDrawable g=new android.graphics.drawable.GradientDrawable(
          android.graphics.drawable.GradientDrawable.Orientation.TL_BR,new int[]{a,b});
        g.setCornerRadius(20*getResources().getDisplayMetrics().density);
        g.setStroke(Math.max(1,(int)getResources().getDisplayMetrics().density),c);
        return g;
    }
    private void applyPlanetViklerHud() {
        int cyan=android.graphics.Color.rgb(118,234,255);
        int white=android.graphics.Color.rgb(233,245,255);
        mBinding.txtscore.setTextColor(white);
        mBinding.txtscore.setTextSize(23);
        mBinding.ballstxt.setTextColor(cyan);
        mBinding.infotxt.setTextColor(cyan);
        mBinding.missiontxt.setTextColor(white);
        mBinding.txtscore.setBackground(hdGlass(0xD510243D,0xD5081528,0xAA34B5D8));
        mBinding.missiontxt.setBackground(hdGlass(0xB5142445,0xB50A182D,0x8842C3F5));
        // The full-screen touch targets must stay transparent for the original flipper input.
        mBinding.left.setText("");
        mBinding.right.setText("");
        // Native plunger still receives the full-size touch as before.
        mBinding.tiltLeft.setText("TILT");
        mBinding.tiltRight.setText("TILT");
        mBinding.tiltBottom.setText("TILT");
        for (android.widget.TextView tilt:new android.widget.TextView[]{
            mBinding.tiltLeft,mBinding.tiltRight,mBinding.tiltBottom}) {
            tilt.setTextColor(cyan);
            tilt.setTextSize(10);
            tilt.setBackground(hdGlass(0x55234160,0x55101E36,0x8842A6DC));
        }
        android.widget.LinearLayout dock=new android.widget.LinearLayout(this);
        dock.setOrientation(android.widget.LinearLayout.HORIZONTAL);
        dock.setPadding(12,0,12,10);
        dock.setClickable(false);
        dock.setFocusable(false);
        String[] labels={"◀  LEVO","◆  LANSIRAJ","DESNO  ▶"};
        for (int i=0;i<3;i++){
            android.widget.TextView label=new android.widget.TextView(this);
            label.setText(labels[i]);
            label.setTextSize(i==1?11:13);
            label.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
            label.setTextColor(i==1?0xFFF9D496:0xFFA8EFFC);
            label.setGravity(android.view.Gravity.CENTER);
            label.setClickable(false);label.setFocusable(false);
            label.setBackground(hdGlass(0xC0163C56,0xC00B1E36,0xFF367E9F));
            android.widget.LinearLayout.LayoutParams lp=new android.widget.LinearLayout.LayoutParams(
              0,(int)(40*getResources().getDisplayMetrics().density),i==1?.72f:1f);
            lp.setMargins(4,0,4,0);
            dock.addView(label,lp);
        }
        android.widget.RelativeLayout.LayoutParams params=new android.widget.RelativeLayout.LayoutParams(
            -1,(int)(52*getResources().getDisplayMetrics().density));
        params.addRule(android.widget.RelativeLayout.ALIGN_PARENT_BOTTOM);
        mLayout.addView(dock,params);
        dock.bringToFront();
    }
'''
anchor="    private void copyAssets(File filesDir) {"
assert anchor in s
s=s.replace(anchor,hud+"\n"+anchor,1)
java.write_text(s)

# Existing settings logic/options remain: only its branding and theme change.
settings=ROOT/"app/src/main/java/com/fexed/spacecadetpinball/Settings.java"
s=settings.read_text()
s=s.replace("checkLatestRelease();","// HD offline edition: no remote update check.")
s=s.replace("HighScoreHandler.postScore(getApplicationContext(), false);",
            "// Offline score is already stored locally; do not contact a server.")
anchor="setContentView(view);"
assert anchor in s
s=s.replace(anchor,anchor+"\n        styleHdSettings(mBinding.getRoot());",1)
theme=r'''
    private void styleHdSettings(android.view.View root) {
        getWindow().setStatusBarColor(0xFF071426);
        getWindow().setNavigationBarColor(0xFF071426);
        android.graphics.drawable.GradientDrawable bg =
            new android.graphics.drawable.GradientDrawable(
              android.graphics.drawable.GradientDrawable.Orientation.TL_BR,
              new int[]{0xFF061022,0xFF12334E,0xFF071222});
        root.setBackground(bg);
        root.setPadding(12,16,12,20);
        recolorHdSettings(root);
        mBinding.gplaytxtv.setVisibility(android.view.View.GONE);
        mBinding.githubtxtv.setVisibility(android.view.View.GONE);
        mBinding.rankingbtnlyt.setVisibility(android.view.View.GONE);
    }
    private void recolorHdSettings(android.view.View v) {
        if (v instanceof android.widget.TextView) {
            android.widget.TextView t=(android.widget.TextView)v;
            t.setTextColor(0xFFE9F6FF);
            if (t instanceof android.widget.Button) {
                android.graphics.drawable.GradientDrawable tile =
                   new android.graphics.drawable.GradientDrawable(
                   android.graphics.drawable.GradientDrawable.Orientation.TL_BR,
                   new int[]{0xFF154360,0xFF0C2038});
                tile.setCornerRadius(14*getResources().getDisplayMetrics().density);
                tile.setStroke(1,0xFF3585A9);
                t.setBackground(tile);
            }
        }
        if (v instanceof android.widget.CompoundButton) {
            ((android.widget.CompoundButton)v).setButtonTintList(
                 android.content.res.ColorStateList.valueOf(0xFF6FE8F5));
        }
        if (v instanceof android.view.ViewGroup) {
            android.view.ViewGroup group=(android.view.ViewGroup)v;
            for(int i=0;i<group.getChildCount();i++)recolorHdSettings(group.getChildAt(i));
        }
    }
'''
anchor="    public void checkLatestRelease() {"
assert anchor in s
s=s.replace(anchor,theme+"\n"+anchor,1)
settings.write_text(s)

# New first-party home menu, preserving the actual native SDL game activity.
launcher=Path("planet-vikler/PremiumLauncher.java")
assert launcher.exists()
dest=ROOT/"app/src/main/java/com/fexed/spacecadetpinball/PremiumLauncher.java"
shutil.copyfile(launcher,dest)
manifest=ROOT/"app/src/main/AndroidManifest.xml"
s=manifest.read_text()
pattern=r'(<activity\s+android:name="\.MainActivity".*?android:exported="true">)\s*<intent-filter>.*?</intent-filter>'
s,num=re.subn(pattern,r'\1',s,flags=re.DOTALL)
assert num==1, "Could not safely move launcher intent filter"
insert='''<activity android:name=".PremiumLauncher"
            android:exported="true">
            <intent-filter>
              <action android:name="android.intent.action.MAIN" />
              <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
        '''
assert '<activity' in s
s=s.replace('<activity\n            android:name=".MainActivity"',insert+'<activity\n            android:name=".MainActivity"',1)
assert 'android.permission.INTERNET' not in s
manifest.write_text(s)

gradle=ROOT/"app/build.gradle"
s=gradle.read_text()
assert 'com.planetvikler.originaloffline' in s
s=s.replace("com.planetvikler.originaloffline","com.planetvikler.hdremaster")
s=s.replace('versionName "1.1.0"','versionName "2.0.0"')
gradle.write_text(s)
strings=ROOT/"app/src/main/res/values/strings.xml"
s=strings.read_text()
s=s.replace("Space Cadet Pinball","Planet Vikler HD Remaster")
s=s.replace('<string name="app_name">Planet Vikler</string>',
            '<string name="app_name">Planet Vikler HD</string>')
strings.write_text(s)
print("HD Remaster: original gameplay untouched, Android GUI + native LED pass prepared.")
