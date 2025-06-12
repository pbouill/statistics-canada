"""
Unit tests for the data utility module.
"""
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import tempfile
import shutil
import pandas as pd
from httpx import Response
import asyncio

from statscan.util.data import download_data, unpack_to_dataframe, DEFAULT_DATA_PATH, DEFAULT_ENCODINGS


class TestDataUtilities(unittest.TestCase):
    """Test cases for data utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_url = "https://example.com/test.csv"
        self.test_filename = "test.csv"
        
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('statscan.util.data.AsyncClient')
    def test_download_data_success(self, mock_client):
        """Test successful data download."""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.content = b"test,data\n1,2\n3,4"
        mock_response.raise_for_status = AsyncMock(return_value=None)
        
        # Mock the async context manager
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Run the test
        async def run_test():
            result_path = await download_data(
                url=self.test_url,
                data_dir=self.temp_dir,
                file_name=self.test_filename
            )
            return result_path
        
        result_path = asyncio.run(run_test())
        
        # Assertions
        expected_path = self.temp_dir / self.test_filename
        self.assertEqual(result_path, expected_path)
        self.assertTrue(result_path.exists())
        
        # Verify the file contents
        with result_path.open('rb') as f:
            content = f.read()
        self.assertEqual(content, b"test,data\n1,2\n3,4")
    
    @patch('statscan.util.data.AsyncClient')
    def test_download_data_file_exists(self, mock_client):
        """Test download when file already exists."""
        # Create existing file
        existing_file = self.temp_dir / self.test_filename
        existing_file.write_text("existing content")
        
        async def run_test():
            result_path = await download_data(
                url=self.test_url,
                data_dir=self.temp_dir,
                file_name=self.test_filename
            )
            return result_path
        
        result_path = asyncio.run(run_test())
        
        # Assertions
        self.assertEqual(result_path, existing_file)
        self.assertEqual(existing_file.read_text(), "existing content")
        
        # Verify HTTP client was not called
        mock_client.assert_not_called()
    
    @patch('statscan.util.data.AsyncClient')
    def test_download_data_creates_directory(self, mock_client):
        """Test that download creates directory if it doesn't exist."""
        non_existent_dir = self.temp_dir / "new_dir"
        
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = AsyncMock(return_value=None)
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        async def run_test():
            result_path = await download_data(
                url=self.test_url,
                data_dir=non_existent_dir,
                file_name=self.test_filename
            )
            return result_path
        
        result_path = asyncio.run(run_test())
        
        # Assertions
        self.assertTrue(non_existent_dir.exists())
        self.assertTrue(result_path.exists())
    
    def test_download_data_filename_from_url(self):
        """Test that filename is extracted from URL when not provided."""
        url_with_filename = "https://example.com/path/to/data.csv"
        
        async def run_test():
            with patch('statscan.util.data.AsyncClient') as mock_client:
                mock_response = MagicMock()
                mock_response.content = b"test"
                mock_response.raise_for_status = AsyncMock(return_value=None)
                
                mock_client_instance = AsyncMock()
                mock_client_instance.get.return_value = mock_response
                mock_client.return_value.__aenter__.return_value = mock_client_instance
                
                result_path = await download_data(
                    url=url_with_filename,
                    data_dir=self.temp_dir
                )
                return result_path
        
        result_path = asyncio.run(run_test())
        expected_path = self.temp_dir / "data.csv"
        self.assertEqual(result_path, expected_path)
    
    def test_unpack_to_dataframe_success(self):
        """Test successful CSV reading."""
        # Create test CSV file
        test_csv = self.temp_dir / "test.csv"
        test_data = "col1,col2,col3\nvalue1,value2,value3\nvalue4,value5,value6"
        test_csv.write_text(test_data, encoding='utf-8')
        
        # Test the function
        df = unpack_to_dataframe(test_csv)
        
        # Assertions
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)  # 2 data rows
        self.assertEqual(list(df.columns), ['col1', 'col2', 'col3'])
        self.assertEqual(df.iloc[0]['col1'], 'value1')
        self.assertEqual(df.iloc[1]['col2'], 'value5')
    
    def test_unpack_to_dataframe_encoding_fallback(self):
        """Test CSV reading with encoding fallback."""
        # Create test CSV with Latin-1 encoding
        test_csv = self.temp_dir / "test_latin.csv"
        test_data = "col1,col2\nvalue1,valuè2"  # Contains accented character
        test_csv.write_text(test_data, encoding='latin1')
        
        # Test the function (should try latin1 first in DEFAULT_ENCODINGS)
        df = unpack_to_dataframe(test_csv)
        
        # Assertions
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['col2'], 'valuè2')
    
    def test_unpack_to_dataframe_all_encodings_fail(self):
        """Test CSV reading when all encodings fail."""
        # Create a binary file that's not a valid CSV
        test_file = self.temp_dir / "invalid.csv"
        test_file.write_bytes(b'\x80\x81\x82\x83')  # Invalid UTF-8 bytes
        
        # Mock pandas.read_csv to always raise ValueError
        with patch('pandas.read_csv', side_effect=ValueError("Encoding error")):
            with self.assertRaises(ValueError) as context:
                unpack_to_dataframe(test_file)
            
            self.assertIn("Failed to read file", str(context.exception))
            self.assertIn(str(test_file), str(context.exception))
    
    def test_unpack_to_dataframe_custom_encodings(self):
        """Test CSV reading with custom encodings."""
        test_csv = self.temp_dir / "test.csv"
        test_csv.write_text("col1,col2\nvalue1,value2", encoding='utf-8')
        
        custom_encodings = ['ascii', 'utf-8']
        df = unpack_to_dataframe(test_csv, encodings=custom_encodings)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
    
    def test_default_constants(self):
        """Test that default constants are properly defined."""
        self.assertIsInstance(DEFAULT_DATA_PATH, Path)
        self.assertEqual(DEFAULT_DATA_PATH, Path('data'))
        
        self.assertIsInstance(DEFAULT_ENCODINGS, tuple)
        self.assertIn('utf-8', DEFAULT_ENCODINGS)
        self.assertIn('latin1', DEFAULT_ENCODINGS)


if __name__ == '__main__':
    unittest.main()
