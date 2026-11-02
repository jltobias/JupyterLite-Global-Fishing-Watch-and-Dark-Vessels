"""Render reproducible standalone book visuals and accessible SVG infographics."""
from pathlib import Path
import html
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from plotly.offline import get_plotlyjs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "content"))
import oceanlab as lab
STATIC = ROOT / "content/_static"


def diagram(name, title, description, boxes, links, width=1100, height=540):
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(description)}</desc>',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#839eaa"/></marker></defs>',
        f'<rect width="{width}" height="{height}" rx="18" fill="#081f32"/>',
        f'<text x="38" y="50" fill="white" font-size="27" font-family="Arial,sans-serif" font-weight="700">{html.escape(title)}</text>']
    for start,end,label in links:
        a,b=boxes[start],boxes[end]
        x1,y1=a[0]+a[2]/2,a[1]+a[3]/2
        x2,y2=b[0]+b[2]/2,b[1]+b[3]/2
        dx,dy=x2-x1,y2-y1
        ratio=max(abs(dx)/(a[2]/2),abs(dy)/(a[3]/2))
        if ratio:x1+=dx/ratio;y1+=dy/ratio
        ratio2=max(abs(dx)/(b[2]/2),abs(dy)/(b[3]/2))
        if ratio2:x2-=dx/ratio2;y2-=dy/ratio2
        parts.append(f'<path d="M{x1} {y1}L{x2} {y2}" stroke="#839eaa" stroke-width="2.2" fill="none" marker-end="url(#arrow)"/>')
        if label:parts.append(f'<text x="{(x1+x2)/2}" y="{(y1+y2)/2-8}" text-anchor="middle" fill="#c8d9e0" font-size="13" font-family="Arial,sans-serif">{html.escape(label)}</text>')
    for x,y,w,h,heading,lines,color in boxes:
        parts.extend([f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#15364a" stroke="{color}" stroke-width="2"/>',
            f'<text x="{x+16}" y="{y+30}" fill="{color}" font-size="19" font-family="Arial,sans-serif" font-weight="700">{html.escape(heading)}</text>'])
        for i,line in enumerate(lines):parts.append(f'<text x="{x+16}" y="{y+56+i*20}" fill="#e1ebee" font-size="15" font-family="Arial,sans-serif">{html.escape(line)}</text>')
    parts.append(f'<text x="38" y="{height-20}" fill="#a6bfcb" font-size="13" font-family="Arial,sans-serif">Conceptual teaching diagram · arrows describe reasoning or possible pathways, not measured causal effects.</text></svg>')
    (STATIC/name).write_text("\n".join(parts),encoding="utf-8")


def main():
    STATIC.mkdir(parents=True,exist_ok=True)
    lab.map2d().savefig(STATIC/"observed-ocean.png",facecolor=lab.NAVY)
    plt.close("all")
    lab.radar_plot().savefig(STATIC/"synthetic-radar.png")
    plt.close("all")
    (STATIC/"plotly.min.js").write_text(get_plotlyjs(),encoding="utf-8")
    for name,fig in [("observed-map",lab.interactive_map()),("observed-globe",lab.globe()),
                     ("ocean-scene",lab.ocean_scene()),("radar-surface",lab.radar_surface()),("stock-scenarios",lab.stock_slider())]:
        fig.write_html(STATIC/(name+".html"),include_plotlyjs="plotly.min.js",full_html=True,
                       config={"responsive":True,"displaylogo":False})
    teal,amber=lab.TEAL,lab.AMBER
    diagram("observation-ladder.svg","From observation to decision",
        "AIS broadcasts and satellite pixels support object detections, classification, interpretation and decisions. Each step introduces assumptions.",[
        (40,110,300,110,"1 / Measurement",["AIS messages or SAR pixels","Instrument, time, footprint"],teal),
        (400,110,300,110,"2 / Detection",["A candidate object or track","Quality flags and uncertainty"],teal),
        (760,110,300,110,"3 / Classification",["Vessel? Fishing? Matched?","Model output, not ground truth"],teal),
        (220,330,300,110,"4 / Interpretation",["Pressure, visibility, hypothesis","Alternative explanations"],amber),
        (620,330,300,110,"5 / Decision",["Bounded action + new evidence","Community and scientific review"],amber)
        ],[(0,1,""),(1,2,""),(2,3,""),(3,4,"")])
    diagram("dark-vessel-tree.svg","Unmatched is a question, not a verdict",
        "Check a radar candidate for artifacts, then check AIS coverage, timing and identity uncertainty before seeking corroborating evidence.",[
        (40,100,300,110,"Radar candidate",["Vessel, clutter or structure?","Review the image and masks"],teal),
        (400,100,300,110,"Coverage check",["Was AIS reasonably receivable?","Check time and data availability"],teal),
        (760,100,300,110,"Matching check",["Motion, timing, location error","One-to-one identity assignment"],teal),
        (220,330,300,115,"Still unmatched?",["Equipment, carriage, reception,","or deliberate concealment?"],amber),
        (620,330,300,115,"Corroborate",["Registries, authorizations, logs","No automatic illegality claim"],amber)
        ],[(0,1,""),(1,2,""),(2,3,""),(3,4,"")])
    diagram("one-health-pathways.svg","One ocean · connected health",
        "Marine ecosystems support aquatic food and livelihoods; environmental change can affect ecosystems and exposure. Distribution, governance and measurement connect these to population health.",[
        (40,105,290,115,"Marine ecosystems",["Stocks, habitats, biodiversity","Growth, bycatch, resilience"],teal),
        (405,105,290,115,"Aquatic food systems",["Landings, trade, loss, prices","Access and working conditions"],teal),
        (770,105,290,115,"People and communities",["Nutrition, income, well-being","Intake is not availability"],teal),
        (40,325,290,115,"Environmental pressures",["Warming, pollution, runoff","Hazards need direct evidence"],amber),
        (405,325,290,115,"Exposure pathways",["Seafood, water contact, work","Dose, timing, susceptibility"],amber),
        (770,325,290,115,"Shared response",["Co-management + monitoring","Health and ecological outcomes"],amber)
        ],[(0,1,""),(1,2,""),(3,0,""),(3,4,""),(4,2,""),(2,5,"")])
    print("Rendered five interactive figures, two image panels and three infographics")


if __name__=="__main__":main()
