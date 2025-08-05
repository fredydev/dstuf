#!/usr/bin/env python3
"""
Unit tests for main module
Coverage target: 80%
"""

import pytest
import json
import csv
import os
import tempfile
from unittest.mock import Mock, patch, call
from io import StringIO
import sys
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main, export_to_csv, export_to_json, export_classification_to_csv, export_classification_to_json
from sonar_qube_service import (
    SonarQubeService, 
    QualityMetrics, 
    ProjectClassification,
    ProjectClassificationStatus,
    SonarQubeConfig
)


class TestMainFunctions:
    """Test main module functions"""
    
    def setup_method(self):
        """Setup test environment"""
        self.sample_metrics = [
            QualityMetrics(
                project_key="project1",
                project_name="Project 1",
                quality_gate_status="OK",
                coverage="85.0",
                bugs="5",
                vulnerabilities="2",
                code_smells="10",
                technical_debt="2h",
                duplicated_lines_density="1.5",
                reliability_rating="A",
                security_rating="A",
                maintainability_rating="B"
            ),
            QualityMetrics(
                project_key="project2",
                project_name="Project 2", 
                quality_gate_status="ERROR",
                coverage="45.0",
                bugs="15",
                vulnerabilities="8",
                code_smells="25",
                technical_debt="8h",
                duplicated_lines_density="3.2",
                reliability_rating="C",
                security_rating="B",
                maintainability_rating="D"
            )
        ]
        
        self.sample_classification = ProjectClassification(
            active_projects=[
                ProjectClassificationStatus(
                    project_key="active1",
                    project_name="Active Project 1",
                    status="active",
                    last_analysis_date="2024-01-01T00:00:00Z",
                    reason="Recent analysis with metrics"
                )
            ],
            configured_inactive_projects=[
                ProjectClassificationStatus(
                    project_key="inactive1",
                    project_name="Inactive Project 1",
                    status="configured_inactive",
                    last_analysis_date="2023-01-01T00:00:00Z",
                    reason="Old analysis or missing metrics"
                )
            ],
            total_projects=2,
            classification_date="2024-01-01T00:00:00Z"
        )
    
    def test_export_to_csv(self):
        """Test CSV export functionality"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_file:
            temp_filename = temp_file.name
        
        try:
            export_to_csv(self.sample_metrics, temp_filename)
            
            # Verify file was created and has correct content
            assert os.path.exists(temp_filename)
            
            with open(temp_filename, 'r') as f:
                content = f.read()
                assert "project1" in content
                assert "Project 1" in content
                assert "85.0" in content
                assert "OK" in content
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
    
    def test_export_to_json(self):
        """Test JSON export functionality"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filename = temp_file.name
        
        try:
            export_to_json(self.sample_metrics, temp_filename)
            
            # Verify file was created and has correct content
            assert os.path.exists(temp_filename)
            
            with open(temp_filename, 'r') as f:
                data = json.load(f)
                assert len(data) == 2
                assert data[0]["project_key"] == "project1"
                assert data[0]["coverage"] == "85.0"
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
    
    def test_export_classification_to_csv(self):
        """Test classification CSV export"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_file:
            temp_filename = temp_file.name
        
        try:
            export_classification_to_csv(self.sample_classification, temp_filename)
            
            assert os.path.exists(temp_filename)
            
            with open(temp_filename, 'r') as f:
                content = f.read()
                assert "active1" in content
                assert "inactive1" in content
                assert "active" in content
                assert "configured_inactive" in content
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
    
    def test_export_classification_to_json(self):
        """Test classification JSON export"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filename = temp_file.name
        
        try:
            export_classification_to_json(self.sample_classification, temp_filename)
            
            assert os.path.exists(temp_filename)
            
            with open(temp_filename, 'r') as f:
                data = json.load(f)
                assert "active_projects" in data
                assert "configured_inactive_projects" in data
                assert len(data["active_projects"]) == 1
                assert len(data["configured_inactive_projects"]) == 1
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)


