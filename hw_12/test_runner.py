import os
import subprocess
import shutil
from JackCompiler import compile_path

REPO_URL = "https://github.com/Croash-1230/_co.git"
CLONE_DIR = "./_co_test_repo"
TARGET_DIR = os.path.join(CLONE_DIR, "11")

def run_tests():
    # 1. 下載 GitHub Repo
    if os.path.exists(CLONE_DIR):
        shutil.rmtree(CLONE_DIR)
    print(f"Cloning {REPO_URL}...")
    subprocess.run(["git", "clone", "--depth", "1", REPO_URL, CLONE_DIR], check=True)

    if not os.path.exists(TARGET_DIR):
        print(f"Error: Directory {TARGET_DIR} not found!")
        return

    # 2. 掃描並編譯 11 資料夾內的所有專案
    print("\n--- Starting Compilation ---")
    compile_path(TARGET_DIR)

    # 3. 驗證每個 .jack 檔案是否都成功產生非空的 .vm 檔案
    print("\n--- Verification Report ---")
    total_files = 0
    passed_files = 0

    for root, _, files in os.walk(TARGET_DIR):
        jack_files = [f for f in files if f.endswith('.jack')]
        if not jack_files:
            continue
        
        project_name = os.path.basename(root)
        print(f"\n[Project: {project_name}]")
        for jf in sorted(jack_files):
            total_files += 1
            vm_path = os.path.join(root, jf[:-5] + '.vm')
            if os.path.exists(vm_path) and os.path.getsize(vm_path) > 0:
                with open(vm_path, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f if line.strip()]
                print(f"  ✅ {jf} -> {jf[:-5]}.vm ({len(lines)} VM instructions)")
                passed_files += 1
            else:
                print(f"  ❌ {jf} -> Failed to generate valid .vm file")

    print(f"\nSummary: {passed_files}/{total_files} files compiled successfully.")

if __name__ == "__main__":
    run_tests()
