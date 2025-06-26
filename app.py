import streamlit as st
from modules import planner, inquiry_builder, router, scanner, orchestrator, synthesizer, composer

st.title("🔒 Secure R&D Assistant – Test Pilot")
st.write("Enter a high‑level R&D project description and let the assistant research it securely.")

# Initialize per-session knowledge base for domain answers
kb = st.session_state.setdefault("knowledge_base", {})  # {domain: answer}

user_request = st.text_area("Project Description:", placeholder="e.g. Design a drone for wildfire detection", height=100)
run_clicked = st.button("Run Secure Research")

if run_clicked and user_request:
    import re
    safe_request = re.sub(r'<[^>]*>', '', user_request).strip()
    if not safe_request:
        st.error("Please enter a valid project description.")
    else:
        st.info("Starting secure research… this may take a minute.")
        results, log = orchestrator.run_research(safe_request, kb)
        st.session_state["knowledge_base"] = kb
        st.subheader("Activity Log")
        st.code("\n".join(log))
        report_md = synthesizer.synthesize(
            project_name=safe_request,
            user_prompt=safe_request,
            data=results,
            artifacts={}
        )
        pdf_bytes = composer.make_pdf(report_md)
        st.success("Research complete! Download the full report below:")
        st.download_button(label="📄 Download Report PDF", data=pdf_bytes, file_name="research_report.pdf", mime="application/pdf")
