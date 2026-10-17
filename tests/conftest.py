# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "rag"))


def pytest_collection_modifyitems(config, items):
    if os.getenv("RUN_INTEGRATION") == "1":
        return
    skip = pytest.mark.skip(reason="集成测试需 Doris/Ollama，RUN_INTEGRATION=1 时运行")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)
