#!/usr/bin/env python3
"""Add the same Planet Vikler HD SDL light pass to the Windows native engine."""
from pathlib import Path
import shutil
src=Path("SpaceCadetPinball/SpaceCadetPinball/render.cpp")
s=src.read_text()
assert "void render::PresentVScreen()" in s
assert "#include \"winmain.h\"" in s
s=s.replace('#include "winmain.h"','#include "winmain.h"\n#include "pinball.h"',1)
s=s.replace('void render::PresentVScreen()', '''// Lazy-loaded additive RGBA light layer. Never touches native ball/collision state.
static SDL_Texture* planetHdGlow = nullptr;
static bool planetHdAttempted = false;

void render::PresentVScreen()''',1)
anchor='''\tif (options::Options.DebugOverlay)
\t{
\t\tDebugOverlay::DrawOverlay();
\t}'''
assert anchor in s
code='''    if (!planetHdAttempted) {
        planetHdAttempted=true;
        auto surface=SDL_LoadBMP(pinball::make_path_name("HD_GLOW.BMP").c_str());
        if (surface) {
            planetHdGlow=SDL_CreateTextureFromSurface(winmain::Renderer,surface);
            SDL_FreeSurface(surface);
            if (planetHdGlow) SDL_SetTextureBlendMode(planetHdGlow,SDL_BLENDMODE_ADD);
        }
    }
    if (planetHdGlow && pb::MainTable && vscreen) {
        float ratio=static_cast<float>(pb::MainTable->Width)/vscreen->Width;
        SDL_Rect rect={
            DestinationRect.x+static_cast<int>(round(offset_x*fullscrn::ScaleX)),
            DestinationRect.y+static_cast<int>(round(offset_y*fullscrn::ScaleY)),
            static_cast<int>(round(DestinationRect.w*ratio)),
            DestinationRect.h
        };
        SDL_SetTextureAlphaMod(planetHdGlow,180);
        SDL_RenderCopy(winmain::Renderer,planetHdGlow,nullptr,&rect);
    }
'''
s=s.replace(anchor,code+anchor,1)
src.write_text(s)
print("Patched Windows renderer. No gameplay or physics files changed.")
