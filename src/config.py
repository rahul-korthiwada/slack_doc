import os
import json
elimination_chars = [(" ",""),("-",""),("\\\\",""),('\\"','"'),('\"','"')]
MINIMUM_REMAINING_TIME_MS = 20000

MOBILE = "mobile"
EMAIL = "email"
CARD = "card"
PAN = "pan"
VPA = "vpa"
CVV = "cvv"
EXPIRY = "expiry"
UID = "uid"
EXPIRY_MONTH = "expiry_month"
EXPIRY_YEAR = "expiry_year"
ACCOUNT = "account_number"
GSTIN = "GSTIN"
ACCESS_TOKEN = "access_token"
REFRESH_TOKEN = "refresh_token"
PUBLIC_TOKEN = "public_token"
SECRET = "secret"
AUTHORIZATION_KEY = "authorization_key"

lambda_version = "22"

spanning_distance = 15
fpSpanningDistance = 10

possible_key_dict = dict()
possible_key_dict["email"]  = ["email","email_id","emailid","customer_email","customeremail"]
possible_key_dict["mobile"] = ["phone","mobile","phoneno","phone_no","mobile_no","customerphone","mobilenum","mobile_number","mobilenumber","contact"]
possible_key_dict["vpa"]    = ["vpa","merchant_vpa","paymentsource","upi_vpa","payervpa","payeevpa","payee_vpa"]
possible_key_dict["card"]   = ["card","cardnumber","card_number","cardnum","card_num","name_on_card","num","number"]
possible_key_dict["pan"]    = ["pan"]
possible_key_dict["cvv"]    = ["securitycode","cvv","cvm","security_code","cvv_number"]
possible_key_dict["uid"]    = ["aadhar","uid"]
possible_key_dict["expiry"] = ["expiry","cardexp"]
possible_key_dict["expiry_month"] = ["expiry_month","card_expirymonth","month","expirymonth", "card_exp_month", "exp_month", "cardexpmonth"]
possible_key_dict["expiry_year"] = ["expiry_year","card_expiryyear","year","expiryyear","expyear","card_exp_year","exp_year","cardexpyear"]
possible_key_dict["account_number"] = ["accrefnumber","accountnumber","account","accountnum"]
possible_key_dict["access_token"] = ["access_token","accesstoken"]
possible_key_dict["refresh_token"] = ["refresh_token","refreshtoken"]
possible_key_dict["public_token"] = ["public_token","publictoken"]
possible_key_dict["secret"] = ["razorpaywebhookssecret","secret"]
possible_key_dict["authorization_key"] = ["authorization"]

inverse_key_dict = dict()
inverse_key_dict["card"] = ["order_id"]
inverse_key_dict["mobile"] = ["order_id"]
inverse_key_dict["cvv"] = ["order_id"]
inverse_key_dict["vpa"] = ["order_id"]
inverse_key_dict["email"] = ["order_id"]

identity_objects = dict()

#add your new search object here
#mobile - tick
identity_objects[MOBILE] = dict()
identity_objects[MOBILE]["regex"] = "([+][9][1]|[9][1]|[0]|[0][9][1]|){0,1}([6-9]{1})([0-9]{9})"
identity_objects[MOBILE]["tag"] = MOBILE
identity_objects[MOBILE]["key_value_list"] = possible_key_dict[MOBILE]
identity_objects[MOBILE]["inverse_key_list"] = inverse_key_dict[MOBILE]


#email - tick
identity_objects[EMAIL] = dict()
# identity_objects[EMAIL]["regex"] = r"(\\*|>)[\"\'][A-Za-z0-9]+[\._]?[A-Za-z0-9]+[@]\w+[.]\w{2,4}(\\*|<)[\'\"]"
identity_objects[EMAIL]["regex"] = "[\w.]+[@][\w.]+[\w]" # something.someone@identity.email.something.com we dont need dashes
identity_objects[EMAIL]["tag"] = EMAIL
identity_objects[EMAIL]["key_value_list"] = possible_key_dict[EMAIL]
identity_objects[EMAIL]["inverse_key_list"] = inverse_key_dict[EMAIL]


