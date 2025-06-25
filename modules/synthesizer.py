def synthesize_report(original_request: str, results: dict) -> str:
    title = f"{original_request} – Preliminary Research Report"
    intro = (f"The following report consolidates findings for the project \"{original_request}\". "
             "It addresses the key domains identified and researched in detail.")
    lines = [title, "=" * len(title), "", intro, ""]
    for domain, content in results.items():
        if domain.lower().startswith("faa part"):
            header = f"Details on {domain}"
        else:
            header = f"{domain} Considerations"
        lines.extend([header, "-" * len(header), content, ""])
    # Inject bullet summaries
    for domain in list(results):
        if domain.endswith("\u2011Summary"):
            header = f"{domain.replace('\u2011Summary','')} –\u00A0Key Take\u2011aways"
            lines.extend([header, "-" * len(header), results[domain], ""])

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
