"""
Mock AI Provider adapter for backend.

Produces intelligent, well-formatted answers by analyzing retrieved context
chunks and matching against a knowledge base of pre-built responses.
Falls back to extracting relevant sentences from the chunk text.
"""

from typing import Any, Dict, List
from adapters.ai.ai_provider import BaseAIProvider
import re


# ═══════════════════════════════════════════════════════════════════
# Pre-built Answer Templates (keyed by query keyword patterns)
# These simulate what a real LLM would generate from the chunks.
# ═══════════════════════════════════════════════════════════════════

ANSWER_TEMPLATES = [
    {
        "keywords": ["calibrat", "fanuc", "r-2000", "welding", "robot"],
        "min_match": 2,
        "answer": (
            "**Welding Robot Calibration Procedure (SOP QA-WR-2024-003)**\n\n"
            "The calibration procedure for the Fanuc R-2000iC welding robots on "
            "Body Shop Line 4 (stations WS-401 through WS-412) is as follows:\n\n"
            "**Calibration Steps:**\n"
            "1. Power down the controller via the main disconnect switch.\n"
            "2. Attach the Renishaw Ballbar QC20-W to the robot flange.\n"
            "3. Run the automated calibration cycle (Program CAL_LINE4_V3).\n"
            "4. Record deviation values in the MES system under ticket WR-CAL.\n"
            "5. If deviation exceeds ±0.15mm, escalate to Maintenance Lead.\n\n"
            "**Acceptance Criteria:**\n"
            "• All six axes must read within ±0.10mm of nominal.\n"
            "• TCP (Tool Center Point) drift must not exceed 0.05mm over 8 hours.\n\n"
            "📋 Calibration certificates are stored in the QMS portal under Documents > Welding."
        )
    },
    {
        "keywords": ["safety", "precaution", "loto", "robot", "cell", "ppe", "welding"],
        "min_match": 2,
        "answer": (
            "**Safety Precautions for Welding Robot Cells**\n\n"
            "Per SOP QA-WR-2024-003, the following safety precautions are **mandatory** "
            "before entering any welding robot cell on Line 4:\n\n"
            "• **LOTO:** Engage Lock Out / Tag Out before entering the robot cell.\n"
            "• **PPE Required:** Heat-resistant gloves, face shield, and steel-toe boots.\n"
            "• **E-Stop Test:** Verify teach pendant Emergency Stop functionality before power-on.\n\n"
            "⚠️ Never enter the cell alone — a spotter must be present at the cell gate."
        )
    },
    {
        "keywords": ["tcp", "drift", "limit", "acceptable", "tolerance"],
        "min_match": 2,
        "answer": (
            "**TCP Drift Tolerance**\n\n"
            "According to SOP QA-WR-2024-003, Section 5 (Acceptance Criteria):\n\n"
            "• TCP (Tool Center Point) drift must **not exceed 0.05mm over 8 hours** of continuous operation.\n"
            "• All six axes must read within **±0.10mm of nominal** after calibration.\n"
            "• If deviation exceeds ±0.15mm during calibration, an immediate escalation to the Maintenance Lead is required."
        )
    },
    {
        "keywords": ["compression", "ratio", "k15c", "engine"],
        "min_match": 2,
        "answer": (
            "**K15C Smart Hybrid Engine — Compression Ratio**\n\n"
            "The K15C 1.5L Dual VVT Smart Hybrid engine has a **compression ratio of 12.5:1**.\n\n"
            "**Key Specifications:**\n"
            "• Displacement: 1462 cc\n"
            "• Bore × Stroke: 74.0 mm × 85.0 mm\n"
            "• Power Output: 103 PS at 6000 rpm\n"
            "• Torque: 138 Nm at 4400 rpm\n"
            "• Fuel System: Multi-point Fuel Injection (MPFI)\n"
            "• Emission Standard: BS-VI Phase 2"
        )
    },
    {
        "keywords": ["proprietary", "coating", "cylinder", "bore", "ptwa"],
        "min_match": 2,
        "answer": (
            "**K15C Cylinder Bore Coating Process**\n\n"
            "The K15C engine uses **Plasma-Transferred Wire-Arc (PTWA) coating** — "
            "this is a proprietary Suzuki process.\n\n"
            "**Details:**\n"
            "• Coating type: Plasma-Transferred Wire-Arc (PTWA)\n"
            "• Thickness tolerance: 150 ± 5 microns\n"
            "• Distribution: Restricted — Engineering department only\n\n"
            "⚠️ This information is classified as RESTRICTED — TRADE SECRET."
        )
    },
    {
        "keywords": ["smart", "hybrid", "isg", "torque", "assist", "regenerative"],
        "min_match": 2,
        "answer": (
            "**K15C Smart Hybrid Features**\n\n"
            "The K15C is equipped with an Integrated Starter Generator (ISG) enabling:\n\n"
            "• **Torque Assist:** Electric motor supplements the petrol engine during acceleration.\n"
            "• **Regenerative Braking:** Kinetic energy captured during deceleration.\n"
            "• **Idle Start-Stop:** Engine automatically shuts off at idle and restarts seamlessly."
        )
    },
    {
        "keywords": ["ppe", "mandatory", "shop", "floor", "production", "hard hat", "boot"],
        "min_match": 2,
        "answer": (
            "**Mandatory PPE on the Production Shop Floor**\n\n"
            "All employees must wear the following PPE:\n\n"
            "• **All production zones:** Hard hat (mandatory)\n"
            "• **Near grinding/welding:** Safety goggles (mandatory)\n"
            "• **Everywhere:** Steel-toe boots (mandatory)\n"
            "• **Logistics zones:** High-visibility vest (mandatory)\n\n"
            "All new employees must complete Plant Floor Safety Training before their first shift."
        )
    },
    {
        "keywords": ["chemical", "spill", "emergency", "fire", "injury", "report"],
        "min_match": 2,
        "answer": (
            "**Emergency Response Procedures**\n\n"
            "• **Fire Alarm:** Evacuate via the nearest green exit sign. Do not use elevators.\n"
            "• **Chemical Spill:** Call the EHS hotline at 1800-XXX-XXXX immediately.\n"
            "• **Injury:** Report to the nearest first-aid station within 15 minutes.\n\n"
            "All incidents must be documented in the incident reporting system."
        )
    },
    {
        "keywords": ["5s", "housekeeping", "sort", "standardize", "sustain"],
        "min_match": 1,
        "answer": (
            "**5S Housekeeping Principles**\n\n"
            "Maruti Suzuki follows the 5S methodology:\n\n"
            "1. **Sort (Seiri):** Remove unnecessary items from the workspace.\n"
            "2. **Set in Order (Seiton):** Organize remaining items for easy access.\n"
            "3. **Shine (Seiso):** Clean workspace and equipment regularly.\n"
            "4. **Standardize (Seiketsu):** Create consistent processes.\n"
            "5. **Sustain (Shitsuke):** Maintain discipline and audit regularly.\n\n"
            "**Key Rule:** Keep walkways clear. No tools left on the floor."
        )
    },
    {
        "keywords": ["sona", "blw", "defect", "rate", "gear"],
        "min_match": 2,
        "answer": (
            "**Sona BLW — Supplier Quality Metrics**\n\n"
            "From the latest Supplier Audit Report (July 2024):\n\n"
            "• **Part Number:** SB-GEAR-9901\n"
            "• **Defect Rate:** 0.03%\n"
            "• **Audit Date:** 2024-07-01\n"
            "• **Rating:** ✅ Excellent — well below the 0.5% threshold\n\n"
            "Sona BLW has the **lowest defect rate** among all audited suppliers."
        )
    },
    {
        "keywords": ["supplier", "defect", "rate", "audit", "all", "ranking"],
        "min_match": 2,
        "answer": (
            "**Supplier Quality Audit Results (2024)**\n\n"
            "| Supplier | Part # | Defect Rate | Audit Date |\n"
            "|----------|--------|-------------|------------|\n"
            "| Sona BLW | SB-GEAR-9901 | 0.03% | 2024-07-01 |\n"
            "| Subros Ltd | SUB-AC-8810 | 0.08% | 2024-07-10 |\n"
            "| Bharat Forge | BF-CRK-7721 | 0.12% | 2024-06-15 |\n"
            "| Minda Industries | MI-HDL-3305 | 0.45% | 2024-06-18 |\n"
            "| Rico Auto | RA-DIE-4402 | 0.67% | 2024-07-12 |\n"
            "| Lumax Auto | LA-LAMP-5520 | **1.20%** | 2024-07-05 |\n\n"
            "⚠️ Lumax Auto exceeds the 1.0% defect threshold. Corrective action recommended.\n\n"
            "📊 Distribution restricted to Production and QA leads only."
        )
    },
    {
        "keywords": ["highest", "defect", "supplier", "worst"],
        "min_match": 2,
        "answer": (
            "**Highest Defect Rate Supplier**\n\n"
            "**Lumax Auto** has the highest defect rate at **1.20%** (Part: LA-LAMP-5520, Audit: 2024-07-05).\n\n"
            "This exceeds the 1.0% defect threshold. Corrective action is recommended.\n\n"
            "Full ranking (worst to best):\n"
            "1. 🔴 Lumax Auto: 1.20%\n"
            "2. 🟡 Rico Auto: 0.67%\n"
            "3. 🟡 Minda Industries: 0.45%\n"
            "4. 🟢 Bharat Forge: 0.12%\n"
            "5. 🟢 Subros Ltd: 0.08%\n"
            "6. 🟢 Sona BLW: 0.03%"
        )
    },
    {
        "keywords": ["rajesh", "kumar", "salary", "employee", "hr"],
        "min_match": 1,
        "answer": (
            "⚠️ **Access Denied — PII Quarantine Active**\n\n"
            "The HR Employee Roster document has been **quarantined** by the automated PII scanner. "
            "The following personally identifiable information was detected:\n\n"
            "• Aadhaar Numbers\n"
            "• PAN Card Numbers\n"
            "• Personal Phone Numbers\n"
            "• Salary/CTC Information\n\n"
            "This document cannot be accessed until a platform administrator reviews and approves it "
            "through the PII remediation workflow."
        )
    },
    {
        "keywords": ["recipe", "butter", "chicken", "cook"],
        "min_match": 1,
        "answer": (
            "I do not have enough verified information relevant to your project context to answer this question.\n\n"
            "The knowledge base contains a document about recipes, but it has been flagged as "
            "**irrelevant content** — it has no relation to automotive manufacturing or Maruti Suzuki operations.\n\n"
            "The assistant only answers queries within the scope of the ingested knowledge base."
        )
    },
    {
        "keywords": ["calibration", "certificate", "stored", "qms", "record"],
        "min_match": 2,
        "answer": (
            "**Calibration Certificate Storage**\n\n"
            "According to SOP QA-WR-2024-003, Section 6 (Records):\n\n"
            "• **Location:** QMS (Quality Management System) Portal\n"
            "• **Path:** QMS Portal → Documents → Welding\n"
            "• **Access:** QA department personnel with internal clearance\n"
            "• **Format:** Digital certificates linked to MES ticket WR-CAL"
        )
    },
]


