from collections import Counter
from sqlalchemy import select, func
from models import Survey, SurveyAdditionalMedium

def _distribution(values, options=None):
    counts = Counter(values)
    labels = list(options or sorted(counts.keys()))
    total = len(values)
    return [
        {"label": label, "count": counts.get(label, 0),
         "relative_frequency": round(counts.get(label, 0) / total, 4) if total else 0,
         "percentage": round(counts.get(label, 0) / total * 100, 2) if total else 0}
        for label in labels
    ]

def build_statistics(session):
    surveys = session.scalars(select(Survey)).all()
    total = len(surveys)
    main_values = [s.main_medium for s in surveys if s.main_medium]
    influence_values = [s.influence_medium for s in surveys if s.influence_medium]
    content_values = [s.content_preference for s in surveys if s.content_preference]
    additional_values = session.scalars(select(SurveyAdditionalMedium.medium)).all()
    main_dist = _distribution(main_values, Survey.MEDIUM_OPTIONS)
    influence_dist = _distribution(influence_values, Survey.MEDIUM_OPTIONS)
    content_dist = _distribution(content_values, Survey.CONTENT_OPTIONS)
    additional_dist = _distribution(additional_values, Survey.MEDIUM_OPTIONS)
    top_main = max(main_dist, key=lambda x: x["count"], default=None)
    top_influence = max(influence_dist, key=lambda x: x["count"], default=None)
    top_content = max(content_dist, key=lambda x: x["count"], default=None)
    return {
        "total_surveys": total,
        "last_survey": max((s.created_at for s in surveys), default=None).strftime("%Y-%m-%d %H:%M") if surveys else None,
        "top_main_medium": top_main if top_main and top_main["count"] else None,
        "top_influence_medium": top_influence if top_influence and top_influence["count"] else None,
        "top_content": top_content if top_content and top_content["count"] else None,
        "main_distribution": main_dist,
        "influence_distribution": influence_dist,
        "content_distribution": content_dist,
        "additional_distribution": additional_dist,
        "valid_counts": {
            "main_medium": len(main_values), "influence_medium": len(influence_values),
            "content_preference": len(content_values), "additional_selections": len(additional_values)
        }
    }
