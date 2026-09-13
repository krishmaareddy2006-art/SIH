"""Storage Target Classification Engine and Method Recommender for ForensicShield.

Classifies block storage devices (HDD, SSD, NVMe, USB/Flash, Virtual Disk, Unknown)
and produces confidence-scored sanitization recommendations with FTL wear-leveling caveats.
"""

from typing import Any, Dict, List, Tuple


class StorageTargetClassifier:
    """Classifies block storage devices and recommends hardware-appropriate sanitization methods."""

    @staticmethod
    def classify_target(
        device_path: str,
        transport: str = "",
        is_rotational: bool = True,
        model: str = "",
        vendor: str = "",
    ) -> str:
        """
        Classifies target into: HDD, SSD, NVME, USB_FLASH, VIRTUAL_DISK, UNKNOWN.
        """
        path_lower = device_path.lower()
        transport_lower = transport.lower()
        model_lower = model.lower()
        vendor_lower = vendor.lower()

        # 1. Virtual Disk Detection
        if (
            path_lower.startswith("/dev/loop")
            or "qemu" in model_lower
            or "virtual" in model_lower
            or "vbox" in model_lower
            or "vmware" in model_lower
        ):
            return "VIRTUAL_DISK"

        # 2. NVMe Detection
        if transport_lower == "nvme" or "nvme" in path_lower or "nvme" in model_lower:
            return "NVME"

        # 3. USB / Flash Detection
        if (
            transport_lower == "usb"
            or "flash" in model_lower
            or "thumb" in model_lower
            or ("sandisk" in vendor_lower and "ultra" in model_lower)
        ):
            return "USB_FLASH"


        # 4. SATA SSD Detection (Non-rotational SATA/SCSI)
        if not is_rotational:
            return "SSD"

        # 5. Magnetic HDD Detection (Rotational SATA/SCSI/IDE)
        if is_rotational and transport_lower in ["sata", "scsi", "ide", "pci", "unknown", ""]:
            return "HDD"

        return "UNKNOWN"

    @staticmethod
    def get_recommendation(target_class: str) -> Dict[str, Any]:
        """Returns confidence-scored sanitization recommendation and technical caveats."""
        if target_class == "NVME":
            return {
                "recommended_method": "NVME_FORMAT_CRYPTO_ERASE",
                "confidence_level": "HIGH",
                "alternative_methods": ["NVME_SANITIZE_BLOCK_ERASE", "GENERIC_SINGLE_PASS_OVERWRITE"],
                "ftl_caveats": "NVMe solid-state drives utilize internal Flash Translation Layers (FTL). NVMe Format with Cryptographic Erase (Command Set 0x80) or NVMe Sanitize is required to purge over-provisioned NAND flash blocks. Software overwriting provides LOW confidence.",
            }

        elif target_class == "SSD":
            return {
                "recommended_method": "ATA_SECURE_ERASE",
                "confidence_level": "HIGH",
                "alternative_methods": ["ATA_SANITIZE_BLOCK_ERASE", "DOD_5220_22_M_3_PASS_OVERWRITE"],
                "ftl_caveats": "SATA SSDs use FTL wear-leveling and spare block pools. ATA Secure Erase (hdparm --security-erase) or ATA Sanitize is required to purge remitted NAND blocks. Software overwriting provides LOW confidence.",
            }

        elif target_class == "HDD":
            return {
                "recommended_method": "DOD_5220_22_M_3_PASS_OVERWRITE",
                "confidence_level": "HIGH",
                "alternative_methods": ["SINGLE_PASS_ZERO_OVERWRITE", "ATA_SECURE_ERASE"],
                "ftl_caveats": "Magnetic Hard Disk Drives (HDDs) have fixed physical LBA track mappings. Multi-pass software overwriting provides HIGH confidence for physical track sanitization.",
            }

        elif target_class == "USB_FLASH":
            return {
                "recommended_method": "USB_CONTROLLER_SANITIZE_OR_CRYPTO_ERASE",
                "confidence_level": "MEDIUM",
                "alternative_methods": ["SINGLE_PASS_ZERO_OVERWRITE"],
                "ftl_caveats": "USB flash drives lack standard ATA/NVMe passthrough interfaces. Software overwriting clears visible LBA blocks, but bad-block pools may retain latent data.",
            }

        elif target_class == "VIRTUAL_DISK":
            return {
                "recommended_method": "VIRTUAL_DISK_UNLINK_AND_HYPERVISOR_PURGE",
                "confidence_level": "HIGH",
                "alternative_methods": ["GUEST_OS_SINGLE_PASS_OVERWRITE"],
                "ftl_caveats": "Virtual disks reside on hypervisor host storage pools. Unlinking image files and issuing hypervisor trim commands is required.",
            }

        else:
            return {
                "recommended_method": "MANUAL_FORENSIC_ANALYST_REVIEW",
                "confidence_level": "LOW",
                "alternative_methods": ["SINGLE_PASS_ZERO_OVERWRITE"],
                "ftl_caveats": "Unidentified hardware storage controller capabilities. Manual physical inspection required before procedure authorization.",
            }
