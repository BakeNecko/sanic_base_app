from app.utils import get_signature


def test_sign_func():
    transaction_id = "5eae174f-7cd0-472c-bd36-35660f00132b"
    user_id = 1
    account_id = 1
    amount = 100
    secret_key = "gfdmhghif38yrf9ew0jkf32"
    signature = "7b47e41efe564a062029da3367bde8844bea0fb049f894687cee5d57f2858bc8"
    sign_str = f'{account_id}{amount}{transaction_id}{user_id}{secret_key}'

    assert get_signature(sign_str) == signature
