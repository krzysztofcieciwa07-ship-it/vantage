import base64
import datetime
import json
from pathlib import Path
import sys

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID, ObjectIdentifier

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.verify_run_invocation import verify, der_utf8_string, RUN_INVOCATION_OID

REPO='krzysztofcieciwa07-ship-it/vantage'
URI=f'https://github.com/{REPO}/actions/runs/40968975127/attempts/1'


def make_bundle(uri=URI, oid=RUN_INVOCATION_OID):
    signer=ec.generate_private_key(ec.SECP256R1())
    name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'synthetic-fixture')])
    encoded=uri.encode('utf-8')
    encoded=(bytes([0x0c,len(encoded)]) + encoded if len(encoded) < 128
             else bytes([0x0c,0x81,len(encoded)]) + encoded)
    cert=(x509.CertificateBuilder()
          .subject_name(name).issuer_name(name).public_key(signer.public_key())
          .serial_number(x509.random_serial_number())
          .not_valid_before(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=1))
          .not_valid_after(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=1))
          .add_extension(x509.UnrecognizedExtension(oid,encoded),critical=False)
          .sign(signer,hashes.SHA256()))
    der=cert.public_bytes(serialization.Encoding.DER)
    return {'verificationMaterial':{'certificate':{'rawBytes':base64.b64encode(der).decode()}}}


def test_exact_fulcio_run_and_attempt_verified():
    r=verify(make_bundle(),REPO,40968975127,1)
    assert r == {'status':'VERIFIED','run_invocation_uri':URI}


def test_wrong_run_and_attempt_are_blocked():
    for number,attempt in ((40968975128,1),(40968975127,2)):
        with pytest.raises(ValueError,match='run invocation mismatch'):
            verify(make_bundle(),REPO,number,attempt)


def test_absent_or_mislabelled_certificate_extension_is_blocked():
    with pytest.raises(ValueError,match='missing Fulcio run invocation'):
        verify(make_bundle(oid=ObjectIdentifier('1.3.6.1.4.1.57264.1.22')),REPO,40968975127,1)
    with pytest.raises(ValueError,match='missing signing certificate'):
        verify({'verificationMaterial':{}},REPO,40968975127,1)


def test_invalid_run_identity_and_certificate_encoding_blocked():
    for rid,attempt in ((0,1),(40968975127,0),(True,1)):
        with pytest.raises(ValueError,match='invalid expected run or attempt'):
            verify(make_bundle(),REPO,rid,attempt)
    with pytest.raises(ValueError,match='invalid signing certificate encoding'):
        verify({'verificationMaterial':{'certificate':{'rawBytes':'not-base64!'}}},REPO,40968975127,1)
    with pytest.raises(ValueError,match='invalid expected repository'):
        verify(make_bundle(),'https://attacker.invalid',40968975127,1)


def test_der_utf8_string_rejects_truncation_noncanonical_and_extra_bytes():
    for data in (b'',b'garbage',b'\x0c\x03ab',b'\x0c\x81\x01a',b'\x0c\x01ab'):
        with pytest.raises(ValueError):
            der_utf8_string(data)
