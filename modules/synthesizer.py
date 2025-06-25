def sanitize(text: str) -> str:
    """Replace MS-Word weird dash or ? artefacts with plain characters."""
    return (text.replace(" ? ", " — ")
                .replace("?Summary", " — Summary")
                .replace("? Key Take?aways", " — Summary")
                .replace("?Summary Considerations", " — Summary"))


def synthesize_report(original_request: str, results: dict) -> str:
    title = f"{original_request} —\u202fPreliminary\u202fResearch\u202fReport"
    intro = (f"The following report consolidates findings for the project \"{original_request}\". "
             "It addresses the key domains identified and researched in detail.")
    lines = [title, "=" * len(title), "", intro, ""]

    # -------------------  dedup logic  -------------------
    # Use bullet summaries if present; skip original long answer to avoid duplicates
    clean_results = {}
    for key, val in results.items():
        if key.endswith("\u2011Summary"):
            base = key.replace("\u2011Summary", "")
            clean_results[f"{base} — Summary"] = sanitize(val)
        elif key in ("Next Steps Considerations",):
            # skip placeholder; we'll keep the proper "Recommended Next Steps"
            continue
        elif f"{key}\u2011Summary" in results:
            # long answer has a summary \u2192 drop long answer
            continue
        else:
            clean_results[key] = sanitize(val)
    results = clean_results
    # -----------------------------------------------------
    for domain, content in results.items():
        if domain.lower().startswith("faa part"):
            header = f"Details on {domain}"
        elif domain.endswith(" — Summary"):
            header = domain
        else:
            header = f"{domain} Considerations"
        lines.extend([header, "-" * len(header), content, ""])

    # Next-steps section
    if "Next Steps" in results:
        lines.extend(["Recommended Next Steps", "-----------------------", results["Next Steps"], ""])

    lines.extend([
        "Conclusion",
        "----------",
        "These domain insights provide a comprehensive overview for the project. ",
        "Next steps may include prototyping and field validation.",
    ])
    return "\n".join(lines)
