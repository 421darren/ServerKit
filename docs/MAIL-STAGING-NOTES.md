# Mail server on staging: manual hardening applied (Oct 2026)

The Email Server extension (serverkit-email 1.0.0) installs Postfix/Dovecot/OpenDKIM
but leaves these gaps. Applied by hand on staging; the installer should do them.

- Postfix `myhostname` = the mail hostname (default was the VPS provider hostname).
- Let's Encrypt cert for the mail hostname (certbot webroot /var/www/certbot, own nginx
  port-80 server block serving only /.well-known/acme-challenge/), used by Postfix
  (smtpd_tls_cert_file/key_file) and Dovecot (ssl_cert/ssl_key); deploy hook reloads both.
- Submission 587 (STARTTLS, SASL via dovecot, auth only) and smtps 465 enabled in master.cf; ufw allows both.
- `smtp_address_preference = ipv4` (Gmail rejects IPv6 senders without matching PTR/AAAA).
- DNS needed: A mail, MX, SPF `v=spf1 mx a ~all`, DKIM full key (default._domainkey),
  DMARC, and PTR (rDNS) for IPv4 (and IPv6 if used) set at the VPS provider.

Extension code fixes (this commit):
- dkim_service.py: DKIM public key was cut at the first quoted chunk of the .txt file.
- email_service.py: status now also returns `components` (the UI Overview reads it).

Known open: domain list does not refresh after adding a domain; SpamAssassin installed but not running.
