from pathlib import Path
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PROJECT_ROOT.parents[1]

lab_source = PROJECT_ROOT / "demo"
lab_destination = REPOSITORY_ROOT / "site" / "public" / "labs" / "ground-effect-vlm"
image_destination = REPOSITORY_ROOT / "site" / "public" / "images" / "projects" / "ground-effect-vlm"
document_destination = REPOSITORY_ROOT / "site" / "public" / "documents"

if lab_destination.exists():
    shutil.rmtree(lab_destination)
shutil.copytree(lab_source, lab_destination)
image_destination.mkdir(parents=True, exist_ok=True)
for name in ("ground-sweep.svg", "span-loading.svg", "verification.svg"):
    shutil.copy2(PROJECT_ROOT / "results" / name, image_destination / name)
document_destination.mkdir(parents=True, exist_ok=True)
shutil.copy2(PROJECT_ROOT / "report" / "technical-report.html", document_destination / "ground-effect-vlm-report.html")
shutil.copy2(PROJECT_ROOT / "report.css", document_destination / "ground-effect-vlm-report.css")
print("Published ground-effect explorer, figures, and report")
