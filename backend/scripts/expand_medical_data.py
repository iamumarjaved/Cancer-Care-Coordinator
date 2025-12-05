"""Script to expand medical data files with comprehensive real-world content."""

import json
from pathlib import Path

# Base directory for mock data
DATA_DIR = Path(__file__).parent.parent / "rag" / "mock_data"


def generate_expanded_guidelines():
    """Generate expanded NCCN guidelines covering multiple cancer types."""

    # Load existing NSCLC guidelines
    with open(DATA_DIR / "mock_nccn_guidelines.json") as f:
        guidelines = json.load(f)

    # Add Breast Cancer Guidelines
    breast_guidelines = [
        {
            "id": "nccn_breast_her2pos_1",
            "title": "HER2-Positive Metastatic Breast Cancer First-Line",
            "cancer_type": "Breast",
            "evidence_level": "Category 1",
            "content": "For HER2-positive metastatic breast cancer, the preferred first-line regimen is pertuzumab + trastuzumab + taxane (docetaxel or paclitaxel) based on CLEOPATRA trial showing improved OS. After progression, T-DM1 (ado-trastuzumab emtansine) is preferred (EMILIA trial). Third-line options include trastuzumab deruxtecan (T-DXd) or tucatinib + trastuzumab + capecitabine.",
            "source": "NCCN Guidelines Breast Cancer v4.2024",
            "year": 2024
        },
        {
            "id": "nccn_breast_her2pos_2",
            "title": "HER2-Positive Early Breast Cancer Adjuvant Therapy",
            "cancer_type": "Breast",
            "evidence_level": "Category 1",
            "content": "For HER2-positive early breast cancer, adjuvant therapy with trastuzumab-based regimens is standard of care. For node-positive or high-risk disease, AC-THP (anthracycline-based with pertuzumab) or TCHP (non-anthracycline) are preferred. Duration is 1 year of HER2-targeted therapy. For residual disease after neoadjuvant therapy, T-DM1 for 14 cycles is recommended (KATHERINE trial).",
            "source": "NCCN Guidelines Breast Cancer v4.2024",
            "year": 2024
        },
        {
            "id": "nccn_breast_tnbc_1",
            "title": "Triple-Negative Breast Cancer Metastatic First-Line",
            "cancer_type": "Breast",
            "evidence_level": "Category 1",
            "content": "For metastatic triple-negative breast cancer (TNBC), pembrolizumab + chemotherapy (nab-paclitaxel, paclitaxel, or gem/carbo) is preferred for PD-L1 CPS ≥10 (KEYNOTE-355). For BRCA1/2-mutated TNBC, olaparib or talazoparib are preferred (OlympiAD). Sacituzumab govitecan is recommended after ≥2 prior therapies (ASCENT trial).",
            "source": "NCCN Guidelines Breast Cancer v4.2024",
            "year": 2024
        },
        {
            "id": "nccn_breast_tnbc_2",
            "title": "Triple-Negative Breast Cancer Early Stage",
            "cancer_type": "Breast",
            "evidence_level": "Category 1",
            "content": "For early-stage TNBC ≥2cm or node-positive, neoadjuvant pembrolizumab + chemotherapy followed by adjuvant pembrolizumab is recommended (KEYNOTE-522). Pathologic complete response (pCR) rates are approximately 65%. For residual disease, capecitabine adjuvant therapy may be considered (CREATE-X trial).",
            "source": "NCCN Guidelines Breast Cancer v4.2024",
            "year": 2024
        },
        {
            "id": "nccn_breast_hrpos_1",
            "title": "HR-Positive/HER2-Negative Metastatic Breast Cancer",
            "cancer_type": "Breast",
            "evidence_level": "Category 1",
            "content": "For HR-positive/HER2-negative metastatic breast cancer, CDK4/6 inhibitor (palbociclib, ribociclib, or abemaciclib) + aromatase inhibitor or fulvestrant is preferred first-line therapy. For ESR1-mutated disease, elacestrant is an option. For PIK3CA-mutated, alpelisib + fulvestrant is recommended. PARP inhibitors for BRCA-mutated disease.",
            "source": "NCCN Guidelines Breast Cancer v4.2024",
            "year": 2024
        },
        {
            "id": "nccn_breast_hrpos_2",
            "title": "HR-Positive Early Breast Cancer Adjuvant Endocrine Therapy",
            "cancer_type": "Breast",
            "evidence_level": "Category 1",
            "content": "For HR-positive early breast cancer, adjuvant endocrine therapy is essential. Premenopausal: tamoxifen ± ovarian suppression (OFS) for 5-10 years. Postmenopausal: aromatase inhibitor (anastrozole, letrozole, exemestane) preferred, or switch strategy. High-risk patients may benefit from extended therapy beyond 5 years. Abemaciclib may be added for high-risk node-positive disease (monarchE).",
            "source": "NCCN Guidelines Breast Cancer v4.2024",
            "year": 2024
        },
        {
            "id": "nccn_breast_brca_1",
            "title": "BRCA-Mutated Breast Cancer Treatment",
            "cancer_type": "Breast",
            "evidence_level": "Category 1",
            "content": "For BRCA1/2-mutated breast cancer, PARP inhibitors are key targeted therapies. Olaparib or talazoparib for HER2-negative metastatic breast cancer with germline BRCA mutation (OlympiAD, EMBRACA). Adjuvant olaparib for 1 year in high-risk HER2-negative early breast cancer (OlympiA). Consider platinum-based chemotherapy for TNBC.",
            "source": "NCCN Guidelines Breast Cancer v4.2024",
            "year": 2024
        },
        {
            "id": "nccn_breast_biomarker_1",
            "title": "Biomarker Testing in Breast Cancer",
            "cancer_type": "Breast",
            "evidence_level": "Category 1",
            "content": "Essential biomarker testing: ER, PR, HER2 (IHC and FISH if equivocal). For metastatic disease, additional testing includes: germline BRCA1/2, PIK3CA mutation (HR+/HER2-), PD-L1 (TNBC), ESR1 mutation (after prior endocrine therapy), and NTRK fusion. Gene expression assays (Oncotype DX, MammaPrint) help guide adjuvant chemotherapy decisions in early-stage HR+/HER2- disease.",
            "source": "NCCN Guidelines Breast Cancer v4.2024",
            "year": 2024
        }
    ]

    # Add Colorectal Cancer Guidelines
    colorectal_guidelines = [
        {
            "id": "nccn_crc_kras_1",
            "title": "KRAS/NRAS Wild-Type Metastatic Colorectal Cancer",
            "cancer_type": "Colorectal",
            "evidence_level": "Category 1",
            "content": "For RAS wild-type (KRAS/NRAS exons 2-4) metastatic colorectal cancer, anti-EGFR therapy (cetuximab or panitumumab) + chemotherapy (FOLFOX or FOLFIRI) is recommended for left-sided tumors. For right-sided tumors, bevacizumab + chemotherapy is preferred due to reduced efficacy of anti-EGFR agents. Extended RAS testing is mandatory before anti-EGFR therapy.",
            "source": "NCCN Guidelines Colon Cancer v3.2024",
            "year": 2024
        },
        {
            "id": "nccn_crc_kras_2",
            "title": "KRAS G12C-Mutated Metastatic Colorectal Cancer",
            "cancer_type": "Colorectal",
            "evidence_level": "Category 2A",
            "content": "For KRAS G12C-mutated metastatic colorectal cancer after prior therapy, sotorasib + panitumumab is a recommended option (CodeBreaK 300 trial). This represents the first targeted therapy for KRAS-mutated CRC. Adagrasib combinations are also under investigation. Single-agent KRAS G12C inhibitors have limited efficacy in CRC.",
            "source": "NCCN Guidelines Colon Cancer v3.2024",
            "year": 2024
        },
        {
            "id": "nccn_crc_msi_1",
            "title": "MSI-High/dMMR Metastatic Colorectal Cancer",
            "cancer_type": "Colorectal",
            "evidence_level": "Category 1",
            "content": "For MSI-high or mismatch repair deficient (dMMR) metastatic colorectal cancer, first-line pembrolizumab or nivolumab ± ipilimumab is preferred over chemotherapy (KEYNOTE-177). Response rates are ~45% with durable responses. MSI/MMR testing is recommended for all CRC patients at diagnosis. Lynch syndrome screening should be considered.",
            "source": "NCCN Guidelines Colon Cancer v3.2024",
            "year": 2024
        },
        {
            "id": "nccn_crc_braf_1",
            "title": "BRAF V600E-Mutated Metastatic Colorectal Cancer",
            "cancer_type": "Colorectal",
            "evidence_level": "Category 2A",
            "content": "For BRAF V600E-mutated metastatic CRC, encorafenib + cetuximab ± binimetinib is recommended after prior therapy (BEACON trial). First-line intensive chemotherapy (FOLFOXIRI + bevacizumab) may be considered. BRAF V600E mutation is associated with poor prognosis. MSI status should be assessed as ~20% are MSI-H.",
            "source": "NCCN Guidelines Colon Cancer v3.2024",
            "year": 2024
        },
        {
            "id": "nccn_crc_her2_1",
            "title": "HER2-Amplified Metastatic Colorectal Cancer",
            "cancer_type": "Colorectal",
            "evidence_level": "Category 2A",
            "content": "For HER2-amplified (3+ by IHC or FISH+) metastatic CRC that is RAS/BRAF wild-type, trastuzumab + pertuzumab or trastuzumab deruxtecan are options after progression on standard therapies (HERACLES, MyPathway, DESTINY-CRC01). HER2 amplification occurs in ~3% of CRC, more common in RAS wild-type.",
            "source": "NCCN Guidelines Colon Cancer v3.2024",
            "year": 2024
        },
        {
            "id": "nccn_crc_adjuvant_1",
            "title": "Stage III Colon Cancer Adjuvant Chemotherapy",
            "cancer_type": "Colorectal",
            "evidence_level": "Category 1",
            "content": "For stage III colon cancer, adjuvant oxaliplatin-based chemotherapy (FOLFOX or CAPEOX) is standard of care. Duration: 6 months for high-risk, 3 months acceptable for low-risk T1-3N1 (IDEA collaboration). Consider 3-month CAPEOX to reduce neuropathy. 5-FU/LV alone for patients unable to tolerate oxaliplatin. ctDNA testing may help guide decisions.",
            "source": "NCCN Guidelines Colon Cancer v3.2024",
            "year": 2024
        },
        {
            "id": "nccn_crc_biomarker_1",
            "title": "Biomarker Testing in Colorectal Cancer",
            "cancer_type": "Colorectal",
            "evidence_level": "Category 1",
            "content": "Essential biomarker testing for metastatic CRC: Extended RAS (KRAS/NRAS exons 2-4), BRAF V600E, MSI/MMR status, HER2 amplification. Consider NTRK fusion testing. UGT1A1 genotyping before irinotecan. NGS panel preferred for comprehensive testing. All patients should be screened for Lynch syndrome. Sidedness matters for treatment selection.",
            "source": "NCCN Guidelines Colon Cancer v3.2024",
            "year": 2024
        }
    ]

    # Add Melanoma Guidelines
    melanoma_guidelines = [
        {
            "id": "nccn_melanoma_braf_1",
            "title": "BRAF V600-Mutated Unresectable/Metastatic Melanoma",
            "cancer_type": "Melanoma",
            "evidence_level": "Category 1",
            "content": "For BRAF V600-mutated unresectable or metastatic melanoma, options include: (1) Anti-PD-1 ± anti-CTLA-4 (preferred for most patients), or (2) BRAF + MEK inhibitor combination (dabrafenib/trametinib, vemurafenib/cobimetinib, or encorafenib/binimetinib). Immunotherapy is often preferred first-line given potential for durable responses. BRAF/MEK may be preferred for rapidly progressive disease.",
            "source": "NCCN Guidelines Melanoma v2.2024",
            "year": 2024
        },
        {
            "id": "nccn_melanoma_braf_2",
            "title": "BRAF Wild-Type Unresectable/Metastatic Melanoma",
            "cancer_type": "Melanoma",
            "evidence_level": "Category 1",
            "content": "For BRAF wild-type unresectable or metastatic melanoma, checkpoint inhibitor immunotherapy is standard of care: nivolumab + ipilimumab (CheckMate 067), pembrolizumab, or nivolumab monotherapy. Relatlimab + nivolumab is another option (RELATIVITY-047). Choice depends on patient factors and tolerability. Intratumoral therapy (T-VEC) for accessible lesions.",
            "source": "NCCN Guidelines Melanoma v2.2024",
            "year": 2024
        },
        {
            "id": "nccn_melanoma_adjuvant_1",
            "title": "Stage III Melanoma Adjuvant Therapy",
            "cancer_type": "Melanoma",
            "evidence_level": "Category 1",
            "content": "For resected stage III melanoma, adjuvant therapy options include: pembrolizumab (KEYNOTE-054) or nivolumab (CheckMate 238) for all patients; dabrafenib/trametinib for BRAF V600-mutated disease (COMBI-AD). Duration is typically 1 year. Consider observation for low-risk stage IIIA. Active surveillance with imaging per NCCN guidelines.",
            "source": "NCCN Guidelines Melanoma v2.2024",
            "year": 2024
        },
        {
            "id": "nccn_melanoma_neoadjuvant_1",
            "title": "Stage III Melanoma Neoadjuvant Therapy",
            "cancer_type": "Melanoma",
            "evidence_level": "Category 2A",
            "content": "Neoadjuvant immunotherapy is emerging as a preferred approach for resectable stage III melanoma. Pembrolizumab neoadjuvant followed by adjuvant (SWOG S1801) showed improved EFS vs adjuvant alone. Neoadjuvant nivolumab + ipilimumab also shows high pCR rates. Consider neoadjuvant therapy for clinically bulky nodal disease.",
            "source": "NCCN Guidelines Melanoma v2.2024",
            "year": 2024
        },
        {
            "id": "nccn_melanoma_ckit_1",
            "title": "KIT-Mutated Melanoma",
            "cancer_type": "Melanoma",
            "evidence_level": "Category 2A",
            "content": "For KIT-mutated melanoma (acral, mucosal, or chronic sun-damaged skin), imatinib is an option if anti-PD-1 therapy is not appropriate or after progression. KIT mutations occur in ~15-20% of acral/mucosal melanomas. Response rates are ~20-25% with KIT inhibitors. Immunotherapy remains preferred first-line approach.",
            "source": "NCCN Guidelines Melanoma v2.2024",
            "year": 2024
        },
        {
            "id": "nccn_melanoma_brain_1",
            "title": "Melanoma Brain Metastases",
            "cancer_type": "Melanoma",
            "evidence_level": "Category 2A",
            "content": "For melanoma brain metastases, systemic therapy with intracranial activity is preferred: nivolumab + ipilimumab has ~50% intracranial response rate (CheckMate 204). BRAF/MEK inhibitors also have CNS activity for BRAF-mutated. Local therapy (SRS, surgery) for limited metastases. Avoid whole brain radiation if possible given neurocognitive effects.",
            "source": "NCCN Guidelines Melanoma v2.2024",
            "year": 2024
        },
        {
            "id": "nccn_melanoma_biomarker_1",
            "title": "Biomarker Testing in Melanoma",
            "cancer_type": "Melanoma",
            "evidence_level": "Category 1",
            "content": "BRAF V600 mutation testing is required for all patients with unresectable or metastatic melanoma before treatment. Consider KIT mutation testing for acral, mucosal, or chronic sun-damaged skin melanomas. NTRK fusion testing may be considered. PD-L1 is not required for treatment decisions. Tumor mutational burden and ctDNA under investigation.",
            "source": "NCCN Guidelines Melanoma v2.2024",
            "year": 2024
        }
    ]

    # Add Pancreatic Cancer Guidelines
    pancreatic_guidelines = [
        {
            "id": "nccn_pancreas_adjuvant_1",
            "title": "Resected Pancreatic Cancer Adjuvant Therapy",
            "cancer_type": "Pancreatic",
            "evidence_level": "Category 1",
            "content": "For resected pancreatic adenocarcinoma, adjuvant chemotherapy is standard of care. Preferred regimens: modified FOLFIRINOX for ECOG 0-1 patients (PRODIGE 24), or gemcitabine/capecitabine (ESPAC-4). Single-agent gemcitabine for patients unable to tolerate combination therapy. Consider adjuvant chemoradiation for R1 resections.",
            "source": "NCCN Guidelines Pancreatic Cancer v2.2024",
            "year": 2024
        },
        {
            "id": "nccn_pancreas_metastatic_1",
            "title": "Metastatic Pancreatic Cancer First-Line Therapy",
            "cancer_type": "Pancreatic",
            "evidence_level": "Category 1",
            "content": "For metastatic pancreatic adenocarcinoma with good PS (ECOG 0-1), FOLFIRINOX or gemcitabine/nab-paclitaxel are preferred first-line options. FOLFIRINOX shows higher response rates but more toxicity. Gemcitabine alone for poor PS. NALIRIFOX is a new option (NAPOLI-3). MSI-high tumors may benefit from pembrolizumab.",
            "source": "NCCN Guidelines Pancreatic Cancer v2.2024",
            "year": 2024
        },
        {
            "id": "nccn_pancreas_brca_1",
            "title": "BRCA-Mutated Pancreatic Cancer",
            "cancer_type": "Pancreatic",
            "evidence_level": "Category 1",
            "content": "For germline BRCA1/2-mutated metastatic pancreatic cancer without progression on platinum-based chemotherapy, olaparib maintenance is recommended (POLO trial). Platinum-based chemotherapy (FOLFIRINOX) is preferred first-line for BRCA-mutated disease. All patients should be offered germline testing. Consider family genetic counseling.",
            "source": "NCCN Guidelines Pancreatic Cancer v2.2024",
            "year": 2024
        },
        {
            "id": "nccn_pancreas_borderline_1",
            "title": "Borderline Resectable Pancreatic Cancer",
            "cancer_type": "Pancreatic",
            "evidence_level": "Category 2A",
            "content": "For borderline resectable pancreatic cancer, neoadjuvant therapy is preferred before surgical exploration. Options include FOLFIRINOX, gemcitabine/nab-paclitaxel, or chemoradiation. Goal is to achieve vascular margin clearance and select patients who will benefit from surgery. Restaging imaging after neoadjuvant therapy to assess resectability.",
            "source": "NCCN Guidelines Pancreatic Cancer v2.2024",
            "year": 2024
        },
        {
            "id": "nccn_pancreas_biomarker_1",
            "title": "Biomarker Testing in Pancreatic Cancer",
            "cancer_type": "Pancreatic",
            "evidence_level": "Category 1",
            "content": "Recommended testing: germline BRCA1/2, PALB2 (all patients); somatic testing for MSI-high/dMMR, KRAS, NTRK fusion. Consider HRD testing. ~5-10% have germline BRCA1/2 mutations. Approximately 1% are MSI-high. KRAS mutations present in ~90% but not directly targetable (except G12C which is rare in pancreatic cancer).",
            "source": "NCCN Guidelines Pancreatic Cancer v2.2024",
            "year": 2024
        }
    ]

    # Combine all guidelines
    guidelines.extend(breast_guidelines)
    guidelines.extend(colorectal_guidelines)
    guidelines.extend(melanoma_guidelines)
    guidelines.extend(pancreatic_guidelines)

    # Save expanded guidelines
    with open(DATA_DIR / "mock_nccn_guidelines.json", "w") as f:
        json.dump(guidelines, f, indent=2)

    print(f"Generated {len(guidelines)} NCCN guidelines")
    return len(guidelines)


