import sqlite3
import os

import uuid
import tempfile
import shutil
import time
import traceback

from analysis.comparison_engine import compare_current_with_multiple_backups
from datetime import datetime, timezone
import re
from core.report_db import init_report_db
from dedup.wal_dedup import deduplicate_wal_messages
from recovery.page_carving import run_page_carving
from ingestion.live_db_ingestion import run_logical_ingestion

from recovery.fts_recovery import carve_deleted_from_fts
from recovery.wal_overlay_recovery import recover_wal_overlay_messages
from recovery.wal_overlay_recovery import recover_wal_overlay_messages
from recovery.wal_frame_carver import carve_wal_strings
from recovery.wal_frame_parser import recover_wal_frame_records

from core.report_utils import log_anomaly, get_table_columns
from recovery.wal_delta_recovery import carve_deleted_from_wal_delta
from core.chat_utils import (
    resolve_avatar_path,
    resolve_or_create_chat_for_recovered_message,
    extract_recovery_source_label,
)


from core.sqlite_utils import (
    get_db_connection,
    get_entropy,
)





def detect_rollback_journal(msgstore_path, report_conn):
    """
    Layer 7: Rollback Journal Detection.
    لا يقوم بالاستخراج الآن، فقط يتحقق هل msgstore.db-journal موجود أم لا.
    """
    try:
        journal_path = f"{msgstore_path}-journal"

        if not os.path.exists(journal_path):
            log_anomaly(
                report_conn,
                "L7_ROLLBACK_JOURNAL",
                f"msgstore.db-journal not found for {msgstore_path}"
            )
            return False

        size = os.path.getsize(journal_path)

        if size == 0:
            log_anomaly(
                report_conn,
                "L7_ROLLBACK_JOURNAL",
                f"msgstore.db-journal exists but empty: {journal_path}"
            )
            return False

        with open(journal_path, "rb") as f:
            header = f.read(32)

        log_anomaly(
            report_conn,
            "L7_ROLLBACK_JOURNAL_FOUND",
            f"path={journal_path} size={size} header={header.hex()}"
        )
        return True

    except Exception as e:
        log_anomaly(report_conn, "L7_ROLLBACK_JOURNAL_ERROR", str(e))
        return False

    








