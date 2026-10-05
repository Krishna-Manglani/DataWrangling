"""
Run the complete Data Wrangling project pipeline.

This orchestration script runs the existing project stages in dependency order
so that the latest monthly Airbnb data can be processed with one command.

Pipeline stages:
    1. process_listings.py
       - Finds and combines all monthly Christchurch Airbnb datasets.

    2. Deliverable3plots.py
       - Recreates the earlier Airbnb exploratory analyses and plots.

    3. clean_listing.py
       - Cleans the combined Airbnb dataset.

    4. clean_tenancy.py
       - Cleans the tenancy dataset used for comparison.

    5. get_area_codes.py
       - Adds Stats NZ SA2 area codes to the cleaned Airbnb data.
       - Reuses cached coordinate lookups where possible.

    6. analysis.py
       - Runs the final Airbnb and tenancy analyses and creates updated plots.

The pipeline stops immediately if any stage fails. This prevents later stages
from running with incomplete or invalid outputs.

Run from the repository root:
    python run_pipeline.py
"""

import subprocess
import sys
import time
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Always use the directory containing this file as the project root.
PROJECT_ROOT = Path(__file__).resolve().parent


# Scripts are listed in dependency/project progression order.
PIPELINE_STAGES = [
    ("Process monthly Airbnb data", "process_listings.py"),
    ("Create Deliverable 3 plots", "Deliverable3plots.py"),
    ("Clean Airbnb data", "clean_listing.py"),
    ("Clean tenancy data", "clean_tenancy.py"),
    ("Add SA2 area codes", "get_area_codes.py"),
    ("Run final analysis", "analysis.py"),
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def validate_pipeline_scripts():
    """
    Check that every required pipeline script exists before starting.

    This prevents the pipeline from completing several stages and then
    discovering that a later script is missing.
    """
    missing_scripts = []

    for _, script_name in PIPELINE_STAGES:
        script_path = PROJECT_ROOT / script_name

        if not script_path.exists():
            missing_scripts.append(script_name)

    if missing_scripts:
        raise FileNotFoundError(
            "The following required pipeline script(s) are missing:\n"
            + "\n".join(
                f"  - {script_name}"
                for script_name in missing_scripts
            )
        )


def run_stage(stage_number, total_stages, description, script_name):
    """
    Run one pipeline stage using the same Python interpreter that launched
    this orchestration script.

    subprocess.run(..., check=True) causes the orchestration to fail
    immediately if the child script exits with an error.
    """
    script_path = PROJECT_ROOT / script_name

    print()
    print("=" * 70)
    print(
        f"STAGE {stage_number}/{total_stages}: "
        f"{description}"
    )
    print(f"Script: {script_name}")
    print("=" * 70)

    start_time = time.perf_counter()

    subprocess.run(
        [
            sys.executable,
            str(script_path),
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )

    elapsed = time.perf_counter() - start_time

    print()
    print(
        f"Completed Stage {stage_number}/{total_stages}: "
        f"{description}"
    )
    print(f"Stage runtime: {elapsed:.1f} seconds")


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def main():
    """
    Run all project pipeline stages in dependency/project progression order.
    """
    print()
    print("=" * 70)
    print("DATA WRANGLING PIPELINE")
    print("=" * 70)
    print(f"Project root: {PROJECT_ROOT}")

    # Check all required scripts before running anything.
    validate_pipeline_scripts()

    total_stages = len(PIPELINE_STAGES)

    print(
        f"Required scripts found. "
        f"{total_stages} stages will run."
    )

    pipeline_start = time.perf_counter()

    try:
        for stage_number, (description, script_name) in enumerate(
            PIPELINE_STAGES,
            start=1,
        ):
            run_stage(
                stage_number,
                total_stages,
                description,
                script_name,
            )

    except subprocess.CalledProcessError as error:
        print()
        print("=" * 70)
        print("PIPELINE FAILED")
        print("=" * 70)
        print(
            "The pipeline stopped because one stage "
            "returned an error."
        )
        print(
            f"Failed command: "
            f"{' '.join(str(part) for part in error.cmd)}"
        )
        print(f"Exit code: {error.returncode}")
        print()
        print(
            "Fix the failed stage before running "
            "the pipeline again."
        )

        sys.exit(error.returncode)

    total_runtime = time.perf_counter() - pipeline_start

    print()
    print("=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(
        f"All {total_stages} stages completed successfully."
    )
    print(f"Total runtime: {total_runtime:.1f} seconds")
    print("Updated datasets and plots are ready.")


if __name__ == "__main__":
    main()