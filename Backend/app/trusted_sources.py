import json
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Resolve path dynamically relative to the backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCES_FILE = os.path.join(BASE_DIR, "my data", "trusted_sources.json")

# Ensure directory exists
os.makedirs(os.path.dirname(SOURCES_FILE), exist_ok=True)

DEFAULT_SOURCES = [
    {
        "id": "src_icar",
        "name": "ICAR — Indian Council of Agricultural Research",
        "base_url": "icar.org.in/en",
        "trust_score": 1.0,
        "enabled": True,
        "description": "Apex body for coordinating, guiding, and managing research and education in agriculture in India."
    },
    {
        "id": "src_pjtsau",
        "name": "Professor Jayashankar Telangana State Agricultural University",
        "base_url": "pjtsau.edu.in",
        "trust_score": 0.95,
        "enabled": True,
        "description": "Leading agricultural university in Telangana."
    },
    {
        "id": "src_angrau",
        "name": "ANGRAU — Acharya N.G. Ranga Agricultural University",
        "base_url": "angrau.ac.in",
        "trust_score": 1.0,
        "enabled": True,
        "description": "Leading agricultural university in Andhra Pradesh."
    },
    {
        "id": "src_tnau",
        "name": "Tamil Nadu Agricultural University",
        "base_url": "tnau.ac.in",
        "trust_score": 0.95,
        "enabled": True,
        "description": "Leading agricultural university in Tamil Nadu."
    },
    {
        "id": "src_agricoop",
        "name": "Department of Agriculture & Cooperation",
        "base_url": "agricoop.nic.in",
        "trust_score": 0.9,
        "enabled": True,
        "description": "Government of India agriculture department."
    },
    {
        "id": "src_kvk",
        "name": "Krishi Vigyan Kendra Knowledge Network",
        "base_url": "kvk.icar.gov.in",
        "trust_score": 0.9,
        "enabled": True,
        "description": "Local agricultural extension network."
    },
    {
        "id": "src_icar_ijags",
        "name": "Indian Journal of Agricultural Sciences — ICAR",
        "base_url": "epubs.icar.org.in/index.php/IJAgS",
        "trust_score": 0.9,
        "enabled": True,
        "description": ""
    },
    {
        "id": "src_tnau_agritech",
        "name": "TNAU Agritech Portal",
        "base_url": "agritech.tnau.ac.in",
        "trust_score": 0.9,
        "enabled": True,
        "description": ""
    },
    {
        "id": "src_icar_niasm",
        "name": "ICAR-NIASM — National Institute of Abiotic Stress Management",
        "base_url": "niam.res.in",
        "trust_score": 0.9,
        "enabled": True,
        "description": ""
    },
    {
        "id": "src_icar_iimr",
        "name": "ICAR-IIMR — Indian Institute of Millets Research",
        "base_url": "millets.res.in",
        "trust_score": 0.9,
        "enabled": True,
        "description": ""
    },
    {
        "id": "src_imd",
        "name": "India Meteorological Department — IMD",
        "base_url": "mausam.imd.gov.in",
        "trust_score": 1.0,
        "enabled": True,
        "description": ""
    },
    {
        "id": "src_imdagrimet",
        "name": "IMD Agricultural Meteorology",
        "base_url": "imdagrimet.gov.in",
        "trust_score": 1.0,
        "enabled": True,
        "description": ""
    },
    {
        "id": "src_imd_adv",
        "name": "IMD Agrometeorological Advisory Services",
        "base_url": "mausam.imd.gov.in/responsive/agromet_adv_ser_state_current.php",
        "trust_score": 1.0,
        "enabled": True,
        "description": ""
    },
    {
        "id": "src_agmarknet",
        "name": "AGMARKNET",
        "base_url": "agmarknet.gov.in",
        "trust_score": 1.0,
        "enabled": True,
        "description": ""
    },
    {
        "id": "src_enam",
        "name": "e-NAM — National Agriculture Market",
        "base_url": "enam.gov.in",
        "trust_score": 1.0,
        "enabled": True,
        "description": ""
    },
    {
        "id": "src_ysrhu",
        "name": "Dr. Y.S.R. Horticultural University",
        "base_url": "drysrhu.ap.gov.in",
        "trust_score": 1.0,
        "enabled": True,
        "description": ""
    },
    {
        "id": "src_nhb",
        "name": "National Horticulture Board",
        "base_url": "nhb.gov.in",
        "trust_score": 0.9,
        "enabled": True,
        "description": ""
    },
    {
        "id": "src_apeda",
        "name": "APEDA — Agricultural and Processed Food Products Export Development Authority",
        "base_url": "apeda.gov.in",
        "trust_score": 0.8,
        "enabled": True,
        "description": ""
    },
    {
        "id": "src_sfac",
        "name": "SFAC — Small Farmers' Agribusiness Consortium",
        "base_url": "sfacindia.com",
        "trust_score": 0.8,
        "enabled": True,
        "description": ""
    },
    {
        "id": "src_ncdc",
        "name": "NCDC — National Cooperative Development Corporation",
        "base_url": "ncdc.in",
        "trust_score": 0.8,
        "enabled": True,
        "description": ""
    },
    {
        "id": "src_soilhealth",
        "name": "Soil Health Card Portal",
        "base_url": "soilhealth.dac.gov.in",
        "trust_score": 1.0,
        "enabled": True,
        "description": "soil health, NPK, fertilizer, micronutrients, soil amendments, crop-specific fertilizer recommendations, soil-test-based recommendations"
    },
    {
        "id": "src_icar_crop_science",
        "name": "ICAR Crop Science",
        "base_url": "icar.org.in/en/crop-science/crop-science",
        "trust_score": 1.0,
        "enabled": True,
        "description": "crop production, crop varieties, crop improvement, plant protection, crop research"
    },
    {
        "id": "src_icar_pubs",
        "name": "ICAR Publications",
        "base_url": "icar.org.in/en/all-publications",
        "trust_score": 1.0,
        "enabled": True,
        "description": "crop management, soil, fertilizer, integrated pest management, agricultural practices, farmer advisories"
    },
    {
        "id": "src_icar_institutes",
        "name": "ICAR Institutes",
        "base_url": "icar.org.in/en/institutes",
        "trust_score": 1.0,
        "enabled": True,
        "description": "crop research, agricultural research, official ICAR institutes, crop-specific research"
    },
    {
        "id": "src_icar_rice",
        "name": "ICAR Indian Institute of Rice Research",
        "base_url": "icar.org.in/en/institutes",
        "trust_score": 1.0,
        "enabled": True,
        "description": "rice, paddy, rice fertilizer, rice nutrient management, rice pests, rice diseases, rice production"
    },
    {
        "id": "src_icar_groundnut",
        "name": "ICAR Indian Institute of Groundnut Research",
        "base_url": "icar.org.in/en/institutes",
        "trust_score": 1.0,
        "enabled": True,
        "description": "groundnut, peanut, groundnut fertilizer, nutrient management, groundnut pests, groundnut diseases"
    },
    {
        "id": "src_icar_maize",
        "name": "ICAR Indian Institute of Maize Research",
        "base_url": "icar.org.in/en/institutes",
        "trust_score": 1.0,
        "enabled": True,
        "description": "maize, corn, maize fertilizer, nutrient management, maize pests, maize diseases"
    },
    {
        "id": "src_icar_pulses",
        "name": "ICAR Indian Institute of Pulses Research",
        "base_url": "icar.org.in/en/institutes",
        "trust_score": 1.0,
        "enabled": True,
        "description": "pulses, red gram, pigeon pea, chickpea, black gram, green gram, pulse fertilizer, nutrient management"
    },
    {
        "id": "src_icar_spices",
        "name": "ICAR Indian Institute of Spices Research",
        "base_url": "icar.org.in/en/institutes",
        "trust_score": 1.0,
        "enabled": True,
        "description": "chilli, spices, pepper, turmeric, spice crop production, fertilizer, pests, diseases"
    },
    {
        "id": "src_icar_vegetable",
        "name": "ICAR Indian Institute of Vegetable Research",
        "base_url": "icar.org.in/en/institutes",
        "trust_score": 1.0,
        "enabled": True,
        "description": "vegetables, tomato, chilli, brinjal, okra, vegetable fertilizer, nutrient management, pests, diseases"
    },
    {
        "id": "src_icar_horticultural",
        "name": "ICAR Indian Institute of Horticultural Research",
        "base_url": "icar.org.in/en/institutes",
        "trust_score": 1.0,
        "enabled": True,
        "description": "horticulture, fruits, vegetables, horticultural crops, fertilizer, nutrient management, pests, diseases"
    },
    {
        "id": "src_icar_oilseeds",
        "name": "ICAR Indian Institute of Oilseeds Research",
        "base_url": "icar.org.in/en/institutes",
        "trust_score": 1.0,
        "enabled": True,
        "description": "oilseeds, groundnut, sunflower, sesame, oilseed fertilizer, nutrient management, pests, diseases"
    },
    {
        "id": "src_icar_water",
        "name": "ICAR Indian Institute of Water Management",
        "base_url": "icar.org.in/en/institutes",
        "trust_score": 1.0,
        "enabled": True,
        "description": "irrigation, water management, crop water requirements, drought, agricultural water management"
    },
    {
        "id": "src_icar_crida",
        "name": "ICAR Central Research Institute for Dryland Agriculture",
        "base_url": "icar.org.in/en/institutes",
        "trust_score": 1.0,
        "enabled": True,
        "description": "dryland agriculture, rainfed farming, drought management, soil moisture, crop management, nutrient management"
    }
]

