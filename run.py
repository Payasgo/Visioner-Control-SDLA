# run.py

import sys


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "web"

    if mode == "simulator":
        from app.main import start_app

        print("Running Visioner-Control-SDLA (Simulator Mode)")
        start_app(mode="simulator")

    elif mode == "web":
        from app import create_app

        app = create_app()
        print("Running Visioner-Control-SDLA (Web Dashboard)")
        # debug=False in production; use an env variable or config for this
        debug = "--debug" in sys.argv
        app.run(host="0.0.0.0", port=5000, debug=debug)

    else:
        print(f"Unknown mode '{mode}'. Use 'simulator' or 'web'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
