import sys
import ssl
import requests

print("Python :", sys.version)
print("OpenSSL:", ssl.OPENSSL_VERSION)
print("Requests:", requests.__version__)