def generate_expanded_trials():
    """Generate expanded clinical trials for multiple cancer types."""

    with open(DATA_DIR / "mock_clinical_trials.json") as f:
        trials = json.load(f)

    # Add breast cancer trials
    breast_trials = [
        {
            "nct_id": "NCT04191135",
            "title": "DESTINY-Breast04: T-DXd in HER2-Low Breast Cancer",
            "phase": "Phase III",
            "status": "Completed",
            "sponsor": "Daiichi Sankyo/AstraZeneca",
            "intervention": "Trastuzumab deruxtecan",
            "description": "Study comparing trastuzumab deruxtecan to physician's choice chemotherapy in HER2-low (IHC 1+ or 2+/ISH-) unresectable or metastatic breast cancer after prior chemotherapy.",
            "eligibility": "HER2-low breast cancer, HR+/HR-, prior chemotherapy, ECOG 0-1",
            "biomarker": "HER2-low",
            "mutations": [],
            "cancer_type": "Breast"
        },
        {
            "nct_id": "NCT03901339",
            "title": "KEYNOTE-522: Pembrolizumab in Early TNBC",
            "phase": "Phase III",
            "status": "Completed",
            "sponsor": "Merck",
            "intervention": "Pembrolizumab + Chemotherapy",
            "description": "Neoadjuvant pembrolizumab plus chemotherapy followed by adjuvant pembrolizumab in early triple-negative breast cancer.",
            "eligibility": "Early-stage TNBC T1c N1-2 or T2-4 N0-2, ECOG 0-1",
            "biomarker": "TNBC",
            "mutations": [],
            "cancer_type": "Breast"
        },
        {
            "nct_id": "NCT03691051",
            "title": "monarchE: Abemaciclib in High-Risk HR+ Early Breast Cancer",
            "phase": "Phase III",
            "status": "Completed",
            "sponsor": "Eli Lilly",
            "intervention": "Abemaciclib + Endocrine Therapy",
            "description": "Adjuvant abemaciclib combined with endocrine therapy in high-risk HR+/HER2- early breast cancer.",
            "eligibility": "HR+/HER2- early breast cancer, node-positive, Ki-67 ≥20%, ECOG 0-1",
            "biomarker": "HR+",
            "mutations": [],
            "cancer_type": "Breast"
        },
        {
            "nct_id": "NCT02810743",
            "title": "OlympiA: Olaparib in gBRCA Early Breast Cancer",
            "phase": "Phase III",
            "status": "Completed",
            "sponsor": "AstraZeneca",
            "intervention": "Olaparib",
            "description": "Adjuvant olaparib in patients with germline BRCA1/2 mutations and high-risk HER2-negative early breast cancer.",
            "eligibility": "gBRCA1/2 mutation, HER2-negative, completed neoadjuvant/adjuvant chemotherapy",
            "biomarker": "BRCA",
            "mutations": ["BRCA1", "BRCA2"],
            "cancer_type": "Breast"
        },
        {
            "nct_id": "NCT04964934",
            "title": "EMBER-3: Imlunestrant in ER+ Advanced Breast Cancer",
            "phase": "Phase III",
            "status": "Recruiting",
            "sponsor": "Eli Lilly",
            "intervention": "Imlunestrant",
            "description": "Oral SERD imlunestrant vs standard endocrine therapy in ER+/HER2- advanced breast cancer with ESR1 mutation.",
            "eligibility": "ER+/HER2- metastatic breast cancer, ESR1 mutation, prior CDK4/6 inhibitor",
            "biomarker": "ESR1",
            "mutations": ["ESR1"],
            "cancer_type": "Breast"
        }
    ]

    # Add colorectal cancer trials
    colorectal_trials = [
        {
            "nct_id": "NCT05198934",
            "title": "KRYSTAL-10: Adagrasib + Cetuximab in KRAS G12C CRC",
            "phase": "Phase III",
            "status": "Recruiting",
            "sponsor": "Mirati Therapeutics",
            "intervention": "Adagrasib + Cetuximab",
            "description": "Study comparing adagrasib plus cetuximab to chemotherapy in KRAS G12C-mutated metastatic colorectal cancer.",
            "eligibility": "KRAS G12C mutation, metastatic CRC, prior fluoropyrimidine and oxaliplatin, ECOG 0-1",
            "biomarker": "KRAS",
            "mutations": ["G12C"],
            "cancer_type": "Colorectal"
        },
        {
            "nct_id": "NCT02912559",
            "title": "KEYNOTE-177: Pembrolizumab in MSI-H CRC",
            "phase": "Phase III",
            "status": "Completed",
            "sponsor": "Merck",
            "intervention": "Pembrolizumab",
            "description": "First-line pembrolizumab versus chemotherapy in MSI-H/dMMR metastatic colorectal cancer.",
            "eligibility": "MSI-H or dMMR, metastatic CRC, treatment-naive, ECOG 0-1",
            "biomarker": "MSI-H",
            "mutations": [],
            "cancer_type": "Colorectal"
        },
        {
            "nct_id": "NCT04931654",
            "title": "BREAKWATER: Encorafenib + Cetuximab First-Line in BRAF V600E CRC",
            "phase": "Phase III",
            "status": "Recruiting",
            "sponsor": "Pfizer/Array BioPharma",
            "intervention": "Encorafenib + Cetuximab + Chemo",
            "description": "First-line encorafenib plus cetuximab with or without chemotherapy in BRAF V600E-mutated metastatic CRC.",
            "eligibility": "BRAF V600E mutation, metastatic CRC, treatment-naive, ECOG 0-1",
            "biomarker": "BRAF",
            "mutations": ["V600E"],
            "cancer_type": "Colorectal"
        },
        {
            "nct_id": "NCT05064059",
            "title": "ctDNA-Guided Adjuvant Therapy in Stage II Colon Cancer",
            "phase": "Phase III",
            "status": "Recruiting",
            "sponsor": "NCI",
            "intervention": "ctDNA-guided treatment",
            "description": "Circulating tumor DNA-guided adjuvant chemotherapy in stage II colon cancer.",
            "eligibility": "Stage II colon cancer, post-resection, ctDNA evaluable",
            "biomarker": "ctDNA",
            "mutations": [],
            "cancer_type": "Colorectal"
        }
    ]

    # Add melanoma trials
    melanoma_trials = [
        {
            "nct_id": "NCT03068455",
            "title": "RELATIVITY-047: Relatlimab + Nivolumab in Melanoma",
            "phase": "Phase III",
            "status": "Completed",
            "sponsor": "Bristol-Myers Squibb",
            "intervention": "Relatlimab + Nivolumab",
            "description": "First-line relatlimab plus nivolumab versus nivolumab alone in unresectable or metastatic melanoma.",
            "eligibility": "Unresectable or metastatic melanoma, treatment-naive, ECOG 0-1",
            "biomarker": "LAG-3",
            "mutations": [],
            "cancer_type": "Melanoma"
        },
        {
            "nct_id": "NCT02908672",
            "title": "COMBI-AD: Dabrafenib + Trametinib Adjuvant in Melanoma",
            "phase": "Phase III",
            "status": "Completed",
            "sponsor": "Novartis",
            "intervention": "Dabrafenib + Trametinib",
            "description": "Adjuvant dabrafenib plus trametinib in resected stage III BRAF V600-mutated melanoma.",
            "eligibility": "Resected stage III melanoma, BRAF V600E/K mutation, ECOG 0-1",
            "biomarker": "BRAF",
            "mutations": ["V600E", "V600K"],
            "cancer_type": "Melanoma"
        },
        {
            "nct_id": "NCT05445583",
            "title": "Lifileucel (TIL Therapy) in Advanced Melanoma",
            "phase": "Phase II/III",
            "status": "Recruiting",
            "sponsor": "Iovance Biotherapeutics",
            "intervention": "Lifileucel (TIL)",
            "description": "Tumor-infiltrating lymphocyte therapy in advanced melanoma after prior anti-PD-1.",
            "eligibility": "Unresectable or metastatic melanoma, prior anti-PD-1, ECOG 0-1",
            "biomarker": "TIL",
            "mutations": [],
            "cancer_type": "Melanoma"
        },
        {
            "nct_id": "NCT02977052",
            "title": "SWOG S1801: Neoadjuvant Pembrolizumab in Stage III/IV Melanoma",
            "phase": "Phase II",
            "status": "Completed",
            "sponsor": "NCI/SWOG",
            "intervention": "Neoadjuvant Pembrolizumab",
            "description": "Neoadjuvant plus adjuvant pembrolizumab vs adjuvant pembrolizumab alone in resectable stage III/IV melanoma.",
            "eligibility": "Resectable stage IIIB-IV melanoma, ECOG 0-1",
            "biomarker": "PD-1",
            "mutations": [],
            "cancer_type": "Melanoma"
        }
    ]

    # Add more trials
    trials.extend(breast_trials)
    trials.extend(colorectal_trials)
    trials.extend(melanoma_trials)

    with open(DATA_DIR / "mock_clinical_trials.json", "w") as f:
        json.dump(trials, f, indent=2)

    print(f"Generated {len(trials)} clinical trials")
    return len(trials)


