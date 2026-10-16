"""Bootstrap must handle an absent parent without masking access failures."""

from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from cloudlayer.lab5_runtime import incumbent_score


def test_absent_endpoint_requires_explicit_bootstrap():
    ml = SimpleNamespace(online_endpoints=SimpleNamespace(list=lambda: []))
    assert incumbent_score(ml, None, {}, True) is None
    with pytest.raises(RuntimeError, match="explicit bootstrap"):
        incumbent_score(ml, None, {}, False)


def test_bootstrap_does_not_hide_workspace_permission_failure():
    denied = Mock(side_effect=PermissionError("denied"))
    ml = SimpleNamespace(online_endpoints=SimpleNamespace(list=denied))
    with pytest.raises(PermissionError):
        incumbent_score(ml, None, {}, True)
