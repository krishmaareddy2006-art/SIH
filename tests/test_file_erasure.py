"""Unit Tests for Controlled Secure File & Folder Erasure Engine."""

import os
import stat
import tempfile
from pathlib import Path
import pytest

from app.core.exceptions import ForensicShieldException
from app.schemas.erasure import ErasureExecuteRequest
from app.services.file_erasure import (
    ConfirmationTokenManager,
    ControlledErasureService,
    PathSandboxGuard,
)


def test_path_traversal_rejection():
    with tempfile.TemporaryDirectory() as tmp_root, tempfile.TemporaryDirectory() as tmp_outside:
        outside_file = Path(tmp_outside) / "outside_secret.txt"
        outside_file.write_text("Confidential Data")

        # 1. Attempt targeting file outside approved root
        with pytest.raises(ForensicShieldException) as exc_info:
            PathSandboxGuard.validate_sandbox_target(str(outside_file), tmp_root)
        assert exc_info.value.code == "PATH_TRAVERSAL_BLOCKED"

        # 2. Attempt relative path traversal sequence
        traversal_path = Path(tmp_root) / "../outside_secret.txt"
        with pytest.raises(ForensicShieldException) as exc_info:
            PathSandboxGuard.validate_sandbox_target(str(traversal_path), tmp_root)
        assert exc_info.value.code == "PATH_TRAVERSAL_BLOCKED"


def test_dry_run_lists_items_without_deletion():
    with tempfile.TemporaryDirectory() as tmp_root:
        target_dir = Path(tmp_root) / "evidence_case_01"
        target_dir.mkdir()
        file1 = target_dir / "sample_log.log"
        file1.write_text("System log output line 1\nLine 2")

        service = ControlledErasureService()
        req = ErasureExecuteRequest(
            target_path=str(target_dir),
            approved_root=tmp_root,
            dry_run=True,
            reason="Routine evidence dry-run listing test",
        )

        report = service.execute_erasure(req)

        assert report.dry_run is True
        assert report.status == "SIMULATED"
        assert report.total_items >= 2  # 1 file + 1 dir
        assert all(item.status == "PLANNED" for item in report.items)

        # File and directory must still exist on disk!
        assert target_dir.exists()
        assert file1.exists()


def test_missing_or_invalid_confirmation_token_rejection():
    with tempfile.TemporaryDirectory() as tmp_root:
        target_dir = Path(tmp_root) / "target_dir"
        target_dir.mkdir()

        service = ControlledErasureService()
        req_missing_token = ErasureExecuteRequest(
            target_path=str(target_dir),
            approved_root=tmp_root,
            dry_run=False,
            confirmation_token=None,
            reason="Testing missing token",
        )

        with pytest.raises(ForensicShieldException) as exc_info:
            service.execute_erasure(req_missing_token, user_id="operator")
        assert exc_info.value.code == "INVALID_CONFIRMATION_TOKEN"

        req_wrong_token = ErasureExecuteRequest(
            target_path=str(target_dir),
            approved_root=tmp_root,
            dry_run=False,
            confirmation_token="CONFIRM:wrong_path:12345678",
            reason="Testing wrong token",
        )

        with pytest.raises(ForensicShieldException) as exc_info:
            service.execute_erasure(req_wrong_token, user_id="operator")
        assert exc_info.value.code == "INVALID_CONFIRMATION_TOKEN"