def generate_expanded_mutations():
    """Generate expanded OncoKB mutations database."""

    with open(DATA_DIR / "mock_oncokb_mutations.json") as f:
        mutations = json.load(f)

    # Add breast cancer mutations
    breast_mutations = [
        {
            "gene": "PIK3CA",
            "variant": "H1047R",
            "classification": "Oncogenic",
            "cancer_type": "Breast",
            "therapies": ["Alpelisib + Fulvestrant"],
            "clinical_significance": "Level 1 evidence for alpelisib in HR+/HER2- metastatic breast cancer (SOLAR-1). Most common PIK3CA hotspot mutation.",
            "notes": "Present in ~40% of HR+ breast cancers. Alpelisib requires glucose monitoring."
        },
        {
            "gene": "PIK3CA",
            "variant": "E545K",
            "classification": "Oncogenic",
            "cancer_type": "Breast",
            "therapies": ["Alpelisib + Fulvestrant"],
            "clinical_significance": "Level 1 evidence for alpelisib. Second most common PIK3CA hotspot.",
            "notes": "PI3K inhibitor sensitivity confirmed in clinical trials."
        },
        {
            "gene": "ESR1",
            "variant": "Y537S",
            "classification": "Oncogenic",
            "cancer_type": "Breast",
            "therapies": ["Elacestrant", "Fulvestrant"],
            "clinical_significance": "Level 1 evidence for elacestrant (EMERALD). Confers resistance to aromatase inhibitors.",
            "notes": "Acquired resistance mutation. Oral SERD elacestrant has improved efficacy."
        },
        {
            "gene": "ESR1",
            "variant": "D538G",
            "classification": "Oncogenic",
            "cancer_type": "Breast",
            "therapies": ["Elacestrant", "Fulvestrant"],
            "clinical_significance": "Level 1 evidence for elacestrant. Common ESR1 resistance mutation.",
            "notes": "Detected by ctDNA in ~30% of patients after AI therapy."
        },
        {
            "gene": "ERBB2",
            "variant": "Amplification",
            "classification": "Oncogenic",
            "cancer_type": "Breast",
            "therapies": ["Trastuzumab", "Pertuzumab", "T-DM1", "Trastuzumab deruxtecan"],
            "clinical_significance": "Level 1 evidence for HER2-targeted therapy. Defines HER2-positive breast cancer.",
            "notes": "~15-20% of breast cancers. Testing by IHC and FISH required."
        }
    ]

    # Add colorectal mutations
    colorectal_mutations = [
        {
            "gene": "KRAS",
            "variant": "G12D",
            "classification": "Oncogenic",
            "cancer_type": "Colorectal",
            "therapies": [],
            "clinical_significance": "Predictive of resistance to anti-EGFR therapy. Most common KRAS mutation in CRC (~35%).",
            "notes": "No approved targeted therapy. Precludes cetuximab/panitumumab."
        },
        {
            "gene": "KRAS",
            "variant": "G12V",
            "classification": "Oncogenic",
            "cancer_type": "Colorectal",
            "therapies": [],
            "clinical_significance": "Predictive of resistance to anti-EGFR therapy. Second most common KRAS mutation.",
            "notes": "Investigational therapies under development."
        },
        {
            "gene": "KRAS",
            "variant": "G13D",
            "classification": "Oncogenic",
            "cancer_type": "Colorectal",
            "therapies": [],
            "clinical_significance": "Some data suggest possible partial sensitivity to cetuximab but not recommended.",
            "notes": "Less common KRAS mutation. Anti-EGFR generally avoided."
        },
        {
            "gene": "NRAS",
            "variant": "Q61K",
            "classification": "Oncogenic",
            "cancer_type": "Colorectal",
            "therapies": [],
            "clinical_significance": "Predictive of resistance to anti-EGFR therapy. Must test before cetuximab/panitumumab.",
            "notes": "NRAS mutations present in ~5% of CRC."
        },
        {
            "gene": "BRAF",
            "variant": "V600E",
            "classification": "Oncogenic",
            "cancer_type": "Colorectal",
            "therapies": ["Encorafenib + Cetuximab"],
            "clinical_significance": "Level 1 evidence for BRAF+EGFR inhibition (BEACON). Poor prognosis marker.",
            "notes": "Present in ~10% of mCRC. Often right-sided. ~20% are MSI-H."
        }
    ]

    # Add melanoma mutations
    melanoma_mutations = [
        {
            "gene": "BRAF",
            "variant": "V600E",
            "classification": "Oncogenic",
            "cancer_type": "Melanoma",
            "therapies": ["Dabrafenib + Trametinib", "Vemurafenib + Cobimetinib", "Encorafenib + Binimetinib"],
            "clinical_significance": "Level 1 evidence for BRAF+MEK inhibition. ~50% of melanomas harbor BRAF V600 mutations.",
            "notes": "Most common BRAF mutation in melanoma. Combination therapy required."
        },
        {
            "gene": "BRAF",
            "variant": "V600K",
            "classification": "Oncogenic",
            "cancer_type": "Melanoma",
            "therapies": ["Dabrafenib + Trametinib", "Vemurafenib + Cobimetinib", "Encorafenib + Binimetinib"],
            "clinical_significance": "Level 1 evidence for BRAF+MEK inhibition. Second most common BRAF mutation (~5-10%).",
            "notes": "Similar response to V600E with BRAF/MEK inhibitors."
        },
        {
            "gene": "NRAS",
            "variant": "Q61R",
            "classification": "Oncogenic",
            "cancer_type": "Melanoma",
            "therapies": [],
            "clinical_significance": "Level 3 evidence. No approved targeted therapy. MEK inhibitors being studied.",
            "notes": "Present in ~20% of melanomas. Mutually exclusive with BRAF."
        },
        {
            "gene": "KIT",
            "variant": "L576P",
            "classification": "Oncogenic",
            "cancer_type": "Melanoma",
            "therapies": ["Imatinib"],
            "clinical_significance": "Level 2 evidence for KIT inhibitors in acral/mucosal melanoma.",
            "notes": "Most common KIT mutation. ~15% of acral/mucosal melanomas."
        },
        {
            "gene": "KIT",
            "variant": "Amplification",
            "classification": "Oncogenic",
            "cancer_type": "Melanoma",
            "therapies": ["Imatinib"],
            "clinical_significance": "Level 3 evidence. Less responsive than KIT mutations.",
            "notes": "May occur with or without KIT mutation."
        }
    ]

    mutations.extend(breast_mutations)
    mutations.extend(colorectal_mutations)
    mutations.extend(melanoma_mutations)

    with open(DATA_DIR / "mock_oncokb_mutations.json", "w") as f:
        json.dump(mutations, f, indent=2)

    print(f"Generated {len(mutations)} OncoKB mutations")
    return len(mutations)


