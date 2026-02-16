import pandas as pd
from services.outlier_detector import OutlierDetector
from const_utils.stats_constansts import ImageStatsKeys


def test_mark_outliers_empty_df():
    """Ensures the detector handles empty input gracefully."""
    df = pd.DataFrame()
    result = OutlierDetector.mark_outliers(df, ["some_col"])
    assert result.empty


def test_global_outlier_detection():
    """Tests if a global metric (like brightness) correctly identifies an outlier."""
    # 10 values, one is a massive spike (1000)
    data = {
        "class_name": ["a"] * 10,
        "im_brightness": [100.0, 102.0, 98.0, 101.0, 105.0, 95.0, 100.0, 103.0, 99.0, 1000.0]
    }
    df = pd.DataFrame(data)

    result = OutlierDetector.mark_outliers(df, ["im_brightness"])

    # The last element (1000) should be an outlier
    assert result["outlier_im_brightness"].iloc[9] == 1
    assert result["outlier_im_brightness"].iloc[0] == 0
    assert result["outlier_any"].iloc[9] == 1


def test_class_specific_outlier_detection():
    """
    Tests if an object metric is analyzed per class.
    A value of 500 might be normal for a 'cloud' but an outlier for a 'tank'.
    """
    data = {
        ImageStatsKeys.class_name: ["tank"] * 10 + ["cloud"] * 10,
        "object_area": [10, 11, 9, 10, 12, 8, 10, 11, 9, 100] +  # 100 is outlier for tank
                       [500, 510, 490, 500, 520, 480, 500, 510, 490, 500]  # 500 is normal for cloud
    }
    df = pd.DataFrame(data)

    result = OutlierDetector.mark_outliers(df, ["object_area"])

    # 100 should be marked as outlier for the tank class
    assert result.loc[9, "outlier_object_area"] == 1
    # 500 should NOT be an outlier for the cloud class, even though it's > 100
    assert result.loc[10, "outlier_object_area"] == 0


def test_outlier_any_aggregation():
    """Tests if outlier_any flag is set if at least one feature is an outlier."""
    data = {
        "class_name": ["a"] * 6,
        "col1": [1, 1, 100, 2, 0, 2 ],  # outlier at index 2
        "col2": [1, 1, 1, 1, 1, 1]  # normal
    }
    df = pd.DataFrame(data)
    result = OutlierDetector.mark_outliers(df, ["col1", "col2"])

    assert result.loc[2, "outlier_any"] == 1
    assert result.loc[0, "outlier_any"] == 0


def test_data_integrity_types():
    """Verifies that the output uses memory-efficient int8 types."""
    df = pd.DataFrame({"object_area": [1, 2, 3], "class_name": ["a", "a", "a"]})
    result = OutlierDetector.mark_outliers(df, ["object_area"])

    assert result["outlier_object_area"].dtype == "int8"
    assert result["outlier_any"].dtype == "int8"