def run_forensic_pipeline(msgstore_path, wa_path, case_path, backup_db_paths=None, avatar_dirs=None):
    """
    Orchestrates a Streamed-to-Disk Forensic Pipeline using Shadow Copy Workspace.
    """
    print(f"[*] Initializing Forensic Pipeline: {repr(str(msgstore_path))}")

    avatar_dirs = avatar_dirs or []
    backup_db_paths = backup_db_paths or []
    current_db_path = msgstore_path
    
    report_conn = init_report_db(case_path)

    # Layer 7: Rollback Journal Detection
    detect_rollback_journal(msgstore_path, report_conn)
    report_conn.commit()

    run_id = uuid.uuid4().hex
    started_at = int(time.time())


    report_conn.execute(
        "INSERT OR IGNORE INTO analysis_runs (run_id, started_at, status, stage, progress) VALUES (?, ?, ?, ?, ?)",
        (run_id, started_at, 'running', 'ingestion', 0)
    )
    report_conn.commit()

    cancel_flag_path = os.path.join(case_path, ".cancel")

    try:
        # Shadow Copy Workspace: Bypass Windows locks by copying DBs to a volatile directory
        with tempfile.TemporaryDirectory() as temp_workspace:
            # 1. Copy Main DB
            temp_msg = os.path.join(temp_workspace, 'msgstore.db')
            shutil.copy2(msgstore_path, temp_msg)
            
            # 2. Copy WAL and SHM if they exist to ensure carving works on the shadow copy
            wal_path_source = f"{msgstore_path}-wal"
            temp_wal = f"{temp_msg}-wal"
            if os.path.exists(wal_path_source):
                shutil.copy2(wal_path_source, temp_wal)
                
            shm_path_source = f"{msgstore_path}-shm"
            temp_shm = f"{temp_msg}-shm"
            if os.path.exists(shm_path_source):
                shutil.copy2(shm_path_source, temp_shm)

            # 3. Copy wa.db
            temp_wa = None
            if wa_path and os.path.exists(wa_path):
                temp_wa = os.path.join(temp_workspace, 'wa.db')
                shutil.copy2(wa_path, temp_wa)

            # =========================================================================
            # 🚨 الخطوة الأولى والمصيرية: النحت الجنائي للـ WAL قبل أي اتصال بقاعدة البيانات
            # =========================================================================
            print("[*] Commencing Deep Forensic Carving (WAL Delta Analysis)...")
            carve_deleted_from_wal_delta(temp_msg, case_path, report_conn)


            if os.path.exists(temp_wal):

                # 🔴 خذ نسخة آمنة من WAL
                safe_wal = os.path.join(temp_workspace, "wal_safe.bin")
                shutil.copy2(temp_wal, safe_wal)

                print("[*] WAL Frame Smart Carving...")
                frame_count = carve_wal_strings(safe_wal, report_conn)
                print(f"[*] WAL Frame Smart Carving recovered {frame_count} messages.")

                print("[*] WAL Frame Record Parser...")
                record_count = recover_wal_frame_records(temp_msg, report_conn)
                print(f"[*] WAL Frame Parser recovered {record_count} structured messages.")

                print("[*] Analyzing WAL binary fragments...")
                with open(safe_wal, 'rb') as f:
                    data = f.read()
                    if get_entropy(data[:4096]) < 7.8:
                        decoded_text = data.decode('utf-8', errors='ignore')
                        pattern = re.compile(r'[\u0020-\u007E\u0600-\u06FF]{5,}')
                        matches = pattern.findall(decoded_text)

                        for i, m in enumerate(set(matches)):
                            if i % 100 == 0 and os.path.exists(cancel_flag_path):
                                ended_at = int(time.time())
                                report_conn.execute(
                                    "UPDATE analysis_runs SET ended_at=?, status=?, stage=?, error_summary=? WHERE run_id=?",
                                    (ended_at, 'cancelled', 'finalize', 'cancelled by user', run_id)
                                )
                                report_conn.commit()
                                print("[!] Analysis cancelled by user.")
                                return False

                            if 'sqlite_' not in m:
                                report_conn.execute(
                                    "INSERT OR IGNORE INTO wal_strings (text) VALUES (?)",
                                    (repr(m.strip()),)
                                )

                # ✅ overlay آخر خطوة
                print("[*] Running WAL Overlay Recovery (Temporary Checkpoint)...")
                overlay_count = recover_wal_overlay_messages(temp_msg, report_conn)
                print(f"[*] WAL Overlay recovered {overlay_count} messages.")

            else:
                print(f"[ ] No WAL file found in temp workspace: {temp_wal}")

            report_conn.commit()


            # =========================================================================
            # 2. Logical Ingestion (استخراج البيانات السليمة) - سيتسبب بتفريغ WAL الآن وهذا طبيعي
            # =========================================================================
            run_logical_ingestion(temp_msg, temp_wa, case_path, report_conn)

            report_conn.execute(
                "UPDATE analysis_runs SET stage=?, progress=? WHERE run_id=?",
                ('carving', 30, run_id)
            )
            report_conn.commit()

            report_conn.execute("UPDATE analysis_runs SET stage=?, progress=? WHERE run_id=?", ('carving', 30, run_id))
            report_conn.commit()


            # =========================================================================
            # 3. Forensic Carving Phase (FTS & Deep Page-Level)
            # =========================================================================
            print("[*] Commencing Forensic Carving (FTS Shadow Tables)...")
            carve_deleted_from_fts(temp_msg, report_conn)

            run_page_carving(temp_msg, case_path, report_conn, run_id, cancel_flag_path)

            # =========================================================================
            # 4. Backup Comparison Phase
            # =========================================================================
            print("[DEBUG] Entered backup comparison phase")
            if backup_db_paths:
                print(f"[*] Running backup comparison against {len(backup_db_paths)} backups...")
                recovered_messages = compare_current_with_multiple_backups(temp_msg, backup_db_paths)

                for msg in recovered_messages:
                    chat_id, resolved_chat_jid, created_new_chat = resolve_or_create_chat_for_recovered_message(report_conn, msg)

                    sender_type = 'me' if msg.get("key_from_me") == 1 else 'contact'
                    recovered_text = msg.get("data")
                    if not recovered_text:
                        recovered_text = "(Recovered Backup Artifact)"

                    recovered_timestamp = (msg.get("timestamp") // 1000) if msg.get("timestamp") else 0
                    recovery_source = extract_recovery_source_label(msg)
                    recovery_method = "backup_comparison"
                    recovered_at = datetime.now(timezone.utc).isoformat()
                    conf_score = 0.98

                    recovery_layer = 0
                    recovery_status = "RecoveredFromBackup"
                    evidence_explanation = (
                        "Recovered by historical backup comparison. "
                        "This artifact exists in an older backup and is absent or changed in the current database."
                    )
                    raw_location = f"backup_source={recovery_source}"

                    report_conn.execute(
                        """
                        INSERT OR IGNORE INTO messages (
                            chat_id, sender, text, timestamp, status,
                            is_deleted, is_recovered, is_deleted_recovered,
                            recovery_source, recovery_method, recovered_at,
                            media_path, mime_type, confidence,
                            recovery_layer, recovery_status, evidence_explanation, raw_location
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            chat_id, sender_type, recovered_text, recovered_timestamp, "recovered",
                            0, 1, 1,
                            recovery_source, recovery_method, recovered_at,
                            None, None, conf_score,
                            recovery_layer, recovery_status, evidence_explanation, raw_location
                        )
                    )

                report_conn.commit()
            else:
                print("[DEBUG] backup_db_paths is empty, skipping backup comparison")
            # =========================================================================
            # 🚨 5. Recalculate Chat Stats (يجب أن يكون خارج شرط الباك أب ليحسب رسائل WAL)
            # =========================================================================
            report_conn.execute("""
            UPDATE chats
            SET has_recovered_messages = 0,
                recovered_message_count = 0
            """)
            report_conn.execute("""
            UPDATE chats
            SET has_recovered_messages = 1,
                recovered_message_count = (
                    SELECT COUNT(*) FROM messages m 
                    WHERE m.chat_id = chats.id AND m.is_recovered = 1
                )
            WHERE id IN (
                SELECT DISTINCT chat_id FROM messages WHERE is_recovered = 1
            )
            """)
            report_conn.commit()
            print("[DEBUG] Chat recovery summary updated for all sources (WAL/FTS/Backup)")

        # Ensure any remaining batched anomalies are committed
        report_conn.commit()
        
        # Final Step: Deduplicate WAL messages to remove false positives
        deduplicate_wal_messages(report_conn)

        

        ended_at = int(time.time())
        report_conn.execute(
            "UPDATE analysis_runs SET ended_at=?, status=?, stage=?, progress=? WHERE run_id=?",
            (ended_at, 'completed', 'finalize', 100, run_id)
        )
        report_conn.commit()

        # OS-Level Protection (Applied AFTER pipeline)
        try:
            os.chmod(msgstore_path, 0o444)
            if wa_path and os.path.exists(wa_path): os.chmod(wa_path, 0o444)
        except: pass 

        print("[+] Streamed Forensic Pipeline Finalized.")
        
        # 🚨 إشارة النجاح للواجهة لمنع مشكلة (UI Freeze)
        print('{"ok": True}')
        return True

    except Exception as e:
        ended_at = int(time.time())
        try:
            report_conn.execute(
                "UPDATE analysis_runs SET ended_at=?, status=?, stage=?, error_summary=? WHERE run_id=?",
                (ended_at, 'failed', 'finalize', str(e), run_id)
            )
            report_conn.commit()
        except:
            pass
        print(f"[!] Pipeline Error: {e}")
        traceback.print_exc() # طباعة المسار الدقيق للخطأ
        raise
    finally:
        report_conn.close()