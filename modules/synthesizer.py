
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
    lines.extend(["Conclusion", "----------",
                  "These domain insights provide a comprehensive overview for the project. "
                  "Next steps may include prototyping and field validation."])
    return "\n".join(lines)
