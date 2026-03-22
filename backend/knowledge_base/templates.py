# knowledge_base/templates.py
"""
Standard contract clause templates.
These are used as reference points for RAG comparison.

In a production system these would be loaded from
a database or S3. For now, hardcoded is fine.

Each template has:
- id: unique identifier
- text: the clause text
- contract_type: NDA, Freelance, Employment, Service
- clause_type: payment, termination, confidentiality etc
"""

STANDARD_TEMPLATES = [
    # ─── PAYMENT CLAUSES ───
    {
        "id": "nda_payment_1",
        "text": "Payment shall be made within 30 days of receipt of invoice. Late payments shall attract interest at 2% per month on the outstanding amount.",
        "contract_type": "NDA",
        "clause_type": "payment"
    },
    {
        "id": "freelance_payment_1",
        "text": "The client shall pay 50% of the total fee upfront before work commences and the remaining 50% upon delivery of the final deliverable.",
        "contract_type": "Freelance",
        "clause_type": "payment"
    },
    {
        "id": "service_payment_1",
        "text": "Service charges shall be paid monthly within 15 days of submission of invoice. The Institute reserves the right to deduct penalties from payments due.",
        "contract_type": "Service",
        "clause_type": "payment"
    },

    # ─── TERMINATION CLAUSES ───
    {
        "id": "nda_termination_1",
        "text": "Either party may terminate this agreement by providing 30 days written notice to the other party. Termination shall not affect any rights or obligations accrued before the termination date.",
        "contract_type": "NDA",
        "clause_type": "termination"
    },
    {
        "id": "freelance_termination_1",
        "text": "The client may terminate this contract immediately for cause, including non-performance or breach of terms. The service provider shall be paid only for work completed up to the termination date.",
        "contract_type": "Freelance",
        "clause_type": "termination"
    },
    {
        "id": "employment_termination_1",
        "text": "Employment may be terminated by either party with 30 days notice or payment in lieu thereof. The employer reserves the right to terminate immediately for gross misconduct.",
        "contract_type": "Employment",
        "clause_type": "termination"
    },

    # ─── CONFIDENTIALITY CLAUSES ───
    {
        "id": "nda_confidentiality_1",
        "text": "Both parties agree to maintain strict confidentiality of all information shared under this agreement and shall not disclose it to any third party without prior written consent.",
        "contract_type": "NDA",
        "clause_type": "confidentiality"
    },
    {
        "id": "employment_confidentiality_1",
        "text": "The employee shall not disclose any proprietary, technical or business information of the employer during or after employment without explicit written authorization.",
        "contract_type": "Employment",
        "clause_type": "confidentiality"
    },

    # ─── LIABILITY CLAUSES ───
    {
        "id": "service_liability_1",
        "text": "The service provider shall be liable for any loss or damage caused due to negligence or wilful misconduct. The Institute shall not be liable for any indirect or consequential losses.",
        "contract_type": "Service",
        "clause_type": "liability"
    },
    {
        "id": "freelance_liability_1",
        "text": "The total liability of either party shall not exceed the total fees paid under this contract in the preceding 3 months.",
        "contract_type": "Freelance",
        "clause_type": "liability"
    },

    # ─── DISPUTE RESOLUTION ───
    {
        "id": "service_dispute_1",
        "text": "Any dispute arising out of this agreement shall be referred to arbitration. The arbitrator shall be appointed by mutual consent and the decision shall be final and binding.",
        "contract_type": "Service",
        "clause_type": "dispute_resolution"
    },
    {
        "id": "employment_dispute_1",
        "text": "All disputes shall be subject to the exclusive jurisdiction of courts in Mumbai. The parties agree to attempt resolution through mediation before initiating legal proceedings.",
        "contract_type": "Employment",
        "clause_type": "dispute_resolution"
    },

    # ─── INTELLECTUAL PROPERTY ───
    {
        "id": "freelance_ip_1",
        "text": "All work product, deliverables and intellectual property created under this contract shall be the exclusive property of the client upon full payment.",
        "contract_type": "Freelance",
        "clause_type": "intellectual_property"
    },
    {
        "id": "employment_ip_1",
        "text": "Any invention, software, design or creative work developed during employment shall be the sole property of the employer, whether or not developed during working hours.",
        "contract_type": "Employment",
        "clause_type": "intellectual_property"
    },

    # ─── SECURITY DEPOSIT ───
    {
        "id": "service_security_1",
        "text": "The service provider shall deposit a security amount before commencement of work. This deposit shall be refunded within 60 days of contract completion subject to no outstanding dues.",
        "contract_type": "Service",
        "clause_type": "security_deposit"
    },

    # ─── FORCE MAJEURE ───
    {
        "id": "service_force_majeure_1",
        "text": "Neither party shall be liable for delays or failure to perform due to circumstances beyond their reasonable control including acts of God, war, strikes or government regulations.",
        "contract_type": "Service",
        "clause_type": "force_majeure"
    },
    {
        "id": "freelance_force_majeure_1",
        "text": "In case of force majeure lasting more than 30 days, either party may terminate the contract without penalty. The service provider shall be paid for work completed up to that date.",
        "contract_type": "Freelance",
        "clause_type": "force_majeure"
    },

    # ─── GOVERNING LAW ───
    {
        "id": "service_governing_law_1",
        "text": "This agreement shall be governed by and construed in accordance with the laws of India. All disputes shall be subject to the jurisdiction of courts in the city where the Institute is located.",
        "contract_type": "Service",
        "clause_type": "governing_law"
    },
    {
        "id": "employment_governing_law_1",
        "text": "This contract shall be governed by Indian law. Any legal proceedings shall be initiated in the courts of competent jurisdiction in the state where the employer is registered.",
        "contract_type": "Employment",
        "clause_type": "governing_law"
    },
]