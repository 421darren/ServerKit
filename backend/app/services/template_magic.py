"""Template variable values: generated secrets and ports, magic tokens (SERVICE_PASSWORD_*, SERVICE_URL_*, ...) and ${VAR} substitution.

Mixed into TemplateService; callers keep using TemplateService."""
import re
import secrets
import string
from typing import Any, Dict


class TemplateMagicMixin:
    @classmethod
    def generate_value(cls, var_config: Dict, force_generate: bool = False) -> str:
        """Generate a value for a variable based on its configuration.

        Args:
            var_config: Variable configuration dict
            force_generate: If True, always generate new value even for ports
        """
        var_type = var_config.get('type', 'string')
        default = var_config.get('default', '')

        if var_type == 'password':
            length = var_config.get('length', 32)
            chars = string.ascii_letters + string.digits
            if var_config.get('special_chars', False):
                chars += '!@#$%^&*'
            return ''.join(secrets.choice(chars) for _ in range(length))

        elif var_type == 'port':
            # ALWAYS find an available port - never trust defaults
            start_port = int(default) if default else 8000
            # A global base-port setting (Settings > managed_app_base_port)
            # overrides the per-template default when configured (non-zero).
            base = cls._managed_app_base_port()
            if base:
                start_port = base
            return str(cls._claim_port(start_port))

        elif var_type == 'uuid':
            import uuid
            return str(uuid.uuid4())

        elif var_type == 'random':
            length = var_config.get('length', 16)
            return secrets.token_hex(length // 2)

        return str(default)

    @classmethod
    def _classify_magic_token(cls, token: str):
        """Return ``(kind, name)`` for a bare magic token (no ``${}``), or
        ``(None, None)`` if it is not a recognized magic variable."""
        if token in cls.MAGIC_EXACT_TOKENS:
            return cls.MAGIC_EXACT_TOKENS[token], ''
        for prefix, kind in cls.MAGIC_PREFIXES:
            if token.startswith(prefix):
                return kind, token[len(prefix):]
        return None, None

    @classmethod
    def _generate_magic_password(cls) -> str:
        """Strong password for a SERVICE_PASSWORD_* token (alnum, no special
        chars to stay shell/compose-safe). Reuses the same primitive as
        ``generate_value(type=password)``."""
        chars = string.ascii_letters + string.digits
        return ''.join(secrets.choice(chars) for _ in range(cls.MAGIC_PASSWORD_LENGTH))

    @classmethod
    def _generate_magic_user(cls, name: str) -> str:
        """Service username for a SERVICE_USER_* token: ``svc_<name>_<rand>``,
        lowercased and reduced to ``[a-z0-9_]`` so it is safe as a DB/app user."""
        base = re.sub(r'[^a-z0-9]+', '_', (name or 'service').lower()).strip('_') or 'service'
        suffix = secrets.token_hex(2)  # 4 hex chars, keeps it short but unique
        return f'svc_{base}_{suffix}'

    @classmethod
    def _resolve_magic_value(cls, kind: str, name: str, context: Dict) -> str:
        """Resolve a single magic token to a value.

        ``context`` may carry ``fqdn`` / ``scheme`` (and ``app_name``); when an
        FQDN is not known yet the FQDN/URL forms degrade to a documented
        placeholder (``localhost``) that the install finalizer can later fill —
        this keeps resolution best-effort and non-fatal.
        """
        context = context or {}
        if kind == 'password':
            return cls._generate_magic_password()
        if kind == 'user':
            return cls._generate_magic_user(name)
        if kind == 'base64':
            import base64
            secret = secrets.token_bytes(24)
            return base64.b64encode(secret).decode('ascii')
        if kind == 'fqdn':
            return str(context.get('fqdn') or context.get('app_name') or 'localhost')
        if kind == 'url':
            scheme = str(context.get('scheme') or 'http')
            host = context.get('fqdn') or context.get('app_name') or 'localhost'
            return f'{scheme}://{host}'
        if kind == 'metrics_token':
            from app.services import metrics_token_service
            return metrics_token_service.get_or_create()
        if kind == 'server_public_ip':
            ip = context.get('server_public_ip')
            if not ip:
                try:
                    from app.services.site_domain_service import SiteDomainService
                    ip = SiteDomainService.server_ip()
                except Exception:
                    ip = None
            return str(ip or '')
        return ''

    @classmethod
    def resolve_magic_variables(cls, content: Any, context: Dict = None):
        """Scan ``content`` for ``${SERVICE_*}`` magic tokens, generate a value
        once per unique token, substitute, and return ``(substituted, generated)``.

        Args:
            content: A string, or a (possibly nested) dict/list — e.g. a parsed
                compose section. Returned with the same shape.
            context: Optional dict with ``app_name`` / ``fqdn`` / ``scheme`` used
                to resolve FQDN/URL tokens. No Docker/network access is performed.

        Returns:
            ``(substituted_content, generated_vars)`` where ``generated_vars`` maps
            each magic variable name (without ``${}``) to its generated value, so
            callers can persist them as env vars / surface them post-install.
            Pure and idempotent for a given ``content`` within one call (the same
            token always maps to the same generated value here).
        """
        context = context or {}
        generated: Dict[str, str] = {}

        def _collect(text: str):
            for match in re.finditer(cls.MAGIC_TOKEN_PATTERN, text):
                token = match.group(1)
                if token in generated:
                    continue
                kind, name = cls._classify_magic_token(token)
                if kind is None:
                    continue
                generated[token] = cls._resolve_magic_value(kind, name, context)

        def _walk_collect(node: Any):
            if isinstance(node, str):
                _collect(node)
            elif isinstance(node, dict):
                for value in node.values():
                    _walk_collect(value)
            elif isinstance(node, list):
                for item in node:
                    _walk_collect(item)

        # Pass 1: discover every unique token and generate a stable value.
        _walk_collect(content)

        # Pass 2: substitute using the generated values. Reuse the existing
        # ${VAR} substitution so behavior is identical to normal variables.
        if isinstance(content, str):
            substituted = cls.substitute_variables(content, generated)
        else:
            substituted = cls.substitute_in_dict(content, generated)

        return substituted, generated

    @classmethod
    def collect_magic_variables(cls, template: Dict, context: Dict = None) -> Dict[str, str]:
        """Generate the magic variables a template uses, given its declared
        ``compose`` / ``files`` / ``scripts`` sections, WITHOUT mutating the
        template. Returns ``{name: value}`` for every ``${SERVICE_*}`` token found.

        This is the wiring entry point for the install flow: the returned dict is
        merged into the install ``variables`` so the existing ``${VAR}``
        substitution renders the tokens, and so the secrets land in ``.env`` /
        post-install output. Templates with no magic tokens get ``{}`` and behave
        exactly as before.
        """
        # Scan the parts that the installer substitutes against.
        scan_target = {
            'compose': template.get('compose', {}),
            'files': template.get('files', []),
            'scripts': template.get('scripts', {}),
        }
        _, generated = cls.resolve_magic_variables(scan_target, context)
        return generated

    @classmethod
    def _install_magic_context(cls, template: Dict, app_name: str,
                               variables: Dict = None) -> Dict:
        """Build the best-effort ``context`` for magic-variable resolution at
        install time.

        Resolves the would-be FQDN from the managed-sites base domain when one is
        configured (the same ``<slug>.<base>`` the finalizer publishes), and the
        scheme from whether wildcard HTTPS is on. All of this is best-effort and
        non-fatal: if site routing isn't set up (or we're outside an app context),
        FQDN/URL tokens fall back to a documented ``localhost`` placeholder that
        the install finalizer can later fill in.
        """
        context = {'app_name': app_name}
        try:
            from app.services.site_domain_service import SiteDomainService
            base = SiteDomainService.base_domain()
            # Only assign an FQDN when the template opts into auto-domain and a
            # base domain exists — mirrors the finalizer's publish condition.
            if base and template.get('auto_domain'):
                host = SiteDomainService.subdomain_for(app_name)
                if host:
                    context['fqdn'] = host
                    context['scheme'] = 'https' if (
                        SiteDomainService.https_enabled()
                        and SiteDomainService.covers(host)
                    ) else 'http'
        except Exception:
            # No app context / site routing not available — leave FQDN unset so
            # tokens degrade to the localhost placeholder.
            pass
        return context

    @classmethod
    def _collect_magic_for_install(cls, template: Dict, app_name: str,
                                   variables: Dict = None) -> Dict[str, str]:
        """Resolve a template's magic variables for an install, using the
        best-effort FQDN context. Thin wrapper over :meth:`collect_magic_variables`."""
        context = cls._install_magic_context(template, app_name, variables)
        return cls.collect_magic_variables(template, context)

    @classmethod
    def substitute_variables(cls, content: str, variables: Dict) -> str:
        """Substitute variables in content using ${VAR} syntax."""
        def replace_var(match):
            var_name = match.group(1)
            return str(variables.get(var_name, match.group(0)))

        # Replace ${VAR} patterns
        pattern = r'\$\{([A-Z_][A-Z0-9_]*)\}'
        return re.sub(pattern, replace_var, content)

    @classmethod
    def substitute_in_dict(cls, data: Any, variables: Dict) -> Any:
        """Recursively substitute variables in a dictionary."""
        if isinstance(data, str):
            return cls.substitute_variables(data, variables)
        elif isinstance(data, dict):
            return {k: cls.substitute_in_dict(v, variables) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.substitute_in_dict(item, variables) for item in data]
        return data
