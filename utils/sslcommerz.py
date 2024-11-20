from decimal import Decimal
import json
import os
from uuid import uuid4

import requests


class SSLCommerz:
    sslc_is_sandbox: bool
    sslc_store_id: str
    sslc_store_pass: str
    sslc_mode_name: str
    integration_data: dict[str, str] = {}

    def __init__(self, sslc_is_sandbox=True, sslc_store_id='', sslc_store_pass='') -> None:
        self.sslc_mode_name = self.set_sslcommerze_mode(sslc_is_sandbox)
        self.sslc_is_sandbox = sslc_is_sandbox
        self.sslc_store_id = sslc_store_id
        self.sslc_store_pass = sslc_store_pass
        self.sslc_session_api = 'https://' + self.sslc_mode_name + '.' + os.getenv("SSLCZ_SESSION_API", None)
        self.sslc_validation_api = 'https://' + self.sslc_mode_name + '.' + os.getenv("SSLCZ_VALIDATION_API", None)

    @staticmethod
    def set_sslcommerze_mode(sslc_is_sandbox: bool) -> str:
        if sslc_is_sandbox is True or sslc_is_sandbox == 1:
            return 'sandbox'
        else:
            return 'securepay'



class SSLCSession(SSLCommerz):
    def __init__(self, sslc_is_sandbox=True, sslc_store_id='', sslc_store_pass='') -> None:
        super().__init__(sslc_is_sandbox, sslc_store_id, sslc_store_pass)

    def set_urls(self, success_url: str, fail_url: str, cancel_url: str, ipn_url: str = '') -> None:
        self.integration_data['success_url'] = success_url
        self.integration_data['fail_url'] = fail_url
        self.integration_data['cancel_url'] = cancel_url
        self.integration_data['ipn_url'] = ipn_url
    
    def set_product_integration(self, total_amount: Decimal, currency: str, product_category: str, product_name: str, num_of_item: int, shipping_method: str, product_profile: str='None') -> None:
        self.integration_data['store_id'] = self.sslc_store_id
        self.integration_data['store_passwd'] = self.sslc_store_pass
        self.integration_data['tran_id'] = str(uuid4())
        self.integration_data['total_amount'] = total_amount
        self.integration_data['currency'] = currency
        self.integration_data['product_category'] = product_category
        self.integration_data['product_name'] = product_name
        self.integration_data['num_of_item'] = num_of_item
        self.integration_data['shipping_method'] = shipping_method
        self.integration_data['product_profile'] = product_profile

    def set_customer_info(self, name: str, email: str, address1: str, city: str, postcode: str, country: str, phone: str, address2: str='') -> None:
        self.integration_data['cus_name'] = name
        self.integration_data['cus_email'] = email
        self.integration_data['cus_add1'] = address1
        self.integration_data['cus_add2'] = address2
        self.integration_data['cus_city'] = city
        self.integration_data['cus_postcode'] = postcode
        self.integration_data['cus_country'] = country
        self.integration_data['cus_phone'] = phone

    def set_shipping_info(self, shipping_to: str, address: str, city: str, postcode: str, country: str) -> None:
        self.integration_data['ship_name'] = shipping_to
        self.integration_data['ship_add1'] = address
        self.integration_data['ship_city'] = city
        self.integration_data['ship_postcode'] = postcode
        self.integration_data['ship_country'] = country

    def set_additional_values(self, value_a: str = '', value_b: str = '', value_c: str = '', value_d: str = '') -> None:
        self.integration_data['value_a'] = value_a
        self.integration_data['value_b'] = value_b
        self.integration_data['value_c'] = value_c
        self.integration_data['value_d'] = value_d

    def init_payment(self):
        post_url = self.sslc_session_api
        post_data = self.integration_data
        response_sslc = requests.post(post_url, post_data)
        response_data: dict[str, str] = {}

        if response_sslc.status_code == 200:
            response_json = json.loads(response_sslc.text)
            if response_json['status'] == 'FAILED':
                response_data['status'] = response_json['status']
                response_data['failedreason'] = response_json['failedreason']
                return response_data
            response_data['status'] = response_json['status']
            response_data['sessionkey'] = response_json['sessionkey']
            response_data['GatewayPageURL'] = response_json['GatewayPageURL']
            return response_data
        else:
            response_json = json.loads(response_sslc.text)
            response_data['status'] = response_json['status']
            response_data['failedreason'] = response_json['failedreason']
            return response_data
        

class Validation(SSLCommerz):
    def __init__(self, sslc_is_sandbox=True, sslc_store_id='', sslc_store_pass='') -> None:
        super().__init__(sslc_is_sandbox, sslc_store_id, sslc_store_pass)

    def validate_transaction(self, validation_id):
        query_params: dict[str, str] = {}
        response_data: dict[str, str] = {}
        query_params['val_id'] = validation_id
        query_params['store_id'] = self.sslc_store_id
        query_params['store_passwd'] = self.sslc_store_pass
        query_params['format'] = 'json'

        validation_response = requests.get(
            self.sslc_validation_api,
            params=query_params
        )

        if validation_response.status_code == 200:
            validation_json = validation_response.json()
            if validation_json['status'] == 'VALIDATED':
                response_data['status'] = 'VALIDATED'
                response_data['data'] = validation_json
            else:
                response_data['status'] = validation_json['status']
                response_data['data'] = validation_json
        else:
            response_data['status'] = 'FAILED'
            response_data['data'] = 'Validation failed due to status code ' + str(validation_response.status_code)
        return response_data