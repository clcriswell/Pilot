
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
                answer = qr.ask(prompt, domain)
            except Exception as e:
                log.append(f"Error querying {domain}: {e}")
                continue
            clean = scanner.scan_content(answer)
            if clean != answer:
                log.append(f"[{domain}] response sanitized.")
            results[domain] = clean
            log.append(f"Received [{domain}] answer ✓")
            if domain.lower() == "regulations":
                import re
                m = re.search(r'Part\s?(\d+)', clean)
                if m:
                    part = m.group(1)
                    follow_up = f"FAA Part {part}"
                    if follow_up not in results:
                        log.append(f"Follow‑up identified: {follow_up}")
                        new_tasks.append(follow_up)
        if not new_tasks:
            break
        domains = new_tasks
        round_num += 1
    log.append("--- All queries completed ---")
    return results, log
