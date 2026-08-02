import argparse
import json
import os
import sys
import threading
from pathlib import Path

from core.engine_output import print_json
from core.engine_verification import verify_case, verify_case_forensic
from ingestion.engine_ingest import execute_ingest
from ingestion.engine_zip_prepare import execute_zip_analysis
from core.engine_case_bundle import execute_export_case_bundle
from core.engine_analysis import execute_analysis


sys.path.append(os.path.dirname(os.path.abspath(__file__)))



def main():
    parser = argparse.ArgumentParser(description="WhatsApp Forensic Engine Standalone CLI")
    parser.add_argument("--msgstore", help="Path to the source msgstore.db file")
    parser.add_argument("--case-dir", help="Target directory for forensic artifacts and report.db")
    parser.add_argument("--wa", help="Optional path to the source wa.db file")
    parser.add_argument("--ipc", action="store_true", help="Enable JSON-RPC style IPC over stdin/stdout")
    
    args = parser.parse_args()
    
    if args.ipc:
        # IPC Mode Loop
        for line in sys.stdin:
            try:
                line = line.strip()
                if not line: continue
                data = json.loads(line)
                cmd = data.get("cmd")

                if cmd == "ingest_zip":
                    zip_p = data.get("zip")
                    threading.Thread(target=execute_ingest, args=(zip_p, True), daemon=True).start()

                elif cmd == "analyze_zip_from_source":
                    stored_zip = data.get("storedZip")
                    case_id = data.get("caseId")
                    provenance = data.get("provenance")
                    # Match old flow: backend/evidence_locker/<case_id>
                    locker_root = Path(__file__).parent / "evidence_locker"
                    cdir = locker_root / case_id
                    threading.Thread(target=execute_zip_analysis, args=(stored_zip, cdir, True, provenance), daemon=True).start()

                elif cmd == "analyze_prepared_databases":
                    databases = data.get("databases", [])
                    case_id = data.get("caseId")
                    provenance = data.get("provenance")
                    avatar_dirs = data.get("avatarDirectories", [])

                    if not databases:
                        print_json({"ok": False, "error": "No databases provided for analysis"})
                        continue

                    current_db = databases[0]
                    backup_db_paths = databases[1:]

                    wa_db = data.get("waDbPath")

                    locker_root = Path(__file__).parent / "evidence_locker"
                    cdir = locker_root / case_id

                    print_json({
                        "event": "debug",
                        "message": "analyze_prepared_databases routing",
                        "current_db": current_db,
                        "wa_db": wa_db,
                        "backup_count": len(backup_db_paths),
                        "backup_dbs": backup_db_paths
                    })

                    threading.Thread(
                        target=execute_analysis,
                        args=(current_db, wa_db, cdir, True, provenance, backup_db_paths, avatar_dirs),
                        daemon=True
                    ).start()

                elif cmd == "cancel":
                    cdir = data.get("caseDir")
                    if cdir:
                        cancel_file = Path(cdir) / ".cancel"
                        cancel_file.touch()
                        print_json({"ok": True, "cancelledRequested": True})
                    else:
                        print_json({"ok": False, "error": "caseDir required for cancel"})
                
                elif cmd == "verify":
                    cdir = data.get("caseDir")
                    if cdir:
                        print_json(verify_case(cdir))
                    else:
                        print_json({"ok": False, "error": "caseDir required for verify"})
                
                elif cmd == "verify_case":
                    cdir = data.get("caseDir")
                    if cdir:
                        print_json(verify_case_forensic(cdir))
                    else:
                        print_json({"ok": False, "error": "caseDir required for verify_case"})
                
                elif cmd == "export_case_bundle":
                    cdir = data.get("case_dir")
                    odir = data.get("out_dir")
                    if cdir and odir:
                        threading.Thread(target=execute_export_case_bundle, args=(cdir, odir), daemon=True).start()
                    else:
                        print_json({"ok": False, "error": "case_dir and out_dir required for export_case_bundle"})
                
                else:
                    print_json({"ok": False, "error": f"Unknown command: {cmd}"})
            except json.JSONDecodeError:
                print_json({"ok": False, "error": "Invalid JSON input"})
            except Exception as e:
                print_json({"ok": False, "error": str(e)})
    else:
        # Legacy CLI Mode
        if not args.msgstore or not args.case_dir:
            parser.error("--msgstore and --case-dir are required in non-IPC mode")
        
        success = execute_analysis(args.msgstore, args.wa, args.case_dir, False)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
