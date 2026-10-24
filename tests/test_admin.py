from fastapi.testclient import TestClient

from jevmura.bucle import Mundo
from jevmura.motor import modelos as m
from jevmura.servidor import crear_app


def cliente(tmp_path, monkeypatch, clave="secreta"):
    if clave:
        monkeypatch.setenv("ALDEA_ADMIN_CLAVE", clave)
    else:
        monkeypatch.delenv("ALDEA_ADMIN_CLAVE", raising=False)
    mundo = Mundo(str(tmp_path / "mundo.db"), semilla=3, segundos_por_turno=0)
    return mundo, TestClient(crear_app(mundo))   # sin `with`: el mundo no echa a andar


def test_sin_contrasena_el_panel_esta_cerrado(tmp_path, monkeypatch):
    _, c = cliente(tmp_path, monkeypatch, clave=None)
    assert c.get("/api/admin/sesion").json() == {"configurado": False, "dentro": False}
    assert c.post("/api/admin/entrar", json={"clave": ""}).status_code == 503
    assert c.get("/api/admin/estado").status_code == 401


def test_entrar_y_salir(tmp_path, monkeypatch):
    _, c = cliente(tmp_path, monkeypatch)
    assert c.get("/api/admin/estado").status_code == 401
    assert c.post("/api/admin/entrar", json={"clave": "mala"}).status_code == 401
    assert c.post("/api/admin/entrar", json={"clave": "secreta"}).status_code == 200
    assert c.get("/api/admin/sesion").json()["dentro"]
    estado = c.get("/api/admin/estado").json()
    assert estado["ajustes"]["velocidad"] == 1 and "gasto" in estado and "servidor" in estado
    c.post("/api/admin/salir")
    assert c.get("/api/admin/estado").status_code == 401


def test_cinco_fallos_bloquean_un_rato(tmp_path, monkeypatch):
    _, c = cliente(tmp_path, monkeypatch)
    for _ in range(5):
        assert c.post("/api/admin/entrar", json={"clave": "mala"}).status_code == 401
    assert c.post("/api/admin/entrar", json={"clave": "secreta"}).status_code == 429


def test_cambiar_la_contrasena_cierra_las_sesiones(tmp_path, monkeypatch):
    _, c = cliente(tmp_path, monkeypatch)
    c.post("/api/admin/entrar", json={"clave": "secreta"})
    monkeypatch.setenv("ALDEA_ADMIN_CLAVE", "otra")
    assert c.get("/api/admin/estado").status_code == 401


def test_los_ajustes_cambian_el_mundo_y_se_guardan(tmp_path, monkeypatch):
    mundo, c = cliente(tmp_path, monkeypatch)
    c.post("/api/admin/entrar", json={"clave": "secreta"})
    assert c.post("/api/admin/ajustes", json={"velocidad": 7}).status_code == 422
    assert c.post("/api/admin/ajustes", json={"usd_dia": 50}).status_code == 422
    r = c.post("/api/admin/ajustes", json={"velocidad": 10, "usd_dia": 0.1, "jev": False, "pausado": True})
    assert r.status_code == 200
    assert mundo.segundos_por_turno == m.TURNO_SEGUNDOS / 10
    assert mundo.presupuesto.por_dia["vecinos"] == round(0.1 / 0.000056 * 0.6)
    assert not mundo.presupuesto.gastar("vecinos", importante=True)     # Jev apagado
    assert c.get("/api/estado").json()["segundos_por_turno"] == 1.0
    otro = Mundo(str(tmp_path / "mundo.db"), semilla=3, segundos_por_turno=0)
    assert otro.ajustes == {"velocidad": 10, "pausado": True, "usd_dia": 0.1, "jev": False}
