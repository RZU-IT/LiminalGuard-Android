import urllib.request

from .dns import validate_query, validate_reply

ENDPOINT = "https://dns.adguard-dns.com/dns-query"


class AdGuardDNS:
    def __call__(self, query):
        validate_query(query)
        request = urllib.request.Request(ENDPOINT, data=query, method="POST", headers={
            "Content-Type": "application/dns-message", "Accept": "application/dns-message",
            "User-Agent": "LiminalGuard-Android/0.1",
        })
        # Ignore proxy environment variables; keep certificate verification enabled.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=5) as result:
            if result.status != 200 or result.headers.get_content_type() != "application/dns-message":
                raise ValueError("Unexpected DNS-over-HTTPS response")
            reply = result.read(65536)
        return validate_reply(query, reply)
