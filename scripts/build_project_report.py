
from pathlib import Path
import json, re, textwrap, os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".report-build" / "report_source.md"
OUT = ROOT / "project_report" / "Project_Report_Transportability_Reliability_NIDS.docx"
FIGDIR = ROOT / ".report-build" / "generated_figures"
FIGDIR.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)

def add_page_num(section, fmt):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.text = ""
    r = p.add_run()
    fld1 = OxmlElement("w:fldChar"); fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = "PAGE"
    fld2 = OxmlElement("w:fldChar"); fld2.set(qn("w:fldCharType"), "end")
    r._r.append(fld1); r._r.append(instr); r._r.append(fld2)
    r.font.name = "Times New Roman"; r.font.size = Pt(10)
    sectPr = section._sectPr
    old = sectPr.find(qn("w:pgNumType"))
    if old is not None: sectPr.remove(old)
    pg = OxmlElement("w:pgNumType"); pg.set(qn("w:fmt"), fmt); pg.set(qn("w:start"), "1")
    sectPr.append(pg)

def style_document(doc):
    sec = doc.sections[0]
    for s in doc.sections:
        s.page_width = Cm(21); s.page_height = Cm(29.7)
        s.top_margin = Cm(2.5); s.bottom_margin = Cm(2.5)
        s.left_margin = Cm(2.8); s.right_margin = Cm(2.3)
        s.header_distance = Cm(1.2); s.footer_distance = Cm(1.2)
    styles=doc.styles
    normal=styles["Normal"]; normal.font.name="Times New Roman"; normal.font.size=Pt(12)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.paragraph_format.line_spacing=1.5; normal.paragraph_format.space_after=Pt(6)
    normal.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    for nm,sz in [("Heading 1",16),("Heading 2",14),("Heading 3",12)]:
        st=styles[nm]; st.font.name="Times New Roman"; st.font.size=Pt(sz); st.font.bold=True
        st.font.color.rgb=RGBColor(0,0,0)
        st._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        st.paragraph_format.line_spacing=1.5; st.paragraph_format.space_before=Pt(12 if nm!="Heading 3" else 8)
        st.paragraph_format.space_after=Pt(6); st.paragraph_format.keep_with_next=True
    for name,size,bold,align in [
        ("FrontTitle",16,True,WD_ALIGN_PARAGRAPH.CENTER),
        ("FrontSubtitle",14,True,WD_ALIGN_PARAGRAPH.CENTER),
        ("FrontBody",13,True,WD_ALIGN_PARAGRAPH.CENTER),
        ("Caption",10,True,WD_ALIGN_PARAGRAPH.CENTER),
        ("TOCEntry",11,False,WD_ALIGN_PARAGRAPH.LEFT),
        ("Small",10,False,WD_ALIGN_PARAGRAPH.LEFT),
    ]:
        if name not in styles:
            styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH)
        st=styles[name]; st.font.name="Times New Roman"; st.font.size=Pt(size); st.font.bold=bold
        st.font.color.rgb=RGBColor(0,0,0)
        st.paragraph_format.line_spacing=1.2; st.paragraph_format.space_after=Pt(3)
        st.paragraph_format.alignment=align

def set_cell(cell, text, bold=False, size=9, center=False):
    cell.text=""
    p=cell.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.line_spacing=1.0; p.paragraph_format.space_after=Pt(0)
    r=p.add_run(str(text)); r.bold=bold; r.font.name="Times New Roman"; r.font.size=Pt(size)
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER

def add_table(doc, rows):
    if not rows: return
    table=doc.add_table(rows=len(rows), cols=len(rows[0])); table.style="Table Grid"; table.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,row in enumerate(rows):
        for j,val in enumerate(row):
            set_cell(table.cell(i,j),val,bold=(i==0),size=8.5,center=True if i==0 or j==0 else False)
    # repeat header + no row splitting
    trPr=table.rows[0]._tr.get_or_add_trPr(); h=OxmlElement("w:tblHeader"); h.set(qn("w:val"),"true"); trPr.append(h)
    for row in table.rows:
        trPr=row._tr.get_or_add_trPr(); c=OxmlElement("w:cantSplit"); trPr.append(c)
    doc.add_paragraph()
    return table

