import asyncio
from modules import planner, inquiry_builder, router, scanner

def run_research(request: str, knowledge_base=None):
    domains = planner.plan_request(request)
    results, log = {}, []
    log.append(f"Task Decomposition -> Domains identified: {', '.join(domains)}")
    knowledge_base = knowledge_base or {}
    qr = router.QueryRouter()
    round_num = 1
    while domains:
        log.append(f"--- Round {round_num}: Executing {len(domains)} queries ---")
        new_tasks = []
        tasks = []
        task_domains = []
        for domain in domains:
            if domain in knowledge_base:
                log.append(f"Using cached answer for [{domain}]")
                results[domain] = knowledge_base[domain]
            else:
                prompt = inquiry_builder.build_inquiry(domain)
                log.append(f'Querying [{domain}] with GPT-4: "{prompt}"')
                tasks.append(qr.ask_async(prompt, domain))
                task_domains.append(domain)
        if tasks:
            async def run_tasks():
                return await asyncio.gather(*tasks)

            responses = asyncio.run(run_tasks())
            for dom, (answer, model_used) in zip(task_domains, responses):
                clean = scanner.scan_content(answer)
                if clean != answer:
                    log.append(f"[{dom}] response sanitized.")
                results[dom] = clean
                knowledge_base[dom] = clean
                log.append(f"Received [{dom}] (model {model_used}) answer ✓")
                if dom.lower() == "regulations":
                    import re
                    follow_re = r'(?:Part\s?\d+|14\s*CFR\s*§\s*\d+|waiver)'
                    match = re.search(follow_re, clean, flags=re.I)
                    if match:
                        follow_up = match.group(0).strip()
                        if follow_up not in results:
                            log.append(f"Follow‑up identified: {follow_up}")
                            new_tasks.append(follow_up)
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

    # --- compile technical spec fields ---
    req_prompt = (
        f"Using the project request '{request}' and all domain findings, "
        "list the key system requirements in bullet form."
    )
    requirements, model_used = qr.ask(req_prompt, "requirements", model_override="gpt-3.5-turbo")
    results["requirements"] = requirements
    log.append("Compiled requirements summary.")

    comp_prompt = (
        "Provide a short component breakdown summarizing major subsystems "
        "and their roles based on the research findings."
    )
    components, model_used = qr.ask(comp_prompt, "analysis", model_override="gpt-3.5-turbo")
    results["component_analysis"] = components
    log.append("Generated component analysis.")

    feas_prompt = (
        "Assess overall feasibility in 2-3 sentences, including any major "
        "risks or challenges mentioned in the research findings."
    )
    feasibility, model_used = qr.ask(feas_prompt, "feasibility", model_override="gpt-3.5-turbo")
    results["feasibility"] = feasibility
    log.append("Evaluated feasibility.")

    # delete any placeholder that crept in
    results.pop("Next Steps Considerations", None)

    return results, log