class MockAIProvider(BaseAIProvider):
    """
    Intelligent mock AI provider that produces well-formatted answers
    from retrieved context chunks by matching against pre-built templates.
    Falls back to extracting key sentences from chunk text.
    """

    def _match_template(self, query: str) -> str | None:
        """Try to match query to a pre-built answer template."""
        query_lower = query.lower()
        
        best_match = None
        best_score = 0
        
        for template in ANSWER_TEMPLATES:
            matches = sum(1 for kw in template["keywords"] if kw in query_lower)
            min_req = template.get("min_match", 2)
            if matches >= min_req and matches > best_score:
                best_score = matches
                best_match = template["answer"]
        
        return best_match

    def _extract_smart_answer(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """Extract relevant sentences from chunks to build an answer."""
        query_words = set(w.lower().strip("?,.!:;()") for w in query.split() if len(w) > 2)
        
        relevant_sentences = []
        for chunk in chunks[:3]:  # Top 3 chunks
            text = chunk.get("text", "")
            sentences = re.split(r'[.\n]', text)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 10:
                    continue
                sentence_lower = sentence.lower()
                matches = sum(1 for w in query_words if w in sentence_lower)
                if matches >= 2:
                    relevant_sentences.append(sentence)
        
        if relevant_sentences:
            # De-duplicate
            seen = set()
            unique = []
            for s in relevant_sentences:
                key = s[:50].lower()
                if key not in seen:
                    seen.add(key)
                    unique.append(s)
            
            source_file = chunks[0].get("metadata", {}).get("filename", "Unknown Document")
            answer = f"Based on **{source_file}**:\n\n"
            for s in unique[:8]:
                answer += f"• {s}\n"
            return answer
        
        return None

    async def generate_response(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        system_instruction: str | None = None
    ) -> str:
        # 1. Try template match first (even if context_chunks is empty)
        template_answer = self._match_template(query)
        if template_answer:
            return template_answer

        if not context_chunks:
            return (
                "I have no relevant context in the knowledge base to answer this question. "
                "Please make sure the relevant documents are ingested with correct permissions."
            )

        # 2. Try smart extraction from chunks
        smart_answer = self._extract_smart_answer(query, context_chunks)
        if smart_answer:
            return smart_answer

        # 3. Fallback: summarize top chunks
        parts = []
        for chunk in context_chunks[:3]:
            text_snippet = chunk.get("text", "")[:400]
            parts.append(f"• {text_snippet}")

        source = context_chunks[0].get("metadata", {}).get("filename", "Retrieved Document")
        header = f"Based on **{source}** ({len(context_chunks)} relevant sections found):\n\n"
        return header + "\n\n".join(parts)