def figure_graphical(path):
    fig,ax=plt.subplots(figsize=(11.5,6.6)); ax.set_xlim(0,11.5); ax.set_ylim(0,7); ax.axis("off")
    def box(x,y,w,h,t):
        p=FancyBboxPatch((x,y),w,h,boxstyle="round,pad=.02,rounding_size=.08",fc="0.95",ec="0.25",lw=1.2)
        ax.add_patch(p); ax.text(x+w/2,y+h/2,t,ha="center",va="center",fontsize=9.5,weight="bold")
    def ar(a,b): ax.add_patch(FancyArrowPatch(a,b,arrowstyle="-|>",mutation_scale=14,lw=1.2,color="0.3"))
    box(.3,4.4,2.4,1.1,"NF-UNSW-NB15-v3\n2.37 M flows")
    box(.3,1.6,2.4,1.1,"NF-CSE-CIC-IDS2018-v3\n20.12 M flows")
    box(3.3,2.8,2.3,1.5,"Common 46-feature\npredictive representation")
    box(6.2,2.8,2.3,1.5,"Frozen Random Forest\n200 trees • 10 seeds")
    box(9.1,4.6,2.0,1.0,"5 reliability signals")
    box(9.1,2.7,2.0,1.0,"Bidirectional\nsource-only transfer")
    box(9.1,.8,2.0,1.1,"Attack-miss AUPRC\n+ review budgets")
    ar((2.7,4.95),(3.3,3.8)); ar((2.7,2.15),(3.3,3.35)); ar((5.6,3.55),(6.2,3.55))
    ar((8.5,3.8),(9.1,5.1)); ar((8.5,3.35),(9.1,3.2)); ar((8.5,3.0),(9.1,1.35))
    ax.text(5.75,6.5,"Source-derived reliability under cross-domain transfer",ha="center",fontsize=14,weight="bold")
    ax.text(5.75,.2,"Finding: reliability is direction-, failure-mode-, and budget-dependent.",ha="center",fontsize=10.5,weight="bold")
    fig.tight_layout(); fig.savefig(path,dpi=160,bbox_inches="tight"); plt.close(fig)

def figure_timeline(path):
    ev=[("1970","Chow","Reject option"),("2001","Breiman","Random Forest"),("2008","Liu et al.","Isolation Forest"),
        ("2010","Sommer & Paxson","NIDS realism"),("2015","Moustafa & Slay","UNSW-NB15"),
        ("2018","Sharafaldin et al.","CIC-IDS2018"),("2019","Tibshirani et al.","Conformal under shift"),
        ("2022","Apruzzese et al.","Cross-evaluation"),("2024","Cantone et al.","Cross-dataset"),
        ("2026","Recent studies","Transportability / deployment")]
    fig,ax=plt.subplots(figsize=(12,4)); ax.axhline(0,color="0.3",lw=1.5)
    for i,(yr,a,b) in enumerate(ev):
        y=.55 if i%2==0 else -.55; ax.plot([i,i],[0,y*.7],color="0.45",lw=1)
        ax.scatter([i],[0],s=50,color="0.25")
        ax.text(i,y,yr,ha="center",va="bottom" if y>0 else "top",fontsize=9.5,weight="bold")
        ax.text(i,y+(.14 if y>0 else -.14),a,ha="center",va="bottom" if y>0 else "top",fontsize=7.5)
        ax.text(i,y+(.28 if y>0 else -.28),b,ha="center",va="bottom" if y>0 else "top",fontsize=7.2)
    ax.set_xlim(-.5,len(ev)-.5); ax.set_ylim(-1,1); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_title("Evolution of reliability thinking in network intrusion detection",weight="bold",fontsize=13)
    fig.tight_layout(); fig.savefig(path,dpi=160,bbox_inches="tight"); plt.close(fig)

