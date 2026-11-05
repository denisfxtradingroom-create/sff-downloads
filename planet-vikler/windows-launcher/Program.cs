using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

namespace PlanetViklerRemaster;

public static class Program {
    [STAThread] public static void Main() {
        Application.EnableVisualStyles();
        Application.Run(new LauncherWindow());
    }
}

public sealed class LauncherWindow: Form {
    private readonly Color white=Color.FromArgb(235,248,255);
    private readonly Color cyan=Color.FromArgb(99,226,247);
    private readonly Color gold=Color.FromArgb(246,203,137);
    public LauncherWindow() {
        Text="PLANET VIKLER  •  HD REMASTER";
        FormBorderStyle=FormBorderStyle.FixedSingle;
        MaximizeBox=false;
        DoubleBuffered=true;
        ClientSize=new Size(520,710);
        StartPosition=FormStartPosition.CenterScreen;
        BackColor=Color.FromArgb(4,13,30);
        var logo=Label("✦",64,gold,new Rectangle(0,83,520,85));
        var title=Label("PLANET VIKLER",40,white,new Rectangle(12,175,496,62));
        var edition=Label("H D   R E M A S T E R   ·   2 0 2 6",14,cyan,new Rectangle(0,237,520,39));
        var slogan=Label("SVAKI UDAR MENJA ORBITU",13,Color.FromArgb(155,190,211),new Rectangle(0,294,520,45));
        Controls.AddRange(new Control[]{logo,title,edition,slogan});
        AddButton("▶   IGRAJ",360,true,()=>{
            string executable=Path.Combine(AppContext.BaseDirectory,"SpaceCadetPinball.exe");
            if(!File.Exists(executable)){
                MessageBox.Show("Native engine nije pronađen uz pokretač.","Planet Vikler",MessageBoxButtons.OK,MessageBoxIcon.Error);
                return;
            }
            Process.Start(new ProcessStartInfo(executable){WorkingDirectory=AppContext.BaseDirectory,UseShellExecute=true});
        });
        AddButton("⚙   PODEŠAVANJA / KONTROLE",440,false,()=>{
            MessageBox.Show("U igri otvori meni OPTIONS za zvuk, kontrole i rezoluciju.\n\nZ / levi Shift: levi fliper\n/ : desni fliper\nSPACE: lansiranje kuglice\nX / . : TILT\nF2: nova igra",
                "Planet Vikler HD • Podešavanja",MessageBoxButtons.OK,MessageBoxIcon.Information);
        });
        AddButton("✕   IZLAZ",520,false,Close);
        Controls.Add(Label("NATIVE SDL ENGINE   •   OFFLINE   •   WINDOWS",11,
            Color.FromArgb(126,160,188),new Rectangle(0,625,520,36)));
    }
    private Label Label(string s,float size,Color color,Rectangle bounds) {
        return new Label{Text=s,Bounds=bounds,TextAlign=ContentAlignment.MiddleCenter,ForeColor=color,
            BackColor=Color.Transparent,Font=new Font("Segoe UI",size,
            size>=40?FontStyle.Bold:FontStyle.Regular,GraphicsUnit.Pixel)};
    }
    private void AddButton(string title,int y,bool primary,Action click) {
        var b=new Button{
            Bounds=new Rectangle(90,y,340,62),FlatStyle=FlatStyle.Flat,
            ForeColor=primary?Color.FromArgb(2,18,30):white,
            BackColor=primary?Color.FromArgb(83,223,237):Color.FromArgb(24,55,78),
            Font=new Font("Segoe UI Semibold",17,FontStyle.Bold,GraphicsUnit.Pixel),
            Text=title,Cursor=Cursors.Hand
        };
        b.FlatAppearance.BorderSize=1;
        b.FlatAppearance.BorderColor=primary?Color.FromArgb(190,250,255):Color.FromArgb(63,140,173);
        b.Click+=(_,_)=>click();
        Controls.Add(b);
    }
    protected override void OnPaintBackground(PaintEventArgs e) {
        base.OnPaintBackground(e);
        var g=e.Graphics;g.SmoothingMode=SmoothingMode.AntiAlias;
        using var bg=new LinearGradientBrush(ClientRectangle,Color.FromArgb(3,10,24),
            Color.FromArgb(22,9,50),LinearGradientMode.ForwardDiagonal);
        g.FillRectangle(bg,ClientRectangle);
        for(int i=0;i<5;i++){
            using var pen=new Pen(Color.FromArgb(i%2==0?48:28,i%2==0?81:226,i%2==0?200:69,
                i%2==0?238:190),i%2==0?2:1);
            g.DrawEllipse(pen,-150+i*26,120+i*12,830-i*52,530-i*20);
        }
        var stars=new Random(2026);
        for(int i=0;i<72;i++){
            float x=stars.Next(ClientSize.Width),y=stars.Next(ClientSize.Height);
            using var brush=new SolidBrush(Color.FromArgb(stars.Next(50,130),171,222,255));
            g.FillEllipse(brush,x,y,stars.Next(1,3),stars.Next(1,3));
        }
    }
}