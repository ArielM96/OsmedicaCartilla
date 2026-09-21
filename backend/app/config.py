import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
RESEARCH_DIR = BASE_DIR / "research"
DATASET_PATH = RESEARCH_DIR / "cartilla.normalized.json"
SUMMARY_PATH = RESEARCH_DIR / "summary.json"
TIPOS_PRESTADOR_PATH = RESEARCH_DIR / "tipo_de_prestador.json"
TIPOS_GUARDIA_PATH = RESEARCH_DIR / "tipo_de_guardia.json"
ESPECIALIDADES_PATH = RESEARCH_DIR / "especialidades.json"
ESTUDIOS_PATH = RESEARCH_DIR / "estudios.json"
MAP_CACHE_PATH = Path(os.getenv("OSMEDICA_MAP_CACHE_PATH", "/var/lib/osmedica-cartilla/geocodes.json"))
