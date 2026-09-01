from mcp_server.errors import ErrorCategory, classify_error


def test_classifies_quota_error():
    assert classify_error(Exception("RESOURCE_EXHAUSTED: quota exceeded")).category == ErrorCategory.QUOTA


def test_classifies_permission_error():
    assert classify_error(Exception("PERMISSION_DENIED: caller lacks aiplatform.user")).category == ErrorCategory.PERMISSION


def test_classifies_authentication_error():
    assert (
        classify_error(Exception("Could not find default credentials")).category
        == ErrorCategory.AUTHENTICATION
    )


def test_classifies_content_filtered_error():
    assert classify_error(Exception("blocked by responsible AI safety filters")).category == ErrorCategory.CONTENT_FILTERED


def test_classifies_billing_error():
    assert classify_error(Exception("This API method requires billing to be enabled")).category == ErrorCategory.BILLING


def test_classifies_model_unavailable_error():
    assert classify_error(Exception("model veo-9.0 not found")).category == ErrorCategory.MODEL_UNAVAILABLE


def test_classifies_timeout_error():
    assert classify_error(TimeoutError("deadline exceeded after 600s")).category == ErrorCategory.TIMEOUT


def test_unrecognized_error_is_unknown_not_miscategorized():
    result = classify_error(Exception("something completely unrelated happened"))
    assert result.category == ErrorCategory.UNKNOWN
    assert result.message == "something completely unrelated happened"
