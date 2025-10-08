from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
from pathlib import Path

from .common.git import get_git_root

git_root = Path(get_git_root())

# === Configuration ===
common_name = "minio"
cert_path = git_root / "certs" / "minio" / "public.crt"
key_path = git_root / "certs" / "minio" / "private.key"

# === Generate private key ===
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# === Build certificate subject/issuer ===
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "CA"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "AB"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, "Localhost"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Main Line"),
    x509.NameAttribute(NameOID.COMMON_NAME, common_name),
])

# === Build certificate ===
cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.utcnow() - timedelta(days=1))
    .not_valid_after(datetime.utcnow() + timedelta(days=3650))  # 10 years
    .add_extension(
        x509.SubjectAlternativeName([x509.DNSName(common_name)]),
        critical=False,
    )
    .sign(key, hashes.SHA256())
)

# === Write key ===
with open(key_path, "wb") as f:
    f.write(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

# === Write certificate ===
with open(cert_path, "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print(f"✅ Generated:\n  - {cert_path}\n  - {key_path}")