class TrustedSourcesManager:
    def __init__(self):
        self._sources = []
        self._load_sources()

    def _load_sources(self):
        if not os.path.exists(SOURCES_FILE):
            self._sources = DEFAULT_SOURCES
            self._save_sources()
        else:
            try:
                with open(SOURCES_FILE, "r", encoding="utf-8") as f:
                    self._sources = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load trusted sources: {e}")
                self._sources = DEFAULT_SOURCES

    def _save_sources(self):
        try:
            with open(SOURCES_FILE, "w", encoding="utf-8") as f:
                json.dump(self._sources, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save trusted sources: {e}")

    def get_all_sources(self) -> List[Dict[str, Any]]:
        return self._sources

    def get_enabled_domains(self) -> List[str]:
        return [src["base_url"] for src in self._sources if src.get("enabled", False)]

    def add_source(self, name: str, base_url: str, description: str = "") -> Dict[str, Any]:
        import uuid
        new_source = {
            "id": f"src_{uuid.uuid4().hex[:8]}",
            "name": name,
            "base_url": base_url.replace("https://", "").replace("http://", "").strip("/"),
            "trust_score": 0.8, # Default for user-added
            "enabled": True,
            "description": description
        }
        self._sources.append(new_source)
        self._save_sources()
        return new_source

    def update_source(self, source_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for src in self._sources:
            if src["id"] == source_id:
                for k, v in updates.items():
                    if k in ["name", "base_url", "trust_score", "enabled", "description"]:
                        src[k] = v
                self._save_sources()
                return src
        return None

    def delete_source(self, source_id: str) -> bool:
        initial_len = len(self._sources)
        self._sources = [src for src in self._sources if src["id"] != source_id]
        if len(self._sources) < initial_len:
            self._save_sources()
            return True
        return False

# Singleton instance
trusted_sources = TrustedSourcesManager()
