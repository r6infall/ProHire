def compute_score(cand, jd, weights):
    skills = set(cand["skills"])
    req = set(jd["required_skills"])
    nice = set(jd["nice_to_have_skills"])

    # skill score
    hard = len(skills & req)
    soft = len(skills & nice) * 0.5
    total = max(len(req) + len(nice), 1)
    s_skill = (hard + soft) / total

    # experience
    exp = cand["experience_years"]
    if exp < jd["min_experience_years"]:
        s_exp = exp / (jd["min_experience_years"] + 1)
    elif exp > jd["max_experience_years"]:
        s_exp = 0.7
    else:
        s_exp = 1

    # projects
    s_proj = min(len(cand["projects"]), 5) / 5

    # cgpa
    s_cgpa = (cand["cgpa"] or 5) / 10

    # college
    tier_map = {"Tier 1": 1, "Tier 2": 0.75, "Tier 3": 0.5, None: 0.5}
    s_col = tier_map[cand["college_tier"]]

    score = (
        weights["skills"] * s_skill +
        weights["experience"] * s_exp +
        weights["projects"] * s_proj +
        weights["cgpa"] * s_cgpa +
        weights["college"] * s_col
    ) * 100

    return round(score, 2)
