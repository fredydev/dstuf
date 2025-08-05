"""
Tests unitaires pour SonarQubeService.
"""
import pytest
import json
import os
from unittest.mock import Mock, patch, mock_open
import requests

from sonar_qube_service import (
    SonarQubeService, 
    SonarQubeConfig, 
    QualityMetrics,
    SonarProject,
    QualityGate,
    ProjectMeasure
)


class TestSonarQubeService:
    """Tests pour la classe SonarQubeService."""
    
    def setup_method(self):
        """Configuration avant chaque test."""
        self.service = SonarQubeService()
        self.test_config = SonarQubeConfig(
            url="https://sonar.example.com",
            token="test_token_123"
        )
    
    def teardown_method(self):
        """Nettoyage après chaque test."""
        if os.path.exists(SonarQubeService.CONFIG_FILE):
            os.remove(SonarQubeService.CONFIG_FILE)
    
    def test_save_and_load_config(self):
        """Test de sauvegarde et chargement de configuration."""
        # Test sauvegarde
        self.service.save_config(self.test_config)
        
        # Vérification que le fichier existe
        assert os.path.exists(SonarQubeService.CONFIG_FILE)
        
        # Test chargement
        loaded_config = self.service.get_config()
        assert loaded_config is not None
        assert loaded_config.url == self.test_config.url
        assert loaded_config.token == self.test_config.token
    
    def test_load_config_file_not_found(self):
        """Test de chargement quand le fichier n'existe pas."""
        service = SonarQubeService()
        config = service.get_config()
        assert config is None
    
    @patch('builtins.open', mock_open(read_data='{"url": "https://test.com", "token": "token123"}'))
    def test_load_config_from_file(self):
        """Test de chargement de configuration depuis un fichier."""
        service = SonarQubeService()
        config = service.get_config()
        assert config is not None
        assert config.url == "https://test.com"
        assert config.token == "token123"
    
    def test_get_auth_headers_no_config(self):
        """Test des headers d'auth sans configuration."""
        service = SonarQubeService()
        with pytest.raises(ValueError, match="Configuration non trouvée"):
            service._get_auth_headers()
    
    def test_get_auth_headers_with_config(self):
        """Test des headers d'auth avec configuration."""
        self.service.save_config(self.test_config)
        headers = self.service._get_auth_headers()
        
        assert 'Authorization' in headers
        assert headers['Authorization'].startswith('Basic ')
        assert 'Content-Type' in headers
    
    @patch('requests.get')
    def test_test_connection_success(self, mock_get):
        """Test de connexion réussie."""
        # Mock de la réponse
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'status': 'UP'}
        mock_get.return_value = mock_response
        
        self.service.save_config(self.test_config)
        success, error = self.service.test_connection()
        
        assert success is True
        assert error is None
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_test_connection_http_error(self, mock_get):
        """Test de connexion avec erreur HTTP."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.reason = 'Unauthorized'
        mock_get.return_value = mock_response
        
        self.service.save_config(self.test_config)
        success, error = self.service.test_connection()
        
        assert success is False
        assert "HTTP 401: Unauthorized" in error
    
    @patch('requests.get')
    def test_test_connection_sonar_down(self, mock_get):
        """Test de connexion avec SonarQube down."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'status': 'DOWN'}
        mock_get.return_value = mock_response
        
        self.service.save_config(self.test_config)
        success, error = self.service.test_connection()
        
        assert success is False
        assert "SonarQube status: DOWN" in error
    
    @patch('requests.get')
    def test_test_connection_network_error(self, mock_get):
        """Test de connexion avec erreur réseau."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        
        self.service.save_config(self.test_config)
        success, error = self.service.test_connection()
        
        assert success is False
        assert "Erreur de connexion" in error
    
    def test_test_connection_no_config(self):
        """Test de connexion sans configuration."""
        success, error = self.service.test_connection()
        
        assert success is False
        assert error == "Configuration non trouvée"
    
    @patch('requests.get')
    def test_get_all_projects_success(self, mock_get):
        """Test de récupération des projets réussie."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'components': [
                {
                    'key': 'project1',
                    'name': 'Project 1',
                    'qualifier': 'TRK',
                    'visibility': 'public',
                    'lastAnalysisDate': '2023-01-01T10:00:00+0100'
                },
                {
                    'key': 'project2',
                    'name': 'Project 2',
                    'qualifier': 'TRK',
                    'visibility': 'private'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        self.service.save_config(self.test_config)
        success, projects, error = self.service.get_all_projects()
        
        assert success is True
        assert error is None
        assert len(projects) == 2
        assert projects[0].key == 'project1'
        assert projects[0].name == 'Project 1'
        assert projects[1].last_analysis_date is None
    
    @patch('requests.get')
    def test_get_project_quality_gate_success(self, mock_get):
        """Test de récupération de Quality Gate réussie."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'projectStatus': {
                'id': 'qg1',
                'name': 'Sonar way',
                'status': 'OK',
                'conditions': [
                    {
                        'metricKey': 'coverage',
                        'comparator': 'LT',
                        'errorThreshold': '80',
                        'actualValue': '85.2',
                        'status': 'OK'
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        self.service.save_config(self.test_config)
        quality_gate = self.service.get_project_quality_gate('test_project')
        
        assert quality_gate is not None
        assert quality_gate.status == 'OK'
        assert len(quality_gate.conditions) == 1
        assert quality_gate.conditions[0].metric_key == 'coverage'
    
    @patch('requests.get')
    def test_get_project_measures_success(self, mock_get):
        """Test de récupération des mesures réussie."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'component': {
                'measures': [
                    {'metric': 'coverage', 'value': '85.2'},
                    {'metric': 'bugs', 'value': '5'},
                    {'metric': 'ncloc', 'value': '1000'}
                ]
            }
        }
        mock_get.return_value = mock_response
        
        self.service.save_config(self.test_config)
        measures = self.service.get_project_measures('test_project')
        
        assert len(measures) == 3
        assert measures[0].metric == 'coverage'
        assert measures[0].value == '85.2'
    
    def test_format_technical_debt(self):
        """Test du formatage de la dette technique."""
        # Test avec valeur normale
        assert SonarQubeService.format_technical_debt('480') == '1j 0h'
        assert SonarQubeService.format_technical_debt('600') == '1j 2h'
        assert SonarQubeService.format_technical_debt('120') == '2h'
        
        # Test avec valeur None ou vide
        assert SonarQubeService.format_technical_debt(None) == 'N/A'
        assert SonarQubeService.format_technical_debt('') == 'N/A'
        
        # Test avec valeur invalide
        assert SonarQubeService.format_technical_debt('invalid') == 'N/A'
    
    def test_get_rating_label(self):
        """Test de la conversion des notes."""
        assert SonarQubeService.get_rating_label('1') == 'A'
        assert SonarQubeService.get_rating_label('2') == 'B'
        assert SonarQubeService.get_rating_label('3') == 'C'
        assert SonarQubeService.get_rating_label('4') == 'D'
        assert SonarQubeService.get_rating_label('5') == 'E'
        assert SonarQubeService.get_rating_label(None) == 'N/A'
        assert SonarQubeService.get_rating_label('unknown') == 'unknown'
    
    @patch.object(SonarQubeService, 'get_all_projects')
    @patch.object(SonarQubeService, 'get_project_quality_gate')
    @patch.object(SonarQubeService, 'get_project_measures')
    def test_get_all_projects_quality_metrics_success(self, mock_measures, mock_quality_gate, mock_projects):
        """Test de récupération de toutes les métriques."""
        # Mock des projets
        mock_projects.return_value = (True, [
            SonarProject('proj1', 'Project 1', 'TRK', 'public', '2023-01-01T10:00:00+0100')
        ], None)
        
        # Mock de la Quality Gate
        mock_quality_gate.return_value = QualityGate('qg1', 'Sonar way', 'OK', [])
        
        # Mock des mesures
        mock_measures.return_value = [
            ProjectMeasure('coverage', '85.2', 'proj1'),
            ProjectMeasure('bugs', '5', 'proj1')
        ]
        
        success, metrics, error = self.service.get_all_projects_quality_metrics()
        
        assert success is True
        assert error is None
        assert len(metrics) == 1
        assert metrics[0].project_key == 'proj1'
        assert metrics[0].quality_gate_status == 'OK'
        assert metrics[0].coverage == '85.2'
        assert metrics[0].bugs == '5'


class TestDataClasses:
    """Tests pour les dataclasses."""
    
    def test_sonar_qube_config(self):
        """Test de SonarQubeConfig."""
        config = SonarQubeConfig(url="https://test.com", token="token123")
        assert config.url == "https://test.com"
        assert config.token == "token123"
    
    def test_quality_metrics(self):
        """Test de QualityMetrics."""
        metrics = QualityMetrics(
            project_key="test_key",
            project_name="Test Project",
            quality_gate_status="OK",
            coverage="85.2"
        )
        assert metrics.project_key == "test_key"
        assert metrics.quality_gate_status == "OK"
        assert metrics.coverage == "85.2"
        assert metrics.bugs is None  # Valeur par défaut


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
