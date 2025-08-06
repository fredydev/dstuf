import pytest
from unittest.mock import MagicMock
from your_module import Ipaas001SnaplogicServiceConnection, Ipaas001SnaplogicServiceConnectionSettings
from azure.devops.v7_1.core.models import TeamProjectReference

@pytest.fixture
def project():
    return TeamProjectReference(id="123", name="CDP.PROJET")

@pytest.fixture
def settings(project):
    return Ipaas001SnaplogicServiceConnectionSettings(project)

@pytest.fixture
def service_connection(settings):
    # Mock des dépendances
    endpoints_mock = MagicMock()
    connection_mock = MagicMock()
    rule = Ipaas001SnaplogicServiceConnection(
        azure_devops_connection=connection_mock,
        azure_devops_service_endpoint=endpoints_mock,
        project=None
    )
    rule._settings = settings
    rule._endpoints = endpoints_mock
    return rule, endpoints_mock


def test_validate_all_connections_exist(service_connection, project):
    rule, endpoints_mock = service_connection

    # Mock: toutes les connexions existent avec URL correcte
    for name, url in rule._settings.required_endpoints.items():
        mock_endpoint = MagicMock()
        mock_endpoint.url = url
        endpoints_mock.get_service_endpoint_by_name.return_value = mock_endpoint

    results = rule.validate(project)
    assert len(results) == 0  # Aucun problème


def test_validate_missing_connection(service_connection, project):
    rule, endpoints_mock = service_connection

    # Mock: aucune connexion trouvée
    endpoints_mock.get_service_endpoint_by_name.return_value = None

    results = rule.validate(project)
    assert len(results) == len(rule._settings.required_endpoints)
    assert "n'a pas été trouvée" in results[0].message


def test_validate_incorrect_url(service_connection, project):
    rule, endpoints_mock = service_connection

    # Mock: connexion existe mais URL incorrecte
    mock_endpoint = MagicMock()
    mock_endpoint.url = "https://wrong-url.com"
    endpoints_mock.get_service_endpoint_by_name.return_value = mock_endpoint

    results = rule.validate(project)
    assert len(results) == len(rule._settings.required_endpoints)
    assert "Attendu:" in results[0].message


def test_remediate_creates_missing_connections(service_connection, project):
    rule, endpoints_mock = service_connection

    # Mock: aucune connexion existante
    endpoints_mock.get_service_endpoint_by_name.return_value = None

    rule.remediate(project)

    # Vérifie que la création est appelée pour chaque connexion manquante
    assert endpoints_mock.create_or_update_service_endpoint.call_count == len(rule._settings.required_endpoints)
