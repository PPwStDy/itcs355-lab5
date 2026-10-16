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


def test_zero_traffic_preflight_is_not_a_serving_incumbent():
    ep = SimpleNamespace(name="itcs355-lab5-staging", traffic={})
    ml = SimpleNamespace(online_endpoints=SimpleNamespace(list=lambda: [ep], get=lambda n: ep))
    assert incumbent_score(ml, None, {}, True) is None
    with pytest.raises(RuntimeError, match="explicit bootstrap"):
        incumbent_score(ml, None, {}, False)


def test_mixed_traffic_cannot_silently_compare_the_wrong_deployment():
    ep = SimpleNamespace(name="itcs355-lab5-staging", traffic={"blue": 50, "green": 50})
    ml = SimpleNamespace(online_endpoints=SimpleNamespace(list=lambda: [ep], get=lambda n: ep))
    with pytest.raises(RuntimeError, match="Mixed incumbent"):
        incumbent_score(ml, None, {}, True)


def test_active_incumbent_permission_error_is_never_bootstrapped_away():
    ep = SimpleNamespace(name="itcs355-lab5-staging", traffic={"green": 100})
    denied = Mock(side_effect=PermissionError("denied"))
    ml = SimpleNamespace(
        online_endpoints=SimpleNamespace(list=lambda: [ep], get=lambda n: ep),
        online_deployments=SimpleNamespace(get=denied),
    )
    with pytest.raises(PermissionError):
        incumbent_score(ml, None, {}, True)
    denied.assert_called_once_with(endpoint_name=ep.name, name="green")
