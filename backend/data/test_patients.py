"""Comprehensive test patient data for Cancer Care Coordinator.

This module provides diverse test patients covering:
- NSCLC (with EGFR, ALK, KRAS, ROS1, BRAF mutations)
- Breast Cancer (HER2+, TNBC, HR+, BRCA-mutated)
- Colorectal Cancer (MSI-H, KRAS, BRAF)
- Melanoma (BRAF, NRAS, wild-type)
- Pancreatic Cancer (BRCA-mutated)

Each patient has realistic:
- Demographics
- Cancer details with staging
- Genomic profiles matching our OncoKB data
- Comorbidities
- Organ function assessments
- Current medications
- Clinical notes
"""

TEST_PATIENTS = [
    # ==========================================
    # NSCLC PATIENTS
    # ==========================================
    {
        "id": "TEST001",
        "first_name": "Michael",
        "last_name": "Chen",
        "date_of_birth": "1961-05-20",
        "sex": "Male",
        "email": "m.chen@testmail.com",
        "phone": "555-1001",
        "cancer_details": {
            "cancer_type": "NSCLC",
            "subtype": "Adenocarcinoma",
            "stage": "Stage IV",
            "tnm_staging": "T2N2M1a",
            "primary_site": "Right upper lobe",
            "tumor_size_cm": 3.5,
            "metastases": ["Pleural effusion", "Contralateral lung nodules"],
            "histology": "Adenocarcinoma, EGFR-mutant",
            "grade": "Grade 2",
            "diagnosis_date": "2024-01-15"
        },
        "comorbidities": [
            {
                "condition": "Type 2 Diabetes Mellitus",
                "severity": "moderate",
                "treatment_implications": ["Monitor glucose with steroids", "A1c 7.2%"]
            }
        ],
        "organ_function": [
            {"organ": "Kidney", "status": "normal", "key_values": {"gfr": 92, "creatinine": 0.9}, "notes": "Normal"},
            {"organ": "Liver", "status": "normal", "key_values": {"ast": 25, "alt": 30, "bilirubin": 0.7}, "notes": "Normal"},
            {"organ": "Heart", "status": "normal", "key_values": {"ef": 62}, "notes": "Normal"}
        ],
        "ecog_status": 1,
        "current_medications": ["Metformin 1000mg BID", "Lisinopril 10mg daily"],
        "allergies": [],
        "smoking_status": "never",
        "pack_years": 0,
        "genomic_report_id": "NGS-TEST001",
        "clinical_notes": [
            "63-year-old Asian male never-smoker with Stage IV NSCLC adenocarcinoma.",
            "NGS revealed EGFR exon 19 deletion (p.E746_A750del) at 35% VAF.",
            "PD-L1 TPS 10%. No other actionable mutations. Brain MRI negative.",
            "EXCELLENT candidate for osimertinib first-line therapy per NCCN guidelines.",
            "Discussion: Osimertinib 80mg daily - expected PFS ~18.9 months per FLAURA trial."
        ]
    },
    {
        "id": "TEST002",
        "first_name": "Sarah",
        "last_name": "Johnson",
        "date_of_birth": "1968-09-12",
        "sex": "Female",
        "email": "s.johnson@testmail.com",
        "phone": "555-1002",
        "cancer_details": {
            "cancer_type": "NSCLC",
            "subtype": "Adenocarcinoma",
            "stage": "Stage IV",
            "tnm_staging": "T3N2M1c",
            "primary_site": "Left lower lobe",
            "tumor_size_cm": 4.2,
            "metastases": ["Brain (3 lesions)", "Bone (spine, pelvis)"],
            "histology": "Adenocarcinoma, ALK-rearranged",
            "grade": "Grade 3",
            "diagnosis_date": "2024-02-01"
        },
        "comorbidities": [
            {
                "condition": "Hypothyroidism",
                "severity": "mild",
                "treatment_implications": ["Well-controlled on levothyroxine"]
            }
        ],
        "organ_function": [
            {"organ": "Kidney", "status": "normal", "key_values": {"gfr": 88, "creatinine": 0.8}, "notes": "Normal"},
            {"organ": "Liver", "status": "normal", "key_values": {"ast": 22, "alt": 26, "bilirubin": 0.5}, "notes": "Normal"},
            {"organ": "Brain", "status": "impaired", "key_values": {"mets": 3, "largest_cm": 1.2}, "notes": "3 brain mets, largest 1.2cm"}
        ],
        "ecog_status": 1,
        "current_medications": ["Levothyroxine 75mcg daily", "Dexamethasone 4mg BID (brain mets)"],
        "allergies": ["Iodine contrast"],
        "smoking_status": "never",
        "pack_years": 0,
        "genomic_report_id": "NGS-TEST002",
        "clinical_notes": [
            "56-year-old female never-smoker with metastatic ALK+ NSCLC including brain metastases.",
            "ALK rearrangement confirmed by FISH (EML4-ALK fusion).",
            "Brain mets symptomatic - on dexamethasone. Consider SRS vs systemic first.",
            "RECOMMEND: Alectinib or lorlatinib given excellent CNS penetration.",
            "Lorlatinib may be preferred given multiple brain mets - discuss with radiation oncology."
        ]
    },
    {
        "id": "TEST003",
        "first_name": "William",
        "last_name": "Martinez",
        "date_of_birth": "1955-03-28",
        "sex": "Male",
        "email": "w.martinez@testmail.com",
        "phone": "555-1003",
        "cancer_details": {
            "cancer_type": "NSCLC",
            "subtype": "Adenocarcinoma",
            "stage": "Stage IV",
            "tnm_staging": "T4N3M1b",
            "primary_site": "Right hilum",
            "tumor_size_cm": 5.5,
            "metastases": ["Liver", "Adrenal glands", "Bone"],
            "histology": "Adenocarcinoma, KRAS G12C mutant",
            "grade": "Grade 3",
            "diagnosis_date": "2024-01-20"
        },
        "comorbidities": [
            {
                "condition": "COPD",
                "severity": "moderate",
                "treatment_implications": ["FEV1 55%", "Monitor for respiratory decline"]
            },
            {
                "condition": "Hypertension",
                "severity": "mild",
                "treatment_implications": ["Well-controlled"]
            }
        ],
        "organ_function": [
            {"organ": "Lung", "status": "moderate_impairment", "key_values": {"fev1": 55, "dlco": 52}, "notes": "COPD"},
            {"organ": "Liver", "status": "mild_impairment", "key_values": {"ast": 45, "alt": 52, "bilirubin": 1.1}, "notes": "Liver mets, mild LFT elevation"},
            {"organ": "Kidney", "status": "normal", "key_values": {"gfr": 78, "creatinine": 1.1}, "notes": "Normal"}
        ],
        "ecog_status": 2,
        "current_medications": ["Tiotropium inhaler daily", "Amlodipine 5mg daily", "Albuterol PRN"],
        "allergies": ["Penicillin"],
        "smoking_status": "former",
        "pack_years": 40,
        "genomic_report_id": "NGS-TEST003",
        "clinical_notes": [
            "69-year-old male former heavy smoker with metastatic NSCLC.",
            "KRAS G12C mutation identified on NGS. PD-L1 TPS 60%.",
            "No other actionable mutations. High PD-L1 favors immunotherapy first-line.",
            "PLAN: Pembrolizumab + chemotherapy first-line (KEYNOTE-189 regimen).",
            "KRAS G12C inhibitors (sotorasib/adagrasib) available for second-line after IO/chemo."
        ]
    },

    # ==========================================
    # BREAST CANCER PATIENTS
    # ==========================================
    {
        "id": "TEST004",
        "first_name": "Jennifer",
        "last_name": "Williams",
        "date_of_birth": "1972-11-15",
        "sex": "Female",
        "email": "j.williams@testmail.com",
        "phone": "555-1004",
        "cancer_details": {
            "cancer_type": "Breast",
            "subtype": "HER2-positive",
            "stage": "Stage IV",
            "tnm_staging": "T2N1M1",
            "primary_site": "Right breast",
            "tumor_size_cm": 2.8,
            "metastases": ["Liver", "Bone (spine)"],
            "histology": "Invasive ductal carcinoma, HER2+ (IHC 3+)",
            "grade": "Grade 3",
            "diagnosis_date": "2024-01-25"
        },
        "comorbidities": [],
        "organ_function": [
            {"organ": "Kidney", "status": "normal", "key_values": {"gfr": 95, "creatinine": 0.7}, "notes": "Normal"},
            {"organ": "Liver", "status": "mild_impairment", "key_values": {"ast": 55, "alt": 62, "bilirubin": 0.9}, "notes": "Liver mets"},
            {"organ": "Heart", "status": "normal", "key_values": {"ef": 65}, "notes": "Baseline echo normal - important for HER2 therapy"}
        ],
        "ecog_status": 0,
        "current_medications": ["Calcium/Vitamin D supplement"],
        "allergies": [],
        "smoking_status": "never",
        "pack_years": 0,
        "genomic_report_id": "NGS-TEST004",
        "clinical_notes": [
            "52-year-old female with metastatic HER2-positive breast cancer.",
            "ER/PR negative (triple testing). HER2 IHC 3+, confirmed by FISH.",
            "Liver and bone metastases on staging CT and bone scan.",
            "RECOMMEND: CLEOPATRA regimen - Pertuzumab + Trastuzumab + Docetaxel.",
            "Baseline ECHO 65% - monitor q3 months on HER2 therapy. GCSF support for chemo."
        ]
    },
    {
        "id": "TEST005",
        "first_name": "Angela",
        "last_name": "Davis",
        "date_of_birth": "1965-06-30",
        "sex": "Female",
        "email": "a.davis@testmail.com",
        "phone": "555-1005",
        "cancer_details": {
            "cancer_type": "Breast",
            "subtype": "Triple-Negative",
            "stage": "Stage IIIA",
            "tnm_staging": "T2N2M0",
            "primary_site": "Left breast",
            "tumor_size_cm": 3.5,
            "metastases": ["Axillary lymph nodes (4 positive)"],
            "histology": "Invasive ductal carcinoma, triple-negative",
            "grade": "Grade 3",
            "diagnosis_date": "2024-02-10"
        },
        "comorbidities": [
            {
                "condition": "Obesity",
                "severity": "moderate",
                "treatment_implications": ["BMI 34", "Consider dose adjustments"]
            }
        ],
        "organ_function": [
            {"organ": "Kidney", "status": "normal", "key_values": {"gfr": 82, "creatinine": 0.9}, "notes": "Normal"},
            {"organ": "Liver", "status": "normal", "key_values": {"ast": 28, "alt": 32, "bilirubin": 0.6}, "notes": "Normal"},
            {"organ": "Heart", "status": "normal", "key_values": {"ef": 60}, "notes": "Normal"}
        ],
        "ecog_status": 0,
        "current_medications": ["Metformin 500mg BID (pre-diabetes)"],
        "allergies": ["Shellfish"],
        "smoking_status": "never",
        "pack_years": 0,
        "genomic_report_id": "NGS-TEST005",
        "clinical_notes": [
            "59-year-old female with locally advanced triple-negative breast cancer.",
            "ER/PR/HER2 all negative. PD-L1 CPS = 15 (positive).",
            "Germline BRCA testing: BRCA1 mutation detected (pathogenic).",
            "RECOMMEND: Neoadjuvant pembrolizumab + chemotherapy (KEYNOTE-522).",
            "Post-surgery: Continue adjuvant pembrolizumab. Consider olaparib given BRCA1+."
        ]
    },
    {
        "id": "TEST006",
        "first_name": "Patricia",
        "last_name": "Anderson",
        "date_of_birth": "1958-02-18",
        "sex": "Female",
        "email": "p.anderson@testmail.com",
        "phone": "555-1006",
        "cancer_details": {
            "cancer_type": "Breast",
            "subtype": "HR-positive/HER2-negative",
            "stage": "Stage IV",
            "tnm_staging": "T1N0M1",
            "primary_site": "Right breast",
            "tumor_size_cm": 1.5,
            "metastases": ["Bone (multiple sites)"],
            "histology": "Invasive lobular carcinoma, ER+/PR+/HER2-",
            "grade": "Grade 2",
            "diagnosis_date": "2024-01-05"
        },
        "comorbidities": [
            {
                "condition": "Osteoporosis",
                "severity": "mild",
                "treatment_implications": ["T-score -2.8", "Needs bone-directed therapy"]
            }
        ],
        "organ_function": [
            {"organ": "Kidney", "status": "normal", "key_values": {"gfr": 75, "creatinine": 1.0}, "notes": "Normal for age"},
            {"organ": "Liver", "status": "normal", "key_values": {"ast": 24, "alt": 28, "bilirubin": 0.5}, "notes": "Normal"},
            {"organ": "Bone", "status": "impaired", "key_values": {"alk_phos": 180}, "notes": "Elevated due to bone mets"}
        ],
        "ecog_status": 1,
        "current_medications": ["Alendronate 70mg weekly", "Calcium/Vitamin D"],
        "allergies": [],
        "smoking_status": "never",
        "pack_years": 0,
        "genomic_report_id": "NGS-TEST006",
        "clinical_notes": [
            "66-year-old postmenopausal female with metastatic HR+/HER2- breast cancer.",
            "Bone-only metastatic disease. PIK3CA H1047R mutation on tumor NGS.",
            "ESR1 wild-type on ctDNA (no prior endocrine therapy).",
            "RECOMMEND: CDK4/6 inhibitor (ribociclib/palbociclib) + aromatase inhibitor.",
            "Add denosumab for bone metastases. If progression, alpelisib given PIK3CA mutation."
        ]
    },

    # ==========================================
    # COLORECTAL CANCER PATIENTS
    # ==========================================
    {
        "id": "TEST007",
        "first_name": "David",
        "last_name": "Brown",
        "date_of_birth": "1960-08-25",
        "sex": "Male",
        "email": "d.brown@testmail.com",
        "phone": "555-1007",
        "cancer_details": {
            "cancer_type": "Colorectal",
            "subtype": "Adenocarcinoma",
            "stage": "Stage IV",
            "tnm_staging": "T3N1M1a",
            "primary_site": "Sigmoid colon",
            "tumor_size_cm": 4.0,
            "metastases": ["Liver (3 lesions, potentially resectable)"],
            "histology": "Adenocarcinoma, moderately differentiated",
            "grade": "Grade 2",
            "diagnosis_date": "2024-02-05"
        },
        "comorbidities": [
            {
                "condition": "Hyperlipidemia",
                "severity": "mild",
                "treatment_implications": ["On statin therapy"]
            }
        ],
        "organ_function": [
            {"organ": "Kidney", "status": "normal", "key_values": {"gfr": 85, "creatinine": 1.0}, "notes": "Normal"},
            {"organ": "Liver", "status": "mild_impairment", "key_values": {"ast": 48, "alt": 55, "bilirubin": 0.8}, "notes": "Liver mets but good synthetic function"},
            {"organ": "Heart", "status": "normal", "key_values": {"ef": 58}, "notes": "Normal"}
        ],
        "ecog_status": 0,
        "current_medications": ["Atorvastatin 40mg daily", "Aspirin 81mg daily"],
        "allergies": [],
        "smoking_status": "never",
        "pack_years": 0,
        "genomic_report_id": "NGS-TEST007",
        "clinical_notes": [
            "64-year-old male with metastatic colorectal cancer, oligometastatic to liver.",
            "Extended RAS testing: KRAS/NRAS wild-type. BRAF wild-type. HER2 negative.",
            "MSI stable (pMMR). Left-sided primary tumor.",
            "RECOMMEND: FOLFOX + cetuximab (RAS WT, left-sided) for conversion therapy.",
            "Goal: Downstage liver mets for potential curative-intent hepatectomy."
        ]
    },
    {
        "id": "TEST008",
        "first_name": "Lisa",
        "last_name": "Taylor",
        "date_of_birth": "1975-04-10",
        "sex": "Female",
        "email": "l.taylor@testmail.com",
        "phone": "555-1008",
        "cancer_details": {
            "cancer_type": "Colorectal",
            "subtype": "Adenocarcinoma",
            "stage": "Stage IV",
            "tnm_staging": "T4N2M1b",
            "primary_site": "Ascending colon",
            "tumor_size_cm": 6.0,
            "metastases": ["Peritoneal carcinomatosis", "Liver"],
            "histology": "Adenocarcinoma, poorly differentiated, MSI-H",
            "grade": "Grade 3",
            "diagnosis_date": "2024-01-30"
        },
        "comorbidities": [],
        "organ_function": [
            {"organ": "Kidney", "status": "normal", "key_values": {"gfr": 98, "creatinine": 0.7}, "notes": "Normal"},
            {"organ": "Liver", "status": "normal", "key_values": {"ast": 30, "alt": 35, "bilirubin": 0.6}, "notes": "Normal"},
            {"organ": "Heart", "status": "normal", "key_values": {"ef": 62}, "notes": "Normal"}
        ],
        "ecog_status": 1,
        "current_medications": [],
        "allergies": ["Codeine"],
        "smoking_status": "never",
        "pack_years": 0,
        "genomic_report_id": "NGS-TEST008",
        "clinical_notes": [
            "49-year-old female with metastatic colorectal cancer - RIGHT-SIDED primary.",
            "MSI-HIGH on IHC (loss of MLH1/PMS2). Germline testing: Lynch syndrome confirmed.",
            "Right-sided + MSI-H = EXCELLENT candidate for immunotherapy.",
            "RECOMMEND: First-line pembrolizumab monotherapy (KEYNOTE-177).",
            "Expected ORR ~45% with durable responses. Family genetic counseling initiated."
        ]
    },
    {
        "id": "TEST009",
        "first_name": "Richard",
        "last_name": "Moore",
        "date_of_birth": "1952-12-05",
        "sex": "Male",
        "email": "r.moore@testmail.com",
        "phone": "555-1009",
        "cancer_details": {
            "cancer_type": "Colorectal",
            "subtype": "Adenocarcinoma",
            "stage": "Stage IV",
            "tnm_staging": "T3N1M1b",
            "primary_site": "Cecum",
            "tumor_size_cm": 5.2,
            "metastases": ["Liver (bilobar)", "Lung nodules"],
            "histology": "Adenocarcinoma, BRAF V600E mutant",
            "grade": "Grade 3",
            "diagnosis_date": "2024-02-15"
        },
        "comorbidities": [
            {
                "condition": "Atrial fibrillation",
                "severity": "moderate",
                "treatment_implications": ["On anticoagulation", "Rate controlled"]
            }
        ],
        "organ_function": [
            {"organ": "Kidney", "status": "normal", "key_values": {"gfr": 72, "creatinine": 1.2}, "notes": "Normal for age"},
            {"organ": "Liver", "status": "mild_impairment", "key_values": {"ast": 42, "alt": 48, "bilirubin": 1.0}, "notes": "Liver mets"},
            {"organ": "Heart", "status": "mild_impairment", "key_values": {"ef": 52, "rhythm": "AFib"}, "notes": "AFib, rate controlled"}
        ],
        "ecog_status": 1,
        "current_medications": ["Apixaban 5mg BID", "Metoprolol 50mg BID"],
        "allergies": [],
        "smoking_status": "former",
        "pack_years": 20,
        "genomic_report_id": "NGS-TEST009",
        "clinical_notes": [
            "72-year-old male with metastatic CRC, RIGHT-sided, BRAF V600E mutant.",
            "BRAF V600E = poor prognosis marker. MSI stable.",
            "UGT1A1 *1/*28 heterozygous - standard irinotecan dosing acceptable.",
            "RECOMMEND: FOLFOXIRI + bevacizumab (intensive) OR encorafenib + cetuximab.",
            "Given age/AFib, consider encorafenib + cetuximab (BEACON regimen) - less toxic."
        ]
    },

    # ==========================================
    # MELANOMA PATIENTS
    # ==========================================
    {
        "id": "TEST010",
        "first_name": "Christopher",
        "last_name": "White",
        "date_of_birth": "1970-07-22",
        "sex": "Male",
        "email": "c.white@testmail.com",
        "phone": "555-1010",
        "cancer_details": {
            "cancer_type": "Melanoma",
            "subtype": "Cutaneous melanoma",
            "stage": "Stage IV",
            "tnm_staging": "T4bN3M1c",
            "primary_site": "Back",
            "tumor_size_cm": 3.0,
            "metastases": ["Lung", "Liver", "Brain (2 lesions)"],
            "histology": "Nodular melanoma, BRAF V600E mutant",
            "grade": "Breslow 4.5mm, ulcerated",
            "diagnosis_date": "2024-02-01"
        },
        "comorbidities": [],
        "organ_function": [
            {"organ": "Kidney", "status": "normal", "key_values": {"gfr": 95, "creatinine": 0.9}, "notes": "Normal"},
            {"organ": "Liver", "status": "mild_impairment", "key_values": {"ast": 52, "alt": 58, "bilirubin": 1.1}, "notes": "Liver mets"},
            {"organ": "Brain", "status": "impaired", "key_values": {"mets": 2, "largest_cm": 1.5}, "notes": "2 brain mets, asymptomatic"}
        ],
        "ecog_status": 0,
        "current_medications": [],
        "allergies": [],
        "smoking_status": "never",
        "pack_years": 0,
        "genomic_report_id": "NGS-TEST010",
        "clinical_notes": [
            "54-year-old male with metastatic melanoma including brain metastases.",
            "BRAF V600E mutation confirmed. LDH elevated (450 U/L).",
            "Asymptomatic brain mets - can consider systemic first vs SRS.",
            "OPTIONS: (1) Nivolumab + ipilimumab - 50% intracranial response rate",
            "         (2) Dabrafenib + trametinib - rapid response but durability concern",
            "RECOMMEND: Nivo/ipi given potential for durable response despite brain mets."
        ]
    },
    {
        "id": "TEST011",
        "first_name": "Michelle",
        "last_name": "Jackson",
        "date_of_birth": "1963-10-08",
        "sex": "Female",
        "email": "m.jackson@testmail.com",
        "phone": "555-1011",
        "cancer_details": {
            "cancer_type": "Melanoma",
            "subtype": "Acral melanoma",
            "stage": "Stage IIIC",
            "tnm_staging": "T4aN2bM0",
            "primary_site": "Right heel",
            "tumor_size_cm": 2.5,
            "metastases": ["In-transit metastases", "Regional lymph nodes"],
            "histology": "Acral lentiginous melanoma, NRAS Q61R mutant",
            "grade": "Breslow 3.2mm",
            "diagnosis_date": "2024-01-18"
        },
        "comorbidities": [
            {
                "condition": "Type 2 Diabetes",
                "severity": "moderate",
                "treatment_implications": ["A1c 7.8%", "Immunotherapy may cause autoimmune diabetes"]
            }
        ],
        "organ_function": [
            {"organ": "Kidney", "status": "normal", "key_values": {"gfr": 80, "creatinine": 0.9}, "notes": "Normal"},
            {"organ": "Liver", "status": "normal", "key_values": {"ast": 26, "alt": 30, "bilirubin": 0.6}, "notes": "Normal"},
            {"organ": "Heart", "status": "normal", "key_values": {"ef": 60}, "notes": "Normal"}
        ],
        "ecog_status": 1,
        "current_medications": ["Metformin 1000mg BID", "Sitagliptin 100mg daily"],
        "allergies": ["Sulfa drugs"],
        "smoking_status": "never",
        "pack_years": 0,
        "genomic_report_id": "NGS-TEST011",
        "clinical_notes": [
            "61-year-old female with locally advanced acral melanoma (heel).",
            "NRAS Q61R mutation - no targeted therapy available for NRAS.",
            "BRAF wild-type, KIT wild-type.",
            "RECOMMEND: Neoadjuvant pembrolizumab then surgery (SWOG S1801 approach).",
            "Monitor glucose closely - immunotherapy can cause autoimmune diabetes."
        ]
    },

    # ==========================================
    # PANCREATIC CANCER PATIENT
    # ==========================================
    {
        "id": "TEST012",
        "first_name": "Robert",
        "last_name": "Garcia",
        "date_of_birth": "1957-01-30",
        "sex": "Male",
        "email": "r.garcia@testmail.com",
        "phone": "555-1012",
        "cancer_details": {
            "cancer_type": "Pancreatic",
            "subtype": "Adenocarcinoma",
            "stage": "Stage IV",
            "tnm_staging": "T3N1M1",
            "primary_site": "Pancreatic body",
            "tumor_size_cm": 4.0,
            "metastases": ["Liver (multiple)", "Peritoneal implants"],
            "histology": "Pancreatic ductal adenocarcinoma",
            "grade": "Grade 2",
            "diagnosis_date": "2024-02-20"
        },
        "comorbidities": [
            {
                "condition": "New-onset diabetes",
                "severity": "moderate",
                "treatment_implications": ["Likely paraneoplastic", "May improve with treatment"]
            }
        ],
        "organ_function": [
            {"organ": "Kidney", "status": "normal", "key_values": {"gfr": 78, "creatinine": 1.1}, "notes": "Normal"},
            {"organ": "Liver", "status": "mild_impairment", "key_values": {"ast": 65, "alt": 72, "bilirubin": 1.5}, "notes": "Liver mets, mild cholestasis"},
            {"organ": "Pancreas", "status": "impaired", "key_values": {"lipase": 180, "glucose": 220}, "notes": "Exocrine and endocrine insufficiency"}
        ],
        "ecog_status": 1,
        "current_medications": ["Insulin glargine 20 units daily", "Pancreatic enzymes with meals"],
        "allergies": [],
        "smoking_status": "former",
        "pack_years": 25,
        "genomic_report_id": "NGS-TEST012",
        "clinical_notes": [
            "67-year-old male with metastatic pancreatic adenocarcinoma.",
            "Germline testing: BRCA2 pathogenic mutation detected.",
            "Tumor MSI stable. KRAS G12D mutation (not targetable).",
            "RECOMMEND: FOLFIRINOX (platinum-based given BRCA2) if PS allows.",
            "If stable/responding after 4 months, consider olaparib maintenance (POLO trial)."
        ]
    }
]


def get_test_patients():
    """Return the list of test patients."""
    return TEST_PATIENTS


def get_test_patient_by_id(patient_id: str):
    """Get a specific test patient by ID."""
    for patient in TEST_PATIENTS:
        if patient["id"] == patient_id:
            return patient
    return None
