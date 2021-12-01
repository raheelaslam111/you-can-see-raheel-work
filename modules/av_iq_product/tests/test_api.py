import odoo.tests
from odoo import api, _
import unittest
import json
import logging
import requests
from odoo.exceptions import UserError, ValidationError

logger = logging.getLogger(__name__)


class TestAVIQProduct(odoo.tests.TransactionCase):
    ''' The goal of this method class is to test the AV IQ Product API to Fetch Products Details,
        Manufacturer Details and Category Details .
    '''

    def setUp(self):
        super(TestAVIQProduct, self).setUp()
        self.user_name=''
        self.password=''
        self.client_id=''
        self.myuid ='' 
        self.fetch_api_credientials()
        self.url = 'http://api-v2.av-iq.com:9100/software/v3.1/get/'
        self.headers = {'Content-Type': 'application/json'}
        self.type_mfr = 'MFR'
        self.auth = (str(self.user_name), str(self.password))
        self.dummy_category =0
        self.dummy_manufacturer=0
        self.type_cat='Tier1'


    def fetch_api_credientials(self):
        data_api =self.env.ref('av_iq_product.demo_api')
        self.user_name = data_api['user_name']
        self.password = data_api['password']
        self.client_id = data_api['clientid']
        self.myuid = data_api['uid']

    def test_01_test_api_auth(self):

        self.url = self.url + 'getmanufacturersjson'
        urlstring = str(self.url)+"?clientid="+str(self.client_id)+"&uid="+str(self.myuid)
        response = requests.request("GET", url=urlstring, headers=self.headers,auth=self.auth)
        if response.status_code != 200:
            logger.error("Unsuccessfull Request for Auth Status is Failed May be Connection is down/Not-Established while authentication.")
            raise ValidationError(
                _('Connection is down/Not-Established while authentication.'))
        elif response.status_code == 200:
            logger.info("Response 200 Status is Successfull Request")

    def test_api_fetch_category(self):
        self.url = self.url + 'getcategoriesjson'
        urlstring = str(self.url)+"?clientid=" + \
                        str(self.client_id)+"&uid="+str(self.myuid)
        response = requests.request(
            "GET", url=urlstring, headers=self.headers, auth=self.auth)
        if response.status_code != 200:
            logger.error("Unsuccessfull Request for Categories Status is Failed may be Connection is down/Not-Established while getting Categories.")
            raise ValidationError(
                _('Connection is down/Not-Established while getting Categories.'))
        elif response.status_code == 200:
            logger.info("Response 200 Status is Successfull Request")
            y = json.loads(response.text)
            self.dummy_category = y[1]['CATEGORY_ID']
            # print("dummy category ",self.dummy_category)
            # print("Data Fetch ",y)
            if y:
                for x in y:
                    values = {
                        'category_id': x['CATEGORY_ID'],
                        'category': x['CATEGORY_DISPLAY_NAME'],
                        'product_count': x['PRODUCTCOUNT'],
                        }
                    self.env['categories.lines'].create(values)
        else:
            logger.error(
                "Connection is down/Not-Established while getting Categories.")

    def test_api_fetch_manufacturer(self):
        self.url = self.url + 'getmanufacturersjson'
        urlstring = str(self.url)+"?clientid=" + \
                        str(self.client_id)+"&uid="+str(self.myuid)
        response = requests.request(
            "GET", url=urlstring, headers=self.headers, auth=self.auth)
        if response.status_code != 200:
                logger.error("Unsuccessfull Request For manufacturers Status is Failed,May be Connection is down/Not-Established while getting manufacturers.")
                raise ValidationError(
                    _('Connection is down/Not-Established while getting manufacturers.'))
        elif response.status_code == 200:
            logger.info("Response 200 Status is Successfull Request")
            y = json.loads(response.text)
            # print("manufacturer data ",y)
            self.dummy_manufacturer = y[1]['MANUFACTURER_ID']
            # print("dummy manufacturer ",self.dummy_manufacturer)
            if y:
                for x in y:
                    values = {
                        'manufacturer_id' : x['MANUFACTURER_ID'],
                        'manufacturer': x['MANUFACTURER'],
                        'product_count': x['PRODUCTCOUNT'],
                    }
                    manufacturers = self.env['manufacturer.lines'].create(values)
        else:
            logger.error("Connection is down/Not-Established while getting manufacturers.")

    def test_api_fetch_product_by_manufacturer(self):

        self.url = self.url + 'getproductsjson'
        urlstring = str(self.url)+"?clientid="+str(self.client_id)+"&uid="+str(self.myuid)+"&option="+str(self.type_mfr)+"&ID="+str(self.dummy_manufacturer)
        response = requests.request("GET", url=urlstring, headers=self.headers,auth=self.auth)
        if response.status_code != 200:
            logger.error("Unsuccessfull Request For Fetching Products By Category Status is Failed May be Connection is down/Not-Established while getting Products by Manufactures.")
            raise ValidationError(_("Connection is down/Not-Established while getting Categories."))

        elif response.status_code == 200:
            logger.info("Response 200 Status is Successfull")
            y = json.loads(response.text)
            # print("response products by Manufacturer ",y)
            if y:
                    
                for x in y:
                    values = {
                    'manufacturer_id' : x['MANUFACTURER_ID'],
                    'manufacturer': x['MANUFACTURER'],
                    'model_number': x['MODEL_NUMBER'],
                    'part_number': x['PART_NUMBER'],
                    'upc_number': x['UPC_NUMBER'],
                    'name': x['DISPLAY_NAME'],
                    'short_description': x['SHORT_DESCRIPTION'],
                    'image_url': x['IMAGE_SPOTLIGHT'],
                    't1cat': x['T1CAT'],
                    't2cat': x['T2CAT'],
                    't3cat': x['T3CAT'],
                    'model_number_clean': x['MODEL_NUMBER_CLEAN'],
                    'msrp': x['MSRP'],
                    'row': x['ROW'],
                    'product_id':x['PRODUCT_ID']
                }
                    self.env['product.lines'].create(values)
        else:
            logger.error('Connection is down/Not-Established while getting products.')
        

    def test_api_fetch_product_by_category(self):

        self.url = self.url + 'getproductsjson'

        urlstring = str(self.url)+"?clientid="+str(self.client_id)+"&uid="+str(self.myuid)+"&option="+str(self.type_cat)+"&ID="+str(self.dummy_category)
        response = requests.request("GET", url=urlstring, headers=self.headers,auth=self.auth)
        if response.status_code != 200:
            logger.error("Unsuccessfull Request Status For Fetching Products By Category  is Failed may be Connection is down/Not-Established while getting products by Category.")
            raise ValidationError(_("Connection is down/Not-Established while getting products by Category."))

        elif response.status_code == 200:
            logger.info("Response 200 Status is Successfull")
            y = json.loads(response.text)
            # print("response products BY CATEGORY",y)
            if y:
                for x in y:
                    values = {
                    'manufacturer_id' : x['MANUFACTURER_ID'],
                        'manufacturer': x['MANUFACTURER'],
                        'model_number': x['MODEL_NUMBER'],
                        'part_number': x['PART_NUMBER'],
                        'upc_number': x['UPC_NUMBER'],
                        'name': x['DISPLAY_NAME'],
                        'short_description': x['SHORT_DESCRIPTION'],
                        'image_url': x['IMAGE_SPOTLIGHT'],
                        't1cat': x['T1CAT'],
                        't2cat': x['T2CAT'],
                        't3cat': x['T3CAT'],
                        'model_number_clean': x['MODEL_NUMBER_CLEAN'],
                        'msrp': x['MSRP'],
                        'row': x['ROW'],
                        'product_id':x['PRODUCT_ID']
                    }
                    self.env['product.lines'].create(values)
        else:
            logger.error('Connection is down/Not-Established while getting products.')

