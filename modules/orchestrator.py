from modules import planner, inquiry_builder, router, scanner

def run_research(request: str):
    domains = planner.plan_request(request)
    results, log = {}, []
    log.append(f"Task Decomposition -> Domains identified: {', '.join(domains)}")
    qr = router.QueryRouter()
    round_num = 1
    while domains:
        log.append(f"--- Round {round_num}: Executing {len(domains)} queries ---")
        new_tasks = []
        for domain in domains:
            prompt = inquiry_builder.build_inquiry(domain)
            key_id = (qr.key_index % len(qr.api_keys)) + 1
            log.append(f'Querying [{domain}] using API Key-{key_id}: "{prompt}"')
            try:
                answer, model_used = qr.ask(prompt, domain, model_override=None)
            except Exception as e:
                log.append(f"Error querying {domain}: {e}")
                continue
            clean = scanner.scan_content(answer)
            if clean != answer:
                log.append(f"[{domain}] response sanitized.")
            results[domain] = clean
            log.append(f"Received [{domain}] (model {model_used}) answer ✓")
            if domain.lower() == "regulations":
                import re
                follow_re = r'(?:Part\s?\d+|14\s*CFR\s*§\s*\d+|waiver)'
                match = re.search(follow_re, clean, flags=re.I)
                if match:
                    follow_up_domain = match.group(0).strip()
                    if follow_up_domain not in results:
                        log.append(f"Follow‑up identified: {follow_up_domain}")
                        new_tasks.append(follow_up_domain)
        if not new_tasks:
            break
        domains = new_tasks
        round_num += 1
    log.append("--- All queries completed ---")

    # --- summary pass ---
    summary_log = []
    # Iterate over a snapshot to avoid 'dictionary changed size' runtime errors
    summary_items = list(results.items())
    for domain, answer in summary_items:
        summary_prompt = (
            f"Summarize the following text in 3–4 crisp bullet points:\n\n{answer}"
        )
        bullets, model_used = qr.ask(summary_prompt, domain, model_override="gpt-3.5-turbo")
        results[f"{domain}\u2011Summary"] = bullets
        summary_log.append(f"Summarized [{domain}] into bullets.")
    log.extend(summary_log)

    # --- generate next steps ---
    next_steps_prompt = (
        "Based on all domain findings, list 3 concrete next steps "
        "to move this R&D project forward."
    )
    next_steps, model_used = qr.ask(next_steps_prompt, "roadmap", model_override="gpt-3.5-turbo")
    results["Next Steps"] = next_steps
    log.append("Generated recommended next steps.")

    # delete any placeholder that crept in
    results.pop("Next Steps Considerations", None)

    return results, log
