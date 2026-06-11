import requests
from django.conf import settings


class ZibalService:
    """سرویس درگاه پرداخت زیبال"""

    BASE_URL = 'https://gateway.zibal.ir/v1'
    TOMAN_TO_RIAL = 10

    RESULT_MESSAGES = {
        100: 'موفق',
        102: 'مرچنت یافت نشد',
        103: 'مرچنت غیرفعال است',
        104: 'مرچنت نامعتبر است',
        201: 'قبلاً تایید شده است',
        202: 'سفارش پرداخت نشده یا ناموفق',
        203: 'trackId نامعتبر است',
    }

    def __init__(self):
        self.merchant = settings.ZIBAL_MERCHANT
        self.callback_url = settings.ZIBAL_CALLBACK_URL

    def request_payment(self, amount_toman, order_id, description='', mobile='', email=''):
        """ایجاد درخواست پرداخت و دریافت لینک"""
        payload = {
            'merchant': self.merchant,
            'amount': int(amount_toman) * self.TOMAN_TO_RIAL,
            'callbackUrl': self.callback_url,
            'orderId': str(order_id),
            'description': description,
        }
        if mobile:
            payload['mobile'] = mobile
        if email:
            payload['email'] = email

        try:
            resp = requests.post(
                f'{self.BASE_URL}/request',
                json=payload,
                timeout=30
            )
            data = resp.json()

            if data.get('result') == 100:
                track_id = str(data['trackId'])
                return {
                    'success': True,
                    'track_id': track_id,
                    'payment_url': f'https://gateway.zibal.ir/start/{track_id}',
                }
            return {
                'success': False,
                'error': self._msg(data.get('result')),
            }
        except requests.RequestException as exc:
            return {'success': False, 'error': f'خطا در ارتباط با درگاه: {exc}'}

    def verify_payment(self, track_id):
        """تایید پرداخت پس از بازگشت از درگاه"""
        payload = {
            'merchant': self.merchant,
            'trackId': int(track_id),
        }
        try:
            resp = requests.post(
                f'{self.BASE_URL}/verify',
                json=payload,
                timeout=30
            )
            data = resp.json()

            if data.get('result') == 100:
                return {
                    'success': True,
                    'amount_toman': data.get('amount', 0) // self.TOMAN_TO_RIAL,
                    'ref_number': data.get('refNumber', ''),
                    'card_number': data.get('cardNumber', ''),
                }
            return {
                'success': False,
                'error': self._msg(data.get('result')),
            }
        except requests.RequestException as exc:
            return {'success': False, 'error': f'خطا در تایید پرداخت: {exc}'}

    def _msg(self, code):
        return self.RESULT_MESSAGES.get(code, f'خطای ناشناخته (کد {code})')
