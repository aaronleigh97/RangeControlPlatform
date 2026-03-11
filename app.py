from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from range_control_platform.main import create_app

if __name__ == "__main__":
    app = create_app()
    app.run_server(debug=True)
