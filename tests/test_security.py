# tests/test_security.py — Tests automáticos de seguridad
import os
import sys
import time
import hmac
import hashlib
import base64
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFirmaTwilio:
    def setup_method(self):
        os.environ["TWILIO_AUTH_TOKEN"] = "auth-token-de-prueba-twilio-12345"
        from agent.providers.twilio import ProveedorTwilio
        self.proveedor = ProveedorTwilio()

    def teardown_method(self):
        os.environ.pop("TWILIO_AUTH_TOKEN", None)

    def _firmar(self, url: str, params: dict, token: str) -> str:
        cadena = url + "".join(k + params[k] for k in sorted(params))
        return base64.b64encode(
            hmac.new(token.encode(), cadena.encode(), hashlib.sha1).digest()
        ).decode()

    def test_firma_valida_acepta(self):
        url = "https://example.com/webhook"
        params = {"Body": "hola", "From": "whatsapp:+5491100000000", "MessageSid": "SM1"}
        firma = self._firmar(url, params, "auth-token-de-prueba-twilio-12345")
        assert self.proveedor._verificar_firma(url, params, firma) is True

    def test_firma_invalida_rechaza(self):
        url = "https://example.com/webhook"
        params = {"Body": "hola"}
        assert self.proveedor._verificar_firma(url, params, self._firmar(url, params, "MAL")) is False

    def test_url_modificada_rechaza(self):
        params = {"Body": "hola"}
        firma = self._firmar("https://bueno.com/webhook", params, "auth-token-de-prueba-twilio-12345")
        assert self.proveedor._verificar_firma("https://malo.com/webhook", params, firma) is False

    def test_param_modificado_rechaza(self):
        url = "https://example.com/webhook"
        firma = self._firmar(url, {"Body": "original"}, "auth-token-de-prueba-twilio-12345")
        assert self.proveedor._verificar_firma(url, {"Body": "modificado"}, firma) is False

    def test_firma_vacia_rechaza(self):
        assert self.proveedor._verificar_firma("https://x.com", {}, "") is False


class TestIdempotencia:
    def setup_method(self):
        from agent.security import MENSAJES_PROCESADOS
        MENSAJES_PROCESADOS.clear()

    def test_mensaje_nuevo_no_esta_procesado(self):
        from agent.security import ya_procesado
        assert ya_procesado("MSG-001") is False

    def test_mensaje_marcado_se_detecta(self):
        from agent.security import ya_procesado, marcar_procesado
        marcar_procesado("MSG-001")
        assert ya_procesado("MSG-001") is True

    def test_id_vacio_devuelve_false(self):
        from agent.security import ya_procesado
        assert ya_procesado("") is False
        assert ya_procesado(None) is False

    def test_cache_acotado_al_maximo(self):
        from agent.security import marcar_procesado, MENSAJES_PROCESADOS, MENSAJES_PROCESADOS_MAX
        for i in range(MENSAJES_PROCESADOS_MAX + 100):
            marcar_procesado(f"MSG-{i}")
        assert len(MENSAJES_PROCESADOS) <= MENSAJES_PROCESADOS_MAX

    def test_entradas_expiradas_se_limpian(self):
        from agent.security import ya_procesado, MENSAJES_PROCESADOS, MENSAJES_PROCESADOS_TTL
        MENSAJES_PROCESADOS["VIEJO"] = time.time() - MENSAJES_PROCESADOS_TTL - 10
        ya_procesado("NUEVO")
        assert "VIEJO" not in MENSAJES_PROCESADOS


class TestSanitizacion:
    def test_texto_normal_pasa(self):
        from agent.security import sanitizar_mensaje
        assert sanitizar_mensaje("Hola, ¿cómo estás?") == "Hola, ¿cómo estás?"

    def test_trunca_a_max_longitud(self):
        from agent.security import sanitizar_mensaje, MAX_LONGITUD_MENSAJE
        assert len(sanitizar_mensaje("a" * (MAX_LONGITUD_MENSAJE + 500))) <= MAX_LONGITUD_MENSAJE

    def test_elimina_caracteres_de_control(self):
        from agent.security import sanitizar_mensaje
        assert sanitizar_mensaje("hola\x00mundo") == "holamundo"
        assert sanitizar_mensaje("test\x1bcommand") == "testcommand"

    def test_preserva_newlines_y_tabs(self):
        from agent.security import sanitizar_mensaje
        assert sanitizar_mensaje("linea1\nlinea2") == "linea1\nlinea2"
        assert sanitizar_mensaje("col1\tcol2") == "col1\tcol2"

    def test_nfkc_normaliza_homoglyphs(self):
        from agent.security import sanitizar_mensaje
        assert sanitizar_mensaje("ＡＢＣ") == "ABC"

    def test_vacio_devuelve_vacio(self):
        from agent.security import sanitizar_mensaje
        assert sanitizar_mensaje("") == ""
        assert sanitizar_mensaje(None) == ""


class TestRateLimit:
    def setup_method(self):
        from agent.security import RATE_LIMIT_TRACKER
        RATE_LIMIT_TRACKER.clear()

    def test_primer_mensaje_pasa(self):
        from agent.security import rate_limit_excedido
        assert rate_limit_excedido("5491100000000") is False

    def test_dentro_del_limite_pasa(self):
        from agent.security import rate_limit_excedido, RATE_LIMIT_MENSAJES
        for _ in range(RATE_LIMIT_MENSAJES):
            assert rate_limit_excedido("5491100000000") is False

    def test_superar_limite_bloquea(self):
        from agent.security import rate_limit_excedido, RATE_LIMIT_MENSAJES
        for _ in range(RATE_LIMIT_MENSAJES):
            rate_limit_excedido("5491100000000")
        assert rate_limit_excedido("5491100000000") is True

    def test_limite_es_independiente_por_telefono(self):
        from agent.security import rate_limit_excedido, RATE_LIMIT_MENSAJES
        for _ in range(RATE_LIMIT_MENSAJES):
            rate_limit_excedido("5491100000000")
        assert rate_limit_excedido("5491199999999") is False