#vpa - tick
identity_objects[VPA] = dict()
identity_objects[VPA]["regex"] = "[\w.]{3,256}@[\w]{3,64}"
identity_objects[VPA]["tag"] = VPA
identity_objects[VPA]["key_value_list"] = possible_key_dict[VPA]
identity_objects[VPA]["inverse_key_list"] = inverse_key_dict[VPA]


#PAN
identity_objects[PAN] = dict()
identity_objects[PAN]["regex"] = "[a-zA-Z]{5}[0-9]{4}[a-zA-Z]"
identity_objects[PAN]["tag"] = PAN
identity_objects[PAN]["key_value_list"] = possible_key_dict[PAN]
identity_objects[PAN]["inverse_key_list"] = inverse_key_dict[VPA]

#CVV - tick
identity_objects[CVV] = dict()
identity_objects[CVV]["regex"] = "\d{3-4}"
identity_objects[CVV]["tag"] = CVV
identity_objects[CVV]["key_value_list"] = possible_key_dict[CVV]
identity_objects[CVV]["inverse_key_list"] = inverse_key_dict[CVV]



#expiry
identity_objects[EXPIRY] = dict()
identity_objects[EXPIRY]["regex"] = "(0[1-9]|1[012])[\ /-]((\d{2})|(20[0-9][0-9]))"
identity_objects[EXPIRY]["tag"] = EXPIRY
identity_objects[EXPIRY]["key_value_list"] = possible_key_dict[EXPIRY]
identity_objects[EXPIRY]["inverse_key_list"] = inverse_key_dict[VPA]

#aadhar
identity_objects[UID] = dict()
identity_objects[UID]["regex"] = "((\\\*)(\"|\')|(>))\d{12}((<)|(\\\*)(\"|\'))"
identity_objects[UID]["tag"] = UID
identity_objects[UID]["key_value_list"] = possible_key_dict[UID]
identity_objects[UID]["inverse_key_list"] = inverse_key_dict[VPA]

#expiry month
identity_objects[EXPIRY_MONTH] = dict()
identity_objects[EXPIRY_MONTH]["regex"] = "((\\\*)(\"|\')|(>))(0[1-9]|1[012])((<)|(\\\*)(\"|\'))"
identity_objects[EXPIRY_MONTH]["tag"] = EXPIRY_MONTH
identity_objects[EXPIRY_MONTH]["key_value_list"] = possible_key_dict[EXPIRY_MONTH]
identity_objects[EXPIRY_MONTH]["inverse_key_list"] = inverse_key_dict[VPA]

#expiry year
identity_objects[EXPIRY_YEAR] = dict()
identity_objects[EXPIRY_YEAR]["regex"] = "((\\\*)(\"|\')|(>))((\d{2})|(20[0-9][0-9]))((<)|(\\\*)(\"|\'))"
identity_objects[EXPIRY_YEAR]["tag"] = EXPIRY_YEAR
identity_objects[EXPIRY_YEAR]["key_value_list"] = possible_key_dict[EXPIRY_YEAR]
identity_objects[EXPIRY_YEAR]["inverse_key_list"] = inverse_key_dict[VPA]

#card
identity_objects[CARD] = dict()
identity_objects[CARD]["regex"] = "\d{12,19}"
identity_objects[CARD]["tag"] = CARD
identity_objects[CARD]["key_value_list"] = possible_key_dict[CARD]
identity_objects[CARD]["inverse_key_list"] = inverse_key_dict[CARD]

#account number
identity_objects[ACCOUNT] = dict()
identity_objects[ACCOUNT]["regex"] = "\d{9,18}"
identity_objects[ACCOUNT]["tag"] = ACCOUNT
identity_objects[ACCOUNT]["key_value_list"] = possible_key_dict[ACCOUNT]
identity_objects[ACCOUNT]["inverse_key_list"] = inverse_key_dict[CARD]

#gstin number
identity_objects[GSTIN] = dict()
identity_objects[GSTIN]["regex"] = "((\\\*)(\"|\')|(>))[0-9]{2}[a-zA-Z]{5}[0-9]{4}[a-zA-Z][a-zA-Z0-9][zZ][a-zA-Z0-9]((<)|((\\\*)(\"|\')))"
identity_objects[GSTIN]["tag"] = ACCOUNT
identity_objects[GSTIN]["key_value_list"] = possible_key_dict[ACCOUNT]
identity_objects[GSTIN]["inverse_key_list"] = inverse_key_dict[CARD]