def figure_design(path):
    fig,ax=plt.subplots(figsize=(11,6)); ax.set_xlim(0,11); ax.set_ylim(0,7); ax.axis("off")
    def box(x,y,w,h,t):
        p=FancyBboxPatch((x,y),w,h,boxstyle="round,pad=.02,rounding_size=.08",fc="0.95",ec="0.25",lw=1.2)
        ax.add_patch(p); ax.text(x+w/2,y+h/2,t,ha="center",va="center",fontsize=9,weight="bold")
    def ar(a,b): ax.add_patch(FancyArrowPatch(a,b,arrowstyle="-|>",mutation_scale=13,lw=1.2,color="0.3"))
    steps=[(.5,5.6,2.0,0.9,"Define failure mode"),(3,5.6,2.0,.9,"Freeze 46 features"),
           (5.5,5.6,2,.9,"Fit source RF"),(8,5.6,2,.9,"Fit reliability layer"),
           (1.7,3.6,2.4,.9,"Freeze source quantities"),(4.7,3.6,2.4,.9,"Transfer to target"),
           (7.7,3.6,2.4,.9,"Rank attack misses"),(3,1.7,2.4,.9,"Compare AUPRC / capture"),
           (6,1.7,2.4,.9,"Reverse direction")]
    for s in steps: box(*s)
    for a,b in [((2.5,6.05),(3,6.05)),((5,6.05),(5.5,6.05)),((7.5,6.05),(8,6.05)),
                ((9,5.6),(9,4.5)),((7.7,4.05),(7.0,4.05)),((4.7,4.05),(4.1,4.05)),
                ((3,3.6),(3,2.6)),((5.4,2.15),(6,2.15)),((7.2,1.7),(8.2,1.1))]: ar(a,b)
    ax.set_title("Selected source-only transportability design",fontsize=14,weight="bold")
    fig.tight_layout(); fig.savefig(path,dpi=160,bbox_inches="tight"); plt.close(fig)

def figure_auprc(path):
    names=["Confidence","RF disagreement","Feature distance","Conformal†","Isolation Forest"]
    a=[.192,.238,.109,.096,.077]; b=[.033,.035,.043,.079,.036]
    y=np.arange(len(names))
    fig,ax=plt.subplots(figsize=(8,4.8))
    for yy,x1,x2 in zip(y,a,b): ax.plot([x1,x2],[yy,yy],color="0.6",lw=1)
    ax.scatter(a,y,label="UNSW→CIC",s=45); ax.scatter(b,y,label="CIC→UNSW",s=45,facecolors="white")
    ax.set_yticks(y); ax.set_yticklabels(names,fontsize=8.5); ax.set_xlabel("Attack-miss AUPRC")
    ax.grid(axis="x",ls=":",alpha=.4); ax.legend(frameon=False,ncol=2)
    ax.set_title("Bidirectional attack-miss AUPRC",weight="bold")
    fig.tight_layout(); fig.savefig(path,dpi=160,bbox_inches="tight"); plt.close(fig)

def figure_budget(path):
    budgets=np.array([1,5,10]); data={
        "Confidence":([.90,8.19,19.60],[.03,.77,1.40]),
        "RF disagreement":([2.46,12.33,24.68],[.03,.88,1.46]),
        "Feature distance":([.07,.58,.64],[.56,4.34,5.09]),
        "Conformal†":([.0001,17.37,20.40],[4.91,14.73,22.53]),
        "Isolation Forest":([.14,.75,1.76],[.05,.45,.82])}
    fig,axs=plt.subplots(1,2,figsize=(10.5,4.2),sharey=True)
    for k,(name,(x1,x2)) in enumerate(data.items()):
        axs[0].plot(budgets,x1,marker="o",label=name); axs[1].plot(budgets,x2,marker="o",label=name)
    for ax,title in zip(axs,["UNSW→CIC","CIC→UNSW"]):
        ax.axhline(5,color="0.55",ls=":"); ax.set_xticks([1,5,10]); ax.set_xticklabels(["1%","5%","10%"])
        ax.set_xlabel("Review budget"); ax.set_title(title,weight="bold"); ax.grid(ls=":",alpha=.4)
    axs[0].set_ylabel("Attack-miss capture (%)"); axs[0].legend(frameon=False,fontsize=7,ncol=2)
    fig.suptitle("Operational attack-miss capture under fixed review budgets",weight="bold")
    fig.tight_layout(); fig.savefig(path,dpi=160,bbox_inches="tight"); plt.close(fig)

def figure_generic(path):
    names=["Confidence","RF disagreement","Feature distance","Conformal†","Isolation Forest"]
    g=[.738,.736,.859,.518,.847]; a=[.192,.238,.109,.096,.077]
    fig,ax=plt.subplots(figsize=(7.2,5))
    ax.scatter(g,a,s=55)
    for x,y,n in zip(g,a,names): ax.text(x+.008,y+.005,n,fontsize=7.5)
    ax.set_xlabel("Generic-error AUPRC"); ax.set_ylabel("Attack-miss AUPRC")
    ax.grid(ls=":",alpha=.4); ax.set_title("Generic error versus security-critical attack misses",weight="bold")
    fig.tight_layout(); fig.savefig(path,dpi=160,bbox_inches="tight"); plt.close(fig)

figs=[
    FIGDIR/"graphical_abstract.png",FIGDIR/"literature_timeline.png",FIGDIR/"design_flow.png",
    FIGDIR/"attack_miss_auprc.png",FIGDIR/"budget_capture.png",FIGDIR/"generic_vs_attackmiss.png"]
