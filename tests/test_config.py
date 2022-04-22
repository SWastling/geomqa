import geomqa.config as config


def test_config():

    assert isinstance(config.MRTRIX_VERSIONS, list)
    assert isinstance(config.MRTRIX_VERSIONS[0], str)
    assert isinstance(config.NIFTYREG_VERSIONS, list)
    assert isinstance(config.NIFTYREG_VERSIONS[0], str)
    assert isinstance(config.DEFAULT_NIFTYREG, str)