identity_objects[ACCESS_TOKEN] = dict()
identity_objects[ACCESS_TOKEN]["regex"] = "[A-Za-z0-9_=]+\.[A-Za-z0-9_=]+\.[A-Za-z0-9_=]+"
identity_objects[ACCESS_TOKEN]["tag"] = ACCESS_TOKEN
identity_objects[ACCESS_TOKEN]["key_value_list"] = possible_key_dict[ACCESS_TOKEN]
identity_objects[ACCESS_TOKEN]["inverse_key_list"] = inverse_key_dict[CARD]


identity_objects[REFRESH_TOKEN] = dict()
identity_objects[REFRESH_TOKEN]["regex"] = "[a-z0-9]+"
identity_objects[REFRESH_TOKEN]["tag"] = REFRESH_TOKEN
identity_objects[REFRESH_TOKEN]["key_value_list"] = possible_key_dict[REFRESH_TOKEN]
identity_objects[REFRESH_TOKEN]["inverse_key_list"] = inverse_key_dict[CARD]

identity_objects[PUBLIC_TOKEN] = dict()
identity_objects[PUBLIC_TOKEN]["regex"] = "[a-zA-Z0-9_]+"
identity_objects[PUBLIC_TOKEN]["tag"] = PUBLIC_TOKEN
identity_objects[PUBLIC_TOKEN]["key_value_list"] = possible_key_dict[PUBLIC_TOKEN]
identity_objects[PUBLIC_TOKEN]["inverse_key_list"] = inverse_key_dict[CARD]

identity_objects[SECRET] = dict()
identity_objects[SECRET]["regex"] = "[A-Z0-9]+"
identity_objects[SECRET]["tag"] = SECRET
identity_objects[SECRET]["key_value_list"] = possible_key_dict[SECRET]
identity_objects[SECRET]["inverse_key_list"] = inverse_key_dict[CARD]

identity_objects[AUTHORIZATION_KEY] = dict()
identity_objects[AUTHORIZATION_KEY]["regex"] = "Basic[\w=]+="
identity_objects[AUTHORIZATION_KEY]["tag"] = AUTHORIZATION_KEY
identity_objects[AUTHORIZATION_KEY]["key_value_list"] = possible_key_dict[AUTHORIZATION_KEY]
identity_objects[AUTHORIZATION_KEY]["inverse_key_list"] = inverse_key_dict[CARD]


product = dict()
product["euler"] = [EXPIRY_YEAR,EXPIRY_MONTH,MOBILE,EMAIL,CARD,PAN,VPA,CVV,UID,ACCESS_TOKEN,REFRESH_TOKEN,PUBLIC_TOKEN,SECRET,AUTHORIZATION_KEY]
product["morpheus"] = [EXPIRY_YEAR,EXPIRY_MONTH,MOBILE,EMAIL,CARD,PAN,VPA,CVV,UID]
product["sdk"] = [EXPIRY_YEAR,EXPIRY_MONTH,MOBILE,EMAIL,CARD,PAN,VPA,CVV,UID]
product["credit"] = [EXPIRY_YEAR,EXPIRY_MONTH,MOBILE,EMAIL,CARD,PAN,VPA,CVV,UID]
product["upi"] = [EXPIRY_YEAR,EXPIRY_MONTH,MOBILE,EMAIL,CARD,PAN,VPA,CVV,UID]


tags = [identity_objects[CARD]]

# f = open("config.json","r")
# config = f.read()
# config = json.load(config)
# elimination_chars = config["elimination_chars"]
# identity_objects = config["identity_objects"]
# spanning_distance = config["spanning_distance"]

# MINIMUM_REMAINING_TIME_MS = config["MINIMUM_TIME_REMAINING"]
# products = config["products"]
# for key in identity_objects:
#     identity_objects[key]["regex"] = identity_objects[key]["regex"].replace("\\","\\")
#     identity_objects[key]["key_value_list"] = products[config["stack"]][key]