def test_logical_erasure_nested_folders_unicode_read_only_huge_file():
    with tempfile.TemporaryDirectory() as tmp_root:
        target_dir = Path(tmp_root) / "nested_evidence"
        sub_dir = target_dir / "sub1" / "sub2"
        sub_dir.mkdir(parents=True)

        # 1. Normal empty file
        empty_file = sub_dir / "empty.txt"
        empty_file.write_bytes(b"")

        # 2. Unicode named file
        unicode_file = sub_dir / "evidence_数据_测试.log"
        unicode_file.write_text("Unicode forensic payload test data", encoding="utf-8")

        # 3. Read-only write-protected file
        readonly_file = sub_dir / "protected.dat"
        readonly_file.write_bytes(b"Protected file content")
        os.chmod(readonly_file, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        # 4. Larger multi-chunk file (128 KB)
        huge_file = target_dir / "huge_payload.bin"
        huge_file.write_bytes(b"X" * (128 * 1024))

        # Generate confirmation token
        _, req_str = ConfirmationTokenManager.generate_token(str(target_dir), "operator")

        service = ControlledErasureService()
        req = ErasureExecuteRequest(
            target_path=str(target_dir),
            approved_root=tmp_root,
            dry_run=False,
            confirmation_token=req_str,
            overwrite_passes=1,
            reason="Authorized secure logical erasure test",
        )

        report = service.execute_erasure(req, user_id="operator")

        assert report.dry_run is False
        assert report.status == "COMPLETED"
        assert report.failed_items == 0
        assert report.erased_items == len(report.items)
        assert report.total_bytes_erased > 0

        # Verify target directory and all files were unlinked from disk!
        assert not target_dir.exists()


def test_symlink_non_following_behavior():
    with tempfile.TemporaryDirectory() as tmp_root, tempfile.TemporaryDirectory() as tmp_outside:
        # Create target file OUTSIDE sandbox
        outside_file = Path(tmp_outside) / "external_target.raw"
        outside_file.write_text("CRITICAL_EXTERNAL_DATA_DO_NOT_DELETE")

        # Create symlink INSIDE sandbox pointing to external file
        sandbox_dir = Path(tmp_root) / "evidence_dir"
        sandbox_dir.mkdir()
        symlink_path = sandbox_dir / "link_to_external.lnk"

        try:
            os.symlink(outside_file, symlink_path)
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks not supported on this environment.")

        _, req_str = ConfirmationTokenManager.generate_token(str(symlink_path), "operator")

        service = ControlledErasureService()
        req = ErasureExecuteRequest(
            target_path=str(symlink_path),
            approved_root=tmp_root,
            dry_run=False,
            confirmation_token=req_str,
            follow_symlinks=False,
            reason="Unlink symlink test",
        )

        report = service.execute_erasure(req, user_id="operator")

        assert report.status == "COMPLETED"
        assert not symlink_path.exists()  # Symlink inside sandbox deleted

        # CRITICAL TEST: External file OUTSIDE sandbox MUST remain untouched!
        assert outside_file.exists()
        assert outside_file.read_text() == "CRITICAL_EXTERNAL_DATA_DO_NOT_DELETE"


def test_cancellation_interruption():
    with tempfile.TemporaryDirectory() as tmp_root:
        target_dir = Path(tmp_root) / "cancel_test"
        target_dir.mkdir()

        file1 = target_dir / "file1.dat"
        file1.write_bytes(b"A" * 1000)

        _, req_str = ConfirmationTokenManager.generate_token(str(target_dir), "operator")

        service = ControlledErasureService()
        req = ErasureExecuteRequest(
            target_path=str(target_dir),
            approved_root=tmp_root,
            dry_run=False,
            confirmation_token=req_str,
            reason="Testing cancellation flag",
        )

        # Callback that immediately cancels execution
        is_cancelled = lambda: True

        report = service.execute_erasure(req, user_id="operator", check_cancelled=is_cancelled)

        assert report.skipped_items > 0


def test_erasure_api_endpoints(client, operator_headers):
    with tempfile.TemporaryDirectory() as tmp_root:
        target_dir = Path(tmp_root) / "api_target"
        target_dir.mkdir()

        # 1. Request token endpoint
        token_res = client.post(
            "/api/v1/erasure/token",
            json={"target_path": str(target_dir), "approved_root": tmp_root},
            headers=operator_headers,
        )
        assert token_res.status_code == 200
        token_data = token_res.json()
        assert "required_confirmation_string" in token_data

        req_str = token_data["required_confirmation_string"]

        # 2. Execute dry-run preview via endpoint
        execute_res = client.post(
            "/api/v1/erasure/execute",
            json={
                "target_path": str(target_dir),
                "approved_root": tmp_root,
                "confirmation_token": req_str,
                "dry_run": True,
                "reason": "Testing endpoint dry-run preview",
            },
            headers=operator_headers,
        )
        assert execute_res.status_code == 200
        report = execute_res.json()
        assert report["dry_run"] is True
        assert report["status"] == "SIMULATED"
