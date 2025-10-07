#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPMP Phase Messages Validation Test

This test verifies that all phase messages match the new requirements:
1. No "Phase X" labels in messages
2. Each phase has working and completed messages
3. Phase 4 shows correct processing message
4. Phase 5 has proper completion sequence
"""

import re
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class PhaseMessageValidator:
    """Validator for OPMP phase messages"""

    # Expected messages per phase
    EXPECTED_MESSAGES = {
        "phase1": {
            "working": "正在分析您的查詢...",
            "completed": "查詢分析完成"
        },
        "phase2": {
            "working": "正在檢索產品資料...",
            "completed": "檢索產品資料完成"
        },
        "phase3": {
            "working": "正在整理產品資訊...",
            "completed": "整理產品資訊完成"
        },
        "phase4": {
            "working": "正在進行資料輸出處理...",
            "completed": "✅ 回答生成完成"
        },
        "phase5": {
            "working": "正在完成最後修飾...",
            "intermediate": "工作完成。",
            "completed": "工作達成"
        }
    }

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_file(self, file_path: Path, phase_num: int) -> bool:
        """Validate messages in a phase file"""
        print(f"\n{'='*60}")
        print(f"Validating {file_path.name} (Phase {phase_num})")
        print(f"{'='*60}")

        content = file_path.read_text(encoding='utf-8')
        phase_key = f"phase{phase_num}"
        expected = self.EXPECTED_MESSAGES[phase_key]

        # Check for prohibited patterns in user-facing messages only
        # Look for "Phase X" in message strings, not in comments or class names
        message_pattern = r'"message":\s*"[^"]*[Pp]hase\s+\d+[^"]*"'
        if re.search(message_pattern, content):
            self.errors.append(f"{file_path.name}: Found 'Phase X' label in user message")

        # Check for working message
        working_msg = expected["working"]
        if working_msg not in content:
            self.errors.append(f"{file_path.name}: Missing working message: '{working_msg}'")
        else:
            print(f"✓ Found working message: '{working_msg}'")

        # Check for completed message
        completed_msg = expected["completed"]
        if completed_msg not in content:
            self.errors.append(f"{file_path.name}: Missing completed message: '{completed_msg}'")
        else:
            print(f"✓ Found completed message: '{completed_msg}'")

        # Special checks for Phase 5
        if phase_num == 5:
            intermediate_msg = expected["intermediate"]
            if intermediate_msg not in content:
                self.errors.append(f"{file_path.name}: Missing intermediate message: '{intermediate_msg}'")
            else:
                print(f"✓ Found intermediate message: '{intermediate_msg}'")

        return len(self.errors) == 0

    def validate_frontend(self) -> bool:
        """Validate frontend JavaScript files"""
        print(f"\n{'='*60}")
        print("Validating Frontend JavaScript Files")
        print(f"{'='*60}")

        print("\n[1/2] progressive_markdown_renderer.js")

        js_file = project_root / "static" / "js" / "progressive_markdown_renderer.js"
        if not js_file.exists():
            self.errors.append("Frontend JS file not found")
            return False

        content = js_file.read_text(encoding='utf-8')

        # Check for removed phase icon
        if re.search(r'phase-marker-icon', content):
            icon_usage = content.count('phase-marker-icon')
            if icon_usage > 1:  # Allow class name in comment or documentation
                self.warnings.append("Frontend: phase-marker-icon still referenced in multiple places")

        # Check for red checkmark implementation
        if 'complete-red' not in content:
            self.errors.append("Frontend: Missing 'complete-red' class implementation")
        else:
            print("✓ Found 'complete-red' completion state")

        if '工作達成' not in content:
            self.errors.append("Frontend: Missing '工作達成' completion text")
        else:
            print("✓ Found '工作達成' completion text")

        # Check that percentage is removed from user-visible text
        # Look for textContent with percentage, not internal attributes
        if re.search(r'textContent\s*=\s*.*\$\{progress\}%', content):
            self.warnings.append("Frontend: Percentage display still shown to user")
        else:
            print("✓ Percentage removed from progress bar text display")

        # Check mgfd_ai_fixed.js for initial thinking indicator
        mgfd_js_file = project_root / "static" / "js" / "mgfd_ai_fixed.js"
        if mgfd_js_file.exists():
            print("\n[2/2] mgfd_ai_fixed.js")
            mgfd_content = mgfd_js_file.read_text(encoding='utf-8')

            if "AI 正在思考中" in mgfd_content:
                self.errors.append("mgfd_ai_fixed.js: Still contains old 'AI 正在思考中' text")
            elif "正在進行資料輸出處理" in mgfd_content:
                print("✓ Found updated thinking indicator text")
            else:
                self.warnings.append("mgfd_ai_fixed.js: Cannot verify thinking indicator text")

        return len(self.errors) == 0

    def validate_css(self) -> bool:
        """Validate frontend CSS file"""
        print(f"\n{'='*60}")
        print("Validating Frontend: progressive_streaming.css")
        print(f"{'='*60}")

        css_file = project_root / "static" / "css" / "progressive_streaming.css"
        if not css_file.exists():
            self.errors.append("Frontend CSS file not found")
            return False

        content = css_file.read_text(encoding='utf-8')

        # Check for complete-red styles
        if '.progress-bar.complete-red' not in content:
            self.errors.append("CSS: Missing '.progress-bar.complete-red' styles")
        else:
            print("✓ Found '.progress-bar.complete-red' styles")

        # Check for red background
        if 'background: #f44336' not in content:
            self.errors.append("CSS: Missing red background color")
        else:
            print("✓ Found red background color (#f44336)")

        # Check for animation stop
        if 'animation: none' not in content:
            self.warnings.append("CSS: animation:none may not be present for completion state")
        else:
            print("✓ Found animation stop directive")

        # Verify phase-marker-icon is removed
        if '.phase-marker-icon' in content and 'flex:' in content.split('.phase-marker-icon')[1].split('}')[0]:
            self.errors.append("CSS: .phase-marker-icon styles should be removed")
        else:
            print("✓ Phase marker icon styles removed")

        return len(self.errors) == 0

    def run_all_validations(self) -> bool:
        """Run all validation tests"""
        print("\n" + "="*60)
        print("OPMP Phase Messages Validation Test")
        print("="*60)

        kernel_dir = project_root / "libs" / "opmp_services" / "opmp_kernel"

        # Validate all phase files
        for phase_num in range(1, 6):
            file_name = f"phase{phase_num}_*.py"
            phase_files = list(kernel_dir.glob(file_name))

            if not phase_files:
                self.errors.append(f"Phase {phase_num} file not found")
                continue

            self.validate_file(phase_files[0], phase_num)

        # Validate frontend files
        self.validate_frontend()
        self.validate_css()

        # Print results
        print(f"\n{'='*60}")
        print("Validation Results")
        print(f"{'='*60}")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")

        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
            return False
        else:
            print("\n✅ All validations passed!")
            return True


if __name__ == "__main__":
    validator = PhaseMessageValidator()
    success = validator.run_all_validations()
    sys.exit(0 if success else 1)