def generate_expanded_pubmed():
    """Generate expanded PubMed articles."""

    with open(DATA_DIR / "mock_pubmed_articles.json") as f:
        articles = json.load(f)

    # Add breast cancer articles
    breast_articles = [
        {
            "pmid": "35320641",
            "title": "Trastuzumab Deruxtecan in HER2-Low Breast Cancer",
            "authors": "Modi S, Jacot W, Yamashita T, et al.",
            "journal": "New England Journal of Medicine",
            "year": 2022,
            "abstract": "DESTINY-Breast04 trial: Trastuzumab deruxtecan significantly improved PFS and OS compared with chemotherapy in HER2-low metastatic breast cancer. Median PFS 10.1 vs 5.4 months, median OS 23.9 vs 17.5 months. Established new treatment paradigm for HER2-low disease.",
            "key_finding": "T-DXd showed median PFS of 10.1 months vs 5.4 months in HER2-low metastatic breast cancer, defining a new targetable population",
            "biomarker": "HER2-low",
            "cancer_type": "Breast"
        },
        {
            "pmid": "34921995",
            "title": "Pembrolizumab in Early Triple-Negative Breast Cancer",
            "authors": "Schmid P, Cortes J, Dent R, et al.",
            "journal": "New England Journal of Medicine",
            "year": 2022,
            "abstract": "KEYNOTE-522 event-free survival analysis: Neoadjuvant pembrolizumab plus chemotherapy followed by adjuvant pembrolizumab significantly improved EFS compared with neoadjuvant chemotherapy alone. EFS HR 0.63, 3-year EFS 84.5% vs 76.8%.",
            "key_finding": "Neoadjuvant/adjuvant pembrolizumab improved 3-year EFS to 84.5% vs 76.8% in early TNBC",
            "biomarker": "TNBC",
            "cancer_type": "Breast"
        },
        {
            "pmid": "34619777",
            "title": "Olaparib in Early Breast Cancer with BRCA Mutation",
            "authors": "Tutt ANJ, Garber JE, Kaufman B, et al.",
            "journal": "New England Journal of Medicine",
            "year": 2021,
            "abstract": "OlympiA trial: Adjuvant olaparib significantly improved invasive disease-free survival in patients with germline BRCA1/2 mutations and HER2-negative high-risk early breast cancer. 3-year iDFS 85.9% vs 77.1%, HR 0.58.",
            "key_finding": "Adjuvant olaparib improved 3-year iDFS to 85.9% vs 77.1% in gBRCA1/2-mutated HER2-negative early breast cancer",
            "biomarker": "BRCA",
            "cancer_type": "Breast"
        },
        {
            "pmid": "33539533",
            "title": "Abemaciclib in High-Risk HR+ Early Breast Cancer",
            "authors": "Johnston SRD, Harbeck N, Hegg R, et al.",
            "journal": "Journal of Clinical Oncology",
            "year": 2020,
            "abstract": "monarchE trial: Adjuvant abemaciclib plus endocrine therapy improved iDFS in high-risk HR+/HER2- early breast cancer. 2-year iDFS 92.2% vs 88.7%, HR 0.75. Benefit seen across subgroups.",
            "key_finding": "Adjuvant abemaciclib improved 2-year iDFS to 92.2% vs 88.7% in high-risk HR+/HER2- early breast cancer",
            "biomarker": "HR+",
            "cancer_type": "Breast"
        }
    ]

    # Add colorectal cancer articles
    colorectal_articles = [
        {
            "pmid": "32955177",
            "title": "Pembrolizumab in MSI-H Metastatic Colorectal Cancer",
            "authors": "Andre T, Shiu KK, Kim TW, et al.",
            "journal": "New England Journal of Medicine",
            "year": 2020,
            "abstract": "KEYNOTE-177 trial: First-line pembrolizumab significantly improved PFS compared with chemotherapy in MSI-H/dMMR metastatic CRC. Median PFS 16.5 vs 8.2 months, HR 0.60. Established immunotherapy as standard first-line for MSI-H CRC.",
            "key_finding": "First-line pembrolizumab doubled PFS to 16.5 months vs 8.2 months in MSI-H metastatic CRC",
            "biomarker": "MSI-H",
            "cancer_type": "Colorectal"
        },
        {
            "pmid": "31566309",
            "title": "Encorafenib Plus Cetuximab in BRAF V600E CRC",
            "authors": "Kopetz S, Grothey A, Yaeger R, et al.",
            "journal": "New England Journal of Medicine",
            "year": 2019,
            "abstract": "BEACON trial: Encorafenib plus cetuximab (with or without binimetinib) significantly improved OS compared with standard therapy in BRAF V600E-mutated metastatic CRC. Median OS 9.0 vs 5.4 months.",
            "key_finding": "Encorafenib plus cetuximab improved median OS to 9.0 months vs 5.4 months in BRAF V600E mCRC",
            "biomarker": "BRAF_V600E",
            "cancer_type": "Colorectal"
        },
        {
            "pmid": "36264841",
            "title": "Sotorasib Plus Panitumumab in KRAS G12C CRC",
            "authors": "Fakih MG, Kopetz S, Kuboki Y, et al.",
            "journal": "New England Journal of Medicine",
            "year": 2023,
            "abstract": "CodeBreaK 300 trial: Sotorasib plus panitumumab significantly improved PFS compared with standard of care in previously treated KRAS G12C-mutated metastatic CRC. Median PFS 5.6 vs 2.2 months.",
            "key_finding": "Sotorasib plus panitumumab improved median PFS to 5.6 months in KRAS G12C mCRC - first targeted therapy for KRAS-mutated CRC",
            "biomarker": "KRAS_G12C",
            "cancer_type": "Colorectal"
        }
    ]

    # Add melanoma articles
    melanoma_articles = [
        {
            "pmid": "35139270",
            "title": "Relatlimab Plus Nivolumab in Untreated Advanced Melanoma",
            "authors": "Tawbi HA, Schadendorf D, Lipson EJ, et al.",
            "journal": "New England Journal of Medicine",
            "year": 2022,
            "abstract": "RELATIVITY-047 trial: Relatlimab plus nivolumab showed superior PFS compared with nivolumab alone in previously untreated advanced melanoma. Median PFS 10.1 vs 4.6 months, HR 0.75.",
            "key_finding": "Relatlimab + nivolumab (LAG-3 + PD-1) improved median PFS to 10.1 months vs 4.6 months in advanced melanoma",
            "biomarker": "LAG-3",
            "cancer_type": "Melanoma"
        },
        {
            "pmid": "34583430",
            "title": "Neoadjuvant Pembrolizumab in Resectable Stage III/IV Melanoma",
            "authors": "Patel SP, Othus M, Chen Y, et al.",
            "journal": "New England Journal of Medicine",
            "year": 2023,
            "abstract": "SWOG S1801 trial: Neoadjuvant plus adjuvant pembrolizumab significantly improved event-free survival compared with adjuvant pembrolizumab alone in resectable stage III/IV melanoma. 2-year EFS 72% vs 49%.",
            "key_finding": "Neoadjuvant pembrolizumab improved 2-year EFS to 72% vs 49% in resectable stage III/IV melanoma",
            "biomarker": "PD-1",
            "cancer_type": "Melanoma"
        },
        {
            "pmid": "28891408",
            "title": "Adjuvant Nivolumab vs Ipilimumab in Resected Stage III/IV Melanoma",
            "authors": "Weber J, Mandala M, Del Vecchio M, et al.",
            "journal": "New England Journal of Medicine",
            "year": 2017,
            "abstract": "CheckMate 238 trial: Adjuvant nivolumab significantly improved recurrence-free survival compared with ipilimumab in resected stage IIIB-IV melanoma. 12-month RFS 70.5% vs 60.8%.",
            "key_finding": "Adjuvant nivolumab improved 12-month RFS to 70.5% vs 60.8% compared with ipilimumab",
            "biomarker": "PD-1",
            "cancer_type": "Melanoma"
        }
    ]

    articles.extend(breast_articles)
    articles.extend(colorectal_articles)
    articles.extend(melanoma_articles)

    with open(DATA_DIR / "mock_pubmed_articles.json", "w") as f:
        json.dump(articles, f, indent=2)

    print(f"Generated {len(articles)} PubMed articles")
    return len(articles)


if __name__ == "__main__":
    print("Expanding medical data files...")

    guidelines = generate_expanded_guidelines()
    trials = generate_expanded_trials()
    mutations = generate_expanded_mutations()
    articles = generate_expanded_pubmed()

    total = guidelines + trials + mutations + articles
    print(f"\nTotal documents: {total}")
    print("Data expansion complete!")