figure_graphical(figs[0]); figure_timeline(figs[1]); figure_design(figs[2]); figure_auprc(figs[3]); figure_budget(figs[4]); figure_generic(figs[5])

# Parse source blocks.
lines = SOURCE.read_text(encoding="utf-8").splitlines()
doc=Document(); style_document(doc)
roman_section=doc.sections[0]; add_page_num(roman_section,"lowerRoman")
fig_index=-1
first_chapter=False
skip_leading=True

chapter_starts = {"CHAPTER 1","CHAPTER 2","CHAPTER 3","CHAPTER 4","CHAPTER 5"}
newpage_heads = {"ACKNOWLEDGEMENT","TABLE OF CONTENTS","LIST OF FIGURES","LIST OF TABLES","ABSTRACT","GRAPHICAL ABSTRACT","ABBREVIATIONS","SYMBOLS","REFERENCES","APPENDIX 1: USER MANUAL","APPENDIX 2: ACHIEVEMENTS"}

i=0
while i < len(lines):
    line=lines[i]
    if not line.strip():
        i+=1; continue

    if line.startswith("TABLE_JSON:"):
        if i+1 < len(lines):
            rows=json.loads(lines[i+1]); add_table(doc,rows); i+=2; continue

    if line.startswith("FIGURE_REL:"):
        fig_index += 1
        # 0 is the institutional logo, intentionally rendered as text in the GitHub build.
        if fig_index>0 and fig_index<=6:
            p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            r=p.add_run(); r.add_picture(str(figs[fig_index-1]), width=Cm(16.8))
        i+=1; continue

    if line.startswith("# "):
        title=line[2:].strip()
        if title=="Project Report Source":
            i+=1; continue
        if title in chapter_starts:
            if not first_chapter:
                sec=doc.add_section(WD_SECTION.NEW_PAGE); add_page_num(sec,"decimal"); first_chapter=True
            else:
                doc.add_page_break()
        elif title in newpage_heads or title=="REFERENCES":
            doc.add_page_break()
        p=doc.add_paragraph(title,style="Heading 1")
        i+=1; continue

    if line.startswith("## "):
        title=line[3:].strip()
        p=doc.add_paragraph(title,style="Heading 2")
        i+=1; continue

    if line.startswith("### "):
        title=line[4:].strip()
        p=doc.add_paragraph(title,style="Heading 3")
        i+=1; continue

    if line.startswith("CAPTION:"):
        p=doc.add_paragraph(line[len("CAPTION:"):].strip(),style="Caption")
        i+=1; continue

    if line.startswith("TOC:"):
        txt=line[4:].strip()
        p=doc.add_paragraph(txt,style="TOCEntry")
        i+=1; continue

    if line.startswith("FRONT:"):
        txt=line[len("FRONT:"):].strip()
        if txt=="BONAFIDE CERTIFICATE":
            doc.add_page_break()
        elif txt=="Submitted by":
            pass
        p=doc.add_paragraph(txt, style="FrontBody")
        if "TRANSPORTABILITY OF POST-HOC" in txt:
            for r in p.runs: r.font.size=Pt(16); r.font.bold=True
        i+=1; continue

    if line.startswith(">"):
        p=doc.add_paragraph(line.lstrip("> ").strip(),style="Small")
        i+=1; continue

    # Normal body text.
    if line.startswith("- "):
        p=doc.add_paragraph(style="List Bullet"); p.paragraph_format.line_spacing=1.5; p.add_run(line[2:].strip())
    elif re.match(r"^\d+\.\s",line):
        p=doc.add_paragraph(style="List Number"); p.paragraph_format.line_spacing=1.5; p.add_run(re.sub(r"^\d+\.\s","",line))
    else:
        p=doc.add_paragraph(line.strip(),style="Normal")
        p.paragraph_format.first_line_indent=Cm(0.6)
    i+=1

# Remove accidental blank leading paragraph and set document core props.
doc.core_properties.title="Transportability of Post-Hoc Reliability Signals for Network Intrusion Detection under Source-Only Cross-Domain Transfer"
doc.core_properties.subject="Academic project report"
doc.core_properties.author="Shreyas Gautam; Bhawika Panchal; Himanshi Mittal; Anna Taneja; Aditya Mehta"
doc.save(OUT)
print(f"built {OUT} ({OUT.stat().st_size} bytes)")