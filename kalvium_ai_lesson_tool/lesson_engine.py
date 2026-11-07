"""AI lesson generation and two independent quality-control audits."""
import json

def _chat_json(client, model, system, user):
    """Call Gemini and parse its structured JSON response."""
    prompt = f"{system}\n\nUSER TASK:\n{user}"
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
    )
    raw = (response.text or "").strip()
    if not raw:
        raise ValueError("Gemini returned an empty response. Please retry.")
    # Defensive cleanup in case a model returns fenced JSON despite JSON mode.
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[:-3].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini returned invalid JSON: {exc}") from exc

def _research_text(research):
    lines=[]
    for category in ("web","books","youtube"):
        lines.append(category.upper()+":")
        for x in research.get(category,[]):
            lines.append(f"- {x.get('title')} | {x.get('url')} | {x.get('snippet')} | source: {x.get('source')}")
    return "\n".join(lines)

def generate_lesson(client, model, title, objective, research):
    system="""You are an instructional designer and research assistant. Create accurate, original lesson material. Use the supplied research leads; do not pretend to have opened or verified a source if only its search/catalogue link is supplied. If evidence is insufficient, explicitly mark claims that need instructor verification. Return valid JSON only with keys: title, objective, overview, total_minutes, sections (array of {heading, minutes, content, activity}), knowledge_check, takeaways (array), references (array of {title,url,type,how_used}), assumptions_or_gaps (array). Plan a complete 45-minute lesson: section minutes must total 45, including activities and knowledge check. Include explanations, concrete examples, practical applications, and answers/rationale in knowledge_check."""
    user=f"LESSON TITLE: {title}\nLEARNING OBJECTIVE: {objective}\nRESEARCH LEADS:\n{_research_text(research)}\nCreate a lesson designed for 45 minutes. Cite only supplied URLs in references. Include books, websites and YouTube search resources when relevant, but label catalogue/search pages honestly."
    result=_chat_json(client,model,system,user)
    result.setdefault("title",title); result.setdefault("objective",objective); result.setdefault("sections",[])
    result.setdefault("total_minutes",sum(int(s.get("minutes",0)) for s in result["sections"]))
    result.setdefault("references",[]); result.setdefault("takeaways",[]); result.setdefault("assumptions_or_gaps",[])
    return result

def run_research_qc(client, model, lesson, research):
    system="""You are an independent factual-accuracy auditor. Audit the lesson against the supplied research leads only. Do not claim to have independently opened URLs. Flag unsupported claims, likely inaccuracies, missing citations, weak source quality, inconsistencies and research gaps. Distinguish verified from unverified. Return JSON with: overall_assessment, source_reliability, issues (array of {severity,claim,problem,suggestion}), unsupported_or_unverified_claims (array), coverage_gaps (array), reviewer_checks (array). If evidence is insufficient, say so rather than guessing."""
    return _chat_json(client,model,system,"LESSON:\n"+json.dumps(lesson,ensure_ascii=False)+"\nRESEARCH LEADS:\n"+_research_text(research))

def run_instructional_qc(client, model, lesson, objective):
    system="""You are a separate instructional-design auditor. Evaluate only pedagogical quality: alignment to the stated learning objective, learner level assumptions, sequencing, clarity, cognitive load, examples, practical application, activities, assessment and feasibility in 45 minutes. Do not perform the factual research audit. Return JSON with: overall_assessment, objective_alignment, issues (array of {criterion,problem,suggestion}), missing_elements (array), timing_assessment, recommended_improvements (array). Be specific and actionable."""
    return _chat_json(client,model,system,"LEARNING OBJECTIVE:\n"+objective+"\nLESSON:\n"+json.dumps(lesson,ensure_ascii=False))


def apply_qc_recommendations(client, model, lesson, qc1, qc2):
    """Create a revised lesson using both reports while preserving its structure."""
    system = """You are an instructional editor. Revise the supplied lesson by applying only appropriate, actionable recommendations from the two QC reports. Preserve the lesson objective, audience assumptions and 45-minute total duration. Do not invent citations or claim facts are verified when the research report says they are unsupported. If a factual issue cannot be resolved from supplied material, qualify it or mark it for instructor verification. Return the complete revised lesson as valid JSON with the same schema as the original lesson."""
    user = ("ORIGINAL LESSON:\\n" + json.dumps(lesson, ensure_ascii=False) + "\\nQC LAYER 1 REPORT:\\n" + json.dumps(qc1 or {}, ensure_ascii=False) + "\\nQC LAYER 2 REPORT:\\n" + json.dumps(qc2 or {}, ensure_ascii=False))
    return _chat_json(client, model, system, user)
