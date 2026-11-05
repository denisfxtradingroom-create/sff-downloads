package com.fexed.spacecadetpinball;

import android.content.Context;
import android.content.Intent;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;

/**
 * Planet Vikler's own premium home menu. This is deliberately separate from
 * the SDL game loop: it never changes table physics, geometry or controls.
 */
public final class PremiumLauncher extends AppCompatActivity {
    private static final int WHITE = Color.rgb(235, 246, 255);
    private static final int CYAN = Color.rgb(80, 232, 251);
    private static final int GOLD = Color.rgb(248, 197, 116);
    private final int dp(float value) { return Math.round(getResources().getDisplayMetrics().density * value); }

    private GradientDrawable surface(int top, int bottom, int stroke, int radius) {
        GradientDrawable out = new GradientDrawable(
            GradientDrawable.Orientation.TL_BR, new int[] {top, bottom});
        out.setCornerRadius(dp(radius));
        out.setStroke(dp(1), stroke);
        return out;
    }

    private TextView text(String label, int size, int color, boolean bold) {
        TextView v = new TextView(this);
        v.setText(label);
        v.setTextColor(color);
        v.setTextSize(size);
        v.setGravity(Gravity.CENTER);
        v.setTypeface(bold ? Typeface.create("sans-serif-medium", Typeface.BOLD) :
                Typeface.create("sans-serif", Typeface.NORMAL));
        return v;
    }

    private TextView menuButton(String label, boolean primary, Runnable action) {
        TextView v = text(label, 18, primary ? Color.rgb(7, 19, 37) : WHITE, true);
        v.setBackground(surface(primary ? Color.rgb(141, 249, 255) : Color.rgb(22, 49, 70),
            primary ? Color.rgb(45, 162, 214) : Color.rgb(11, 29, 51),
            primary ? Color.rgb(211, 252, 255) : Color.rgb(55, 136, 165), 19));
        v.setElevation(dp(6));
        v.setOnClickListener(w -> action.run());
        return v;
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        PrefsHelper.setPrefs(getSharedPreferences("com.fexed.spacecadetpinball", Context.MODE_PRIVATE));
        getWindow().setStatusBarColor(Color.rgb(3, 9, 21));
        getWindow().setNavigationBarColor(Color.rgb(3, 9, 21));

        FrameLayout background = new FrameLayout(this);
        background.setBackgroundColor(Color.rgb(3, 9, 21));
        background.addView(new NebulaBackdrop(this),
            new FrameLayout.LayoutParams(-1, -1));

        LinearLayout content = new LinearLayout(this);
        content.setGravity(Gravity.CENTER_HORIZONTAL);
        content.setPadding(dp(28), dp(16), dp(28), dp(30));
        content.setOrientation(LinearLayout.VERTICAL);
        FrameLayout.LayoutParams frame=new FrameLayout.LayoutParams(
            -1, -2, Gravity.CENTER);
        background.addView(content, frame);

        TextView symbol = text("✦", 68, GOLD, true);
        content.addView(symbol, new LinearLayout.LayoutParams(-1, dp(90)));
        TextView brand = text("PLANET\nVIKLER", 42, WHITE, true);
        brand.setLineSpacing(dp(0), 0.9f);
        content.addView(brand, new LinearLayout.LayoutParams(-1, dp(106)));
        TextView edition = text("H D  R E M A S T E R   ·   2 0 2 6", 12, CYAN, true);
        LinearLayout.LayoutParams ed = new LinearLayout.LayoutParams(-1, dp(45));
        ed.bottomMargin=dp(10);
        content.addView(edition, ed);
        TextView tagline = text("SVAKI UDAR MENJA ORBITU", 12,
            Color.rgb(177, 194, 211), false);
        content.addView(tagline, new LinearLayout.LayoutParams(-1, dp(40)));
        View space=new View(this);
        content.addView(space, new LinearLayout.LayoutParams(-1, dp(40)));
        TextView start=menuButton("▶  IGRAJ", true, () -> {
            startActivity(new Intent(this, MainActivity.class));
        });
        LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(-1, dp(62));
        bp.bottomMargin=dp(14);
        content.addView(start,bp);
        TextView options=menuButton("⚙  PODEŠAVANJA", false, () ->
            startActivity(new Intent(this, Settings.class)));
        LinearLayout.LayoutParams op=new LinearLayout.LayoutParams(-1, dp(60));
        op.bottomMargin=dp(14);
        content.addView(options,op);
        TextView help=menuButton("ⓘ  KONTROLE / POMOĆ", false, () -> {
            new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("PLANET VIKLER · KONTROLE")
                .setMessage("LEVO / DESNO: flipperi\nLANSIRAJ: zadrži pa pusti\nTILT: lagano pomeri sto\nPAUZA: zaustavi partiju\n\nOriginalni Space Cadet gameplay i fizika ostaju nepromenjeni.")
                .setPositiveButton("RAZUMEM", (dialog, which)->{})
                .show();
        });
        content.addView(help,new LinearLayout.LayoutParams(-1,dp(60)));
        View lower=new View(this);
        content.addView(lower,new LinearLayout.LayoutParams(-1,dp(30)));
        TextView footer=text("NATIVE ENGINE  •  OFFLINE  •  ANDROID",11,
            Color.rgb(106, 153, 175),false);
        content.addView(footer,new LinearLayout.LayoutParams(-1,dp(28)));
        setContentView(background);
    }

    private static final class NebulaBackdrop extends View {
        private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
        NebulaBackdrop(Context context) {super(context);}
        @Override protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            float w=getWidth(), h=getHeight();
            paint.setShader(new LinearGradient(0,0,w,h,
                new int[]{Color.rgb(2,9,24),Color.rgb(8,31,62),Color.rgb(23,8,53),Color.rgb(2,9,24)},
                null,Shader.TileMode.CLAMP));
            canvas.drawRect(0,0,w,h,paint);paint.setShader(null);
            // Cosmetic orbit arcs, not game colliders.
            paint.setStyle(Paint.Style.STROKE);
            for(int i=0;i<4;i++){
                paint.setStrokeWidth(i%2==0?2:1);
                paint.setColor((i%2==0?0x447EDFF0:0x44ED5CC7));
                float f=(i+1)*34f;
                canvas.drawOval(-w*.22f+f,h*.08f+f,w*1.15f-f,h*.91f-f,paint);
            }
            paint.setStyle(Paint.Style.FILL);
            for (int i=0;i<65;i++){
                float x=((i*73+41)%439)/439f*w;
                float y=((i*131+11)%619)/619f*h;
                paint.setColor(i%5==0?0xBBE8F2FF:0x5568B7ED);
                canvas.drawCircle(x,y,(i%4==0?1.9f:0.9f),paint);
            }
        }
    }
}