#!/usr/bin/env python
"""Build MEMRES-to-CGAR.pptx from the rendered PDF pages (image-faithful)
plus a final clickable 'Sources' slide for all raster images."""
import glob, os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, os.pardir, "MEMRES-to-CGAR.pptx")

W = Inches(13.333)   # 16:9
H = Inches(7.5)

prs = Presentation()
prs.slide_width  = W
prs.slide_height = H
blank = prs.slide_layouts[6]

imgs = sorted(glob.glob(os.path.join(HERE, "s-*.png")))
for img in imgs:
    s = prs.slides.add_slide(blank)
    s.shapes.add_picture(img, 0, 0, width=W, height=H)

# ---- final 'Sources' slide: all raster-image links, clickable ----
NAVY = RGBColor(0x23, 0x37, 0x3B)
ORANGE = RGBColor(0xEB, 0x81, 0x1B)
GRAY = RGBColor(0x66, 0x66, 0x66)

sources = [
    ("Logo HCMUS",                       "https://www.hcmus.edu.vn"),
    ("Logo FSE 2026",                    "https://conf.researchr.org/home/fse-2026"),
    ("Figure: MEMRES pipeline (paper)",  "https://arxiv.org/abs/2604.16941"),
    ("Minh hoa AI: CGAR overview",       "https://chatgpt.com/share/6a2a3c91-5640-83ec-8761-25876b30abe3"),
    ("Minh hoa AI: Session learning",    "https://chatgpt.com/share/6a2a3c8b-93f8-83ec-9452-052ef1ef7e87"),
]

s = prs.slides.add_slide(blank)
# title
tb = s.shapes.add_textbox(Inches(0.7), Inches(0.5), Inches(12), Inches(0.9))
p = tb.text_frame.paragraphs[0]
r = p.add_run(); r.text = "Nguon hinh anh / Image sources"
r.font.size = Pt(28); r.font.bold = True; r.font.color.rgb = NAVY

# body
body = s.shapes.add_textbox(Inches(0.9), Inches(1.7), Inches(11.5), Inches(5.2))
tf = body.text_frame; tf.word_wrap = True
for i, (label, url) in enumerate(sources):
    para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    para.space_after = Pt(12)
    r1 = para.add_run(); r1.text = f"{label}:  "
    r1.font.size = Pt(16); r1.font.bold = True; r1.font.color.rgb = NAVY
    r2 = para.add_run(); r2.text = url
    r2.font.size = Pt(16); r2.font.color.rgb = ORANGE
    r2.hyperlink.address = url

note = s.shapes.add_textbox(Inches(0.9), Inches(6.7), Inches(11.5), Inches(0.6))
np = note.text_frame.paragraphs[0]
nr = np.add_run()
nr.text = ("Anh AI: link toi cuoc tro chuyen ChatGPT da sinh anh. "
           "Hinh tu paper / logo: link nguon chinh thuc.")
nr.font.size = Pt(11); nr.font.italic = True; nr.font.color.rgb = GRAY

prs.save(OUT)
print("Saved:", os.path.normpath(OUT))
print("Slides:", len(prs.slides._sldIdLst))
