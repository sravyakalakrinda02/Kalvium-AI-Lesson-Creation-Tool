import io, json, zipfile
from datetime import datetime

def lesson_to_markdown(lesson, research):
    lines=[f"# {lesson.get('title','Lesson')}","",f"**Learning objective:** {lesson.get('objective','')}","",f"**Duration:** {lesson.get('total_minutes',45)} minutes","",lesson.get('overview',''),""]
    for i,s in enumerate(lesson.get('sections',[]),1):
        lines += [f"## {i}. {s.get('heading','Section')} ({s.get('minutes',0)} min)","",s.get('content',''),""]
        if s.get('activity'): lines += [f"**Activity / application:** {s['activity']}",""]
    lines += ["## Knowledge check","",lesson.get('knowledge_check',''),"","## Key takeaways",""]
    for t in lesson.get('takeaways',[]): lines.append(f"- {t}")
    lines += ["","## References",""]
    refs=lesson.get('references',[])
    if not refs:
        for cat in ('web','books','youtube'):
            refs += [{"title":x.get('title'),"url":x.get('url'),"type":cat} for x in research.get(cat,[])]
    for r in refs: lines.append(f"- [{r.get('title','Source')}]({r.get('url','#')}) — {r.get('type','reference')}")
    if lesson.get('assumptions_or_gaps'):
        lines += ["","## Assumptions and research gaps",""]+[f"- {x}" for x in lesson['assumptions_or_gaps']]
    return "\n".join(lines)

def make_export_zip(lesson,research,qc1,qc2):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('final_lesson.md',lesson_to_markdown(lesson,research))
        z.writestr('lesson.json',json.dumps(lesson,ensure_ascii=False,indent=2))
        z.writestr('research_references.json',json.dumps(research,ensure_ascii=False,indent=2))
        z.writestr('qc_layer_1_research_accuracy.json',json.dumps(qc1 or {},ensure_ascii=False,indent=2))
        z.writestr('qc_layer_2_instructional_quality.json',json.dumps(qc2 or {},ensure_ascii=False,indent=2))
        z.writestr('README.txt','LessonCraft AI export\nContains the edited lesson, research leads and separate QC audit reports. AI-generated QC is decision support; verify factual claims against primary sources.\n')
    return buf.getvalue()
