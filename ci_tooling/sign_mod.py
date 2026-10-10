#!/usr/bin/env python3
"""Sign a built Mod application/helper without notarization or trust settings changes."""

import argparse
import plistlib
import subprocess
import tempfile
from pathlib import Path


CERTIFICATE = '19FD838A17B096F42774B90A438950EC8052A4A5'
APP_ID = 'com.dortania.opencore-legacy-patcher'
HELPER_ID = APP_ID + '.privileged-helper'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path)
    parser.add_argument('--helper', type=Path)
    parser.add_argument('--p12-file', type=Path, required=True)
    parser.add_argument('--p12-password-file', type=Path, required=True)
    parser.add_argument('--rcodesign', type=Path, required=True)
    parser.add_argument('--entitlements', type=Path)
    args = parser.parse_args()
    if not (args.app or args.helper):
        parser.error('Specify --app and/or --helper')
    files = [args.rcodesign, args.p12_file, args.p12_password_file]
    for path in (args.app, args.helper, args.entitlements, *files):
        if path and not path.exists():
            raise FileNotFoundError(path)
    if args.app:
        info = plistlib.loads((args.app / 'Contents/Info.plist').read_bytes())
        if info.get('CFBundleIdentifier') != APP_ID:
            raise ValueError('Unexpected application identifier')
    for path, identifier in ((args.helper, HELPER_ID), (args.app, APP_ID)):
        if not path:
            continue
        rule = f'certificate leaf = H"{CERTIFICATE}" and identifier "{identifier}"'
        with tempfile.TemporaryDirectory(prefix='oclp-sign-requirement-') as temporary:
            requirement = Path(temporary) / 'requirement.bin'
            subprocess.run(['csreq', '-r', '=certificate leaf = H"' + CERTIFICATE + '"', '-b', str(requirement)], check=True)
            command = [str(args.rcodesign.resolve()), 'sign', '-C', '/dev/null', '--timestamp-url', 'none',
                       '--binary-identifier', identifier, '--code-requirements-file', str(requirement),
                       '--code-signature-flags', 'runtime']
            if path == args.app:
                # rcodesign 0.29 does not inherit designated requirements into nested code.
                magic = {b'\xfe\xed\xfa\xce', b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xcf', b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca'}
                for nested in sorted(path.rglob('*')):
                    if nested.is_symlink():
                        continue
                    is_code = nested.is_dir() and nested.suffix in ('.framework', '.app', '.bundle')
                    if nested.is_file():
                        with nested.open('rb') as source:
                            is_code = source.read(4) in magic
                    if is_code:
                        command += ['--code-requirements-file', nested.relative_to(path).as_posix() + ':' + str(requirement)]
            # Decode the P12 explicitly so rcodesign receives the leaf first.
            openssl = ['openssl', 'pkcs12']
            if subprocess.check_output(['openssl', 'version'], text=True).startswith('OpenSSL 3.'):
                openssl.append('-legacy')
            for name, flags in [('key.pem', ['-nocerts', '-nodes']),
                                ('leaf.pem', ['-clcerts', '-nokeys']),
                                ('chain.pem', ['-cacerts', '-nokeys'])]:
                output = Path(temporary) / name
                subprocess.run([*openssl, '-in', str(args.p12_file),
                                '-passin', 'file:' + str(args.p12_password_file),
                                *flags, '-out', str(output)], check=True)
                output.chmod(0o600)
            fingerprint = subprocess.check_output(['openssl', 'x509', '-in',
                str(Path(temporary) / 'leaf.pem'), '-noout', '-fingerprint', '-sha1'], text=True)
            if fingerprint.strip().split('=')[1].replace(':', '') != CERTIFICATE:
                raise ValueError('Identity does not match the helper certificate pin')
            for name in ('key.pem', 'leaf.pem', 'chain.pem'):
                command += ['--pem-file', str(Path(temporary) / name)]
            if path == args.app and args.entitlements:
                command += ['--entitlements-xml-file', str(args.entitlements)]
            subprocess.run([*command, str(path)], check=True)
        subprocess.run(['codesign', '--verify', '--strict', '--deep', '--all-architectures',
                        '-R', '=' + rule, str(path)], check=True)
    print('Signed and verified with the pinned Mod application identity.')


if __name__ == '__main__':
    main()
