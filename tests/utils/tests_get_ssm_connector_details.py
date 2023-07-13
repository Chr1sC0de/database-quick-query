import os
import dbqq.utils
import pytest

ssm_name = os.getenv("DBQQ_SSM_NAME", None)
ssm_region = os.getenv("DBQQ_SSM_REGION", "ap-southeast-2")


@pytest.mark.skipif(
    condition=ssm_name is not None, reason="ssm_name must exists"
)
def test_get_ssm_connector_details():
    configuration = dbqq.utils.get_ssm_connector_details(ssm_name, ssm_region)
    assert configuration is not None, "could not get configuration"


@pytest.mark.skipif(
    condition=ssm_name is not None, reason="ssm_name must exists"
)
def test_get_ssm_using_get_connector_details():
    configuration = dbqq.utils.get_connector_details()
    assert configuration is not None, "could not get configuration"


if __name__ == "__main__":
    test_get_ssm_using_get_connector_details()