class TestMainCLI:
    """Test main CLI functionality"""
    
    @patch('sys.argv', ['main.py'])
    @patch.object(SonarQubeService, 'get_config')
    @patch.object(SonarQubeService, 'test_connection')
    @patch.object(SonarQubeService, 'get_all_projects_quality_metrics')
    @patch('builtins.print')
    def test_main_default_behavior(self, mock_print, mock_get_metrics, mock_test_conn, mock_get_config):
        """Test main function default behavior"""
        # Setup mocks
        mock_get_config.return_value = SonarQubeConfig(
            server_url="http://localhost:9000",
            username="admin",
            password="admin"
        )
        mock_test_conn.return_value = True
        mock_get_metrics.return_value = [
            QualityMetrics(
                project_key="test_project",
                project_name="Test Project",
                quality_gate_status="OK",
                coverage="80.0",
                bugs="0",
                vulnerabilities="0", 
                code_smells="5",
                technical_debt="1h",
                duplicated_lines_density="2.0",
                reliability_rating="A",
                security_rating="A",
                maintainability_rating="A"
            )
        ]
        
        main()
        
        # Verify calls were made
        mock_get_config.assert_called_once()
        mock_test_conn.assert_called_once()
        mock_get_metrics.assert_called_once()
        
        # Verify output contains expected information
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output = " ".join(print_calls)
        assert "test_project" in output
    
    @patch('sys.argv', ['main.py', '--classify'])
    @patch.object(SonarQubeService, 'get_config')
    @patch.object(SonarQubeService, 'test_connection')
    @patch.object(SonarQubeService, 'classify_projects')
    @patch('builtins.print')
    def test_main_classify_option(self, mock_print, mock_classify, mock_test_conn, mock_get_config):
        """Test main function with classify option"""
        # Setup mocks
        mock_get_config.return_value = SonarQubeConfig(
            server_url="http://localhost:9000",
            username="admin", 
            password="admin"
        )
        mock_test_conn.return_value = True
        mock_classify.return_value = ProjectClassification(
            active_projects=[],
            configured_inactive_projects=[],
            total_projects=0,
            classification_date="2024-01-01T00:00:00Z"
        )
        
        main()
        
        # Verify classify was called
        mock_classify.assert_called_once()
    
    @patch('sys.argv', ['main.py', '--export-csv', 'test_output.csv'])
    @patch.object(SonarQubeService, 'get_config')
    @patch.object(SonarQubeService, 'test_connection')
    @patch.object(SonarQubeService, 'get_all_projects_quality_metrics')
    @patch('main.export_to_csv')
    def test_main_export_csv(self, mock_export_csv, mock_get_metrics, mock_test_conn, mock_get_config):
        """Test main function with CSV export"""
        # Setup mocks
        mock_get_config.return_value = SonarQubeConfig(
            server_url="http://localhost:9000",
            username="admin",
            password="admin"
        )
        mock_test_conn.return_value = True
        mock_get_metrics.return_value = []
        
        main()
        
        # Verify export was called with correct filename
        mock_export_csv.assert_called_once_with([], 'test_output.csv')
    
    @patch('sys.argv', ['main.py', '--export-json', 'test_output.json'])
    @patch.object(SonarQubeService, 'get_config')
    @patch.object(SonarQubeService, 'test_connection')
    @patch.object(SonarQubeService, 'get_all_projects_quality_metrics')
    @patch('main.export_to_json')
    def test_main_export_json(self, mock_export_json, mock_get_metrics, mock_test_conn, mock_get_config):
        """Test main function with JSON export"""
        # Setup mocks
        mock_get_config.return_value = SonarQubeConfig(
            server_url="http://localhost:9000",
            username="admin",
            password="admin"
        )
        mock_test_conn.return_value = True
        mock_get_metrics.return_value = []
        
        main()
        
        # Verify export was called with correct filename
        mock_export_json.assert_called_once_with([], 'test_output.json')
    
    @patch('sys.argv', ['main.py', '--classify', '--export-classification-csv', 'classification.csv'])
    @patch.object(SonarQubeService, 'get_config')
    @patch.object(SonarQubeService, 'test_connection')
    @patch.object(SonarQubeService, 'classify_projects')
    @patch('main.export_classification_to_csv')
    def test_main_classify_export_csv(self, mock_export_csv, mock_classify, mock_test_conn, mock_get_config):
        """Test main function with classify and CSV export"""
        # Setup mocks
        mock_get_config.return_value = SonarQubeConfig(
            server_url="http://localhost:9000",
            username="admin",
            password="admin"
        )
        mock_test_conn.return_value = True
        classification = ProjectClassification(
            active_projects=[],
            configured_inactive_projects=[],
            total_projects=0,
            classification_date="2024-01-01T00:00:00Z"
        )
        mock_classify.return_value = classification
        
        main()
        
        # Verify export was called
        mock_export_csv.assert_called_once_with(classification, 'classification.csv')
    
    @patch('sys.argv', ['main.py'])
    @patch.object(SonarQubeService, 'get_config')
    @patch('builtins.print')
    def test_main_no_config(self, mock_print, mock_get_config):
        """Test main function when no config exists"""
        mock_get_config.return_value = None
        
        main()
        
        # Verify error message was printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output = " ".join(print_calls)
        assert "configuration" in output.lower()
    
    @patch('sys.argv', ['main.py'])
    @patch.object(SonarQubeService, 'get_config')
    @patch.object(SonarQubeService, 'test_connection')
    @patch('builtins.print')
    def test_main_connection_failed(self, mock_print, mock_test_conn, mock_get_config):
        """Test main function when connection fails"""
        mock_get_config.return_value = SonarQubeConfig(
            server_url="http://localhost:9000",
            username="admin",
            password="admin"
        )
        mock_test_conn.return_value = False
        
        main()
        
        # Verify error message was printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output = " ".join(print_calls)
        assert "connection" in output.lower() or "failed" in output.lower()


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_export_csv_invalid_path(self):
        """Test CSV export with invalid path"""
        invalid_path = "/invalid/path/that/does/not/exist/file.csv"
        
        with pytest.raises(Exception):
            export_to_csv([], invalid_path)
    
    def test_export_json_invalid_path(self):
        """Test JSON export with invalid path"""
        invalid_path = "/invalid/path/that/does/not/exist/file.json"
        
        with pytest.raises(Exception):
            export_to_json([], invalid_path)
    
    def test_export_classification_csv_invalid_path(self):
        """Test classification CSV export with invalid path"""
        invalid_path = "/invalid/path/that/does/not/exist/file.csv"
        classification = ProjectClassification(
            active_projects=[],
            configured_inactive_projects=[],
            total_projects=0,
            classification_date="2024-01-01T00:00:00Z"
        )
        
        with pytest.raises(Exception):
            export_classification_to_csv(classification, invalid_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=main", "--cov-report=html", "--cov-report=term"])
