#!/usr/bin/env python3
"""Fail-closed binding of a *Cosign-verified* Fulcio cert to a GitHub run.

Call this only after `cosign verify-blob` validates the SAME bundle and blob
against exact certificate identity and OIDC issuer. This script does NOT
independently authenticate X.509 chains or transparency inclusion.
"""
import argparse
import base64
import binascii
import json
from pathlib import Path
import re
import sys

from cryptography import x509
from cryptography.x509.oid import ObjectIdentifier

RUN_INVOCATION_OID = ObjectIdentifier('1.3.6.1.4.1.57264.1.21')
REPO_RE = re.compile(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z')


def der_utf8_string(data):
    """Parse a single exact DER UTF8String (OID values are ASN.1 encoded)."""
    if len(data) < 2 or data[0] != 0x0C:
        raise ValueError('run invocation extension is not DER UTF8String')
    length = data[1]
    pos = 2
    if length & 0x80:
        n = length & 0x7F
        if not 1 <= n <= 4 or len(data) < pos + n:
            raise ValueError('invalid DER string length')
        size_bytes = data[pos:pos+n]
        if size_bytes[0] == 0:
            raise ValueError('noncanonical DER length')
        length = int.from_bytes(size_bytes, 'big')
        if length < 128:
            raise ValueError('noncanonical DER long length')
        pos += n
    if pos + length != len(data) or length == 0:
        raise ValueError('DER string length mismatch')
    return data[pos:].decode('utf-8', errors='strict')


def _certificate_der(bundle):
    vm = bundle.get('verificationMaterial')
    if not isinstance(vm, dict):
        raise ValueError('missing verification material')
    raw = vm.get('certificate', {}).get('rawBytes') if isinstance(vm.get('certificate'), dict) else None
    chain = vm.get('x509CertificateChain')
    if chain is not None:
        certs = chain.get('certificates') if isinstance(chain, dict) else None
        if not isinstance(certs, list) or not certs or not isinstance(certs[0], dict):
            raise ValueError('invalid x509 certificate chain')
        other = certs[0].get('rawBytes')
        if raw is not None and raw != other:
            raise ValueError('ambiguous certificates in bundle')
        raw = other
    if not isinstance(raw, str) or not raw:
        raise ValueError('missing signing certificate')
    try:
        return base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError('invalid signing certificate encoding') from exc


def verify(bundle: dict, repository: str, run_id: int, attempt: int):
    if not isinstance(repository, str) or not REPO_RE.fullmatch(repository):
        raise ValueError('invalid expected repository')
    if type(run_id) is not int or run_id < 1 or type(attempt) is not int or attempt < 1:
        raise ValueError('invalid expected run or attempt')
    cert = x509.load_der_x509_certificate(_certificate_der(bundle))
    try:
        ext = cert.extensions.get_extension_for_oid(RUN_INVOCATION_OID)
    except x509.ExtensionNotFound as exc:
        raise ValueError('missing Fulcio run invocation OID') from exc
    if not isinstance(ext.value, x509.UnrecognizedExtension):
        raise ValueError('unexpected run invocation extension type')
    actual = der_utf8_string(ext.value.value)
    expected = f'https://github.com/{repository}/actions/runs/{run_id}/attempts/{attempt}'
    if actual != expected:
        raise ValueError('signing certificate run invocation mismatch')
    return {'status': 'VERIFIED', 'run_invocation_uri': actual}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--repository', required=True)
    p.add_argument('--run-id', type=int, required=True)
    p.add_argument('--run-attempt', type=int, required=True)
    args = p.parse_args()
    try:
        data = json.loads(args.bundle.read_text(encoding='utf-8'))
        report = verify(data, args.repository, args.run_id, args.run_attempt)
    except (OSError, ValueError, json.JSONDecodeError, x509.InvalidVersion) as exc:
        print(json.dumps({'status':'BLOCKED','reason':str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
