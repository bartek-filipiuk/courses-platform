import pytest
from app.net_guard import assert_public_url


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", [
    "http://127.0.0.1/", "http://localhost/", "http://169.254.169.254/latest/meta-data/",
    "http://10.0.0.5/", "http://192.168.1.1/", "http://[::1]/", "file:///etc/passwd", "redis://redis:6379",
])
async def test_blocks_private_and_bad_scheme(bad):
    with pytest.raises(ValueError):
        await assert_public_url(bad)


@pytest.mark.asyncio
async def test_allows_public_https():
    await assert_public_url("https://example.com/health")  # resolves to public IP
