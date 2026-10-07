"""The encryption key must never be replaced, and ciphertext must never be wrapped twice."""
import pytest
from cryptography.fernet import Fernet

from app.utils import crypto


@pytest.fixture
def env_file(tmp_path, monkeypatch):
    f = tmp_path / '.env'
    monkeypatch.setattr(crypto, '_find_env_file', lambda: f)
    monkeypatch.delenv('SERVERKIT_ENCRYPTION_KEY', raising=False)
    monkeypatch.setenv('FLASK_ENV', 'production')
    return f


def test_process_without_env_reuses_key_from_dotenv(env_file):
    key = Fernet.generate_key().decode()
    env_file.write_text(f'FOO=1\nSERVERKIT_ENCRYPTION_KEY={key}\n')
    assert crypto.get_encryption_key() == key.encode()
    assert key in env_file.read_text()


def test_dotenv_key_is_used_even_outside_production(env_file, monkeypatch):
    key = Fernet.generate_key().decode()
    env_file.write_text(f'SERVERKIT_ENCRYPTION_KEY={key}\n')
    monkeypatch.delenv('FLASK_ENV', raising=False)
    assert crypto.get_encryption_key() == key.encode()


def test_ensure_key_never_regenerates_when_dotenv_has_one(env_file, monkeypatch):
    old = Fernet.generate_key().decode()
    env_file.write_text(f'SERVERKIT_ENCRYPTION_KEY={old}\n')
    monkeypatch.setattr(crypto, 'generate_encryption_key', lambda: pytest.fail('must not generate a new key'))
    assert crypto.ensure_encryption_key() == old.encode()
    assert old in env_file.read_text()


def test_first_install_still_generates_and_persists(env_file):
    key = crypto.get_encryption_key()
    assert key.decode() in env_file.read_text()


def test_token_from_another_key_is_recognised_as_a_token(env_file, monkeypatch):
    other = Fernet(Fernet.generate_key()).encrypt(b'secret').decode()
    monkeypatch.setenv('SERVERKIT_ENCRYPTION_KEY', Fernet.generate_key().decode())
    assert crypto.looks_like_fernet_token(other) is True
    assert crypto.looks_like_fernet_token(crypto.encrypt_secret(other)) is True


def test_storage_save_does_not_wrap_an_unreadable_token_again(env_file, monkeypatch, tmp_path):
    from app.services.storage_provider_service import StorageProviderService as S
    monkeypatch.setenv('SERVERKIT_ENCRYPTION_KEY', Fernet.generate_key().decode())
    monkeypatch.setattr(S, 'CONFIG_FILE', str(tmp_path / 'storage.json'))
    foreign = Fernet(Fernet.generate_key()).encrypt(b'005realkeyid').decode()
    cfg = {'provider': 'b2', 'b2': {'key_id': foreign, 'application_key': foreign, 'bucket': 'b'}}
    assert S.save_config(cfg)['success']
    import json
    assert json.load(open(S.CONFIG_FILE))['b2']['key_id'] == foreign


def test_plain_secrets_are_not_mistaken_for_ciphertext(env_file, monkeypatch):
    monkeypatch.setenv('SERVERKIT_ENCRYPTION_KEY', Fernet.generate_key().decode())
    for plain in ('005abcdef0123456789abcdef', 'K005abcdefghijklmnopqrstuvwxyz1', 'hunter2'):
        assert crypto.is_encrypted(plain) is False
        assert crypto.looks_like_fernet_token(plain) is False
