"""
Database Loader - Load mock data for matching
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


def load_mock_database(mock_data_path: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load mock database from JSON file
    
    Args:
        mock_data_path: Path to mock data JSON (default: tests/mock-data.json)
    
    Returns:
        Dictionary with owners, customers, properties lists
    """
    if mock_data_path is None:
        # Default path
        root_dir = Path(__file__).parent.parent.parent
        mock_data_path = root_dir / "tests" / "mock-data.json"
    
    with open(mock_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    database_records = data.get("database_records", {})
    
    return {
        "owners": database_records.get("owners", []),
        "customers": database_records.get("customers", []),
        "properties": database_records.get("properties", [])
    }


def load_sample_receipts(mock_data_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load sample receipts from mock data
    
    Args:
        mock_data_path: Path to mock data JSON
    
    Returns:
        List of sample receipts
    """
    if mock_data_path is None:
        root_dir = Path(__file__).parent.parent.parent
        mock_data_path = root_dir / "tests" / "mock-data.json"
    
    with open(mock_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get("dekont_ornekleri", [])


__all__ = [
    "load_mock_database",
    "load_sample_receipts"
]
