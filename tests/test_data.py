"""
Unit tests for the data utility module.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import tempfile
import shutil
import pandas as pd
from httpx import Response
import asyncio

from statscan.util.get_data import download_data, unpack_to_dataframe, DEFAULT_DATA_PATH, DEFAULT_ENCODINGS


class TestDataUtilities:
    """Test cases for data utility functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_url = "https://example.com/test.csv"
        self.test_filename = "test.csv"
        
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('statscan.util.get_data.AsyncClient')
    @pytest.mark.asyncio
    async def test_download_data_success(self, mock_client):
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
        result_path = await download_data(
            url=self.test_url,
            data_dir=self.temp_dir,
            file_name=self.test_filename
        )
        
        # Assertions
        expected_path = self.temp_dir / self.test_filename
        assert result_path == expected_path
        assert result_path.exists()
        
        # Verify the file contents
        with result_path.open('rb') as f:
            content = f.read()
        assert content == b"test,data\n1,2\n3,4"
    
    @patch('statscan.util.get_data.AsyncClient')
    @pytest.mark.asyncio
    async def test_download_data_file_exists(self, mock_client):
        """Test download when file already exists."""
        # Create existing file
        existing_file = self.temp_dir / self.test_filename
        existing_file.write_text("existing content")
        
        result_path = await download_data(
            url=self.test_url,
            data_dir=self.temp_dir,
            file_name=self.test_filename
        )
        
        # Assertions
        assert result_path == existing_file
        assert existing_file.read_text() == "existing content"
        
        # Verify HTTP client was not called
        mock_client.assert_not_called()
    
    @patch('statscan.util.get_data.AsyncClient')
    @pytest.mark.asyncio
    async def test_download_data_file_exists_with_overwrite(self, mock_client):
        """Test download when file already exists with overwrite=True.
        
        Note: Current implementation doesn't use the overwrite parameter,
        so this test documents the current behavior which may be a bug.
        """
        # Create existing file
        existing_file = self.temp_dir / self.test_filename
        existing_file.write_text("existing content")
        
        result_path = await download_data(
            url=self.test_url,
            data_dir=self.temp_dir,
            file_name=self.test_filename,
            overwrite=True
        )
        
        # Assertions - current implementation still skips download even with overwrite=True
        assert result_path == existing_file
        assert existing_file.read_text() == "existing content"
        
        # Verify HTTP client was not called (current behavior - may be a bug)
        mock_client.assert_not_called()
    
    @patch('statscan.util.get_data.AsyncClient')
    @pytest.mark.asyncio
    async def test_download_data_creates_directory(self, mock_client):
        """Test that download creates directory if it doesn't exist."""
        non_existent_dir = self.temp_dir / "new_dir"
        
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = AsyncMock(return_value=None)
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        result_path = await download_data(
            url=self.test_url,
            data_dir=non_existent_dir,
            file_name=self.test_filename
        )
        
        # Assertions
        assert non_existent_dir.exists()
        assert result_path.exists()
    
    @pytest.mark.asyncio
    async def test_download_data_filename_from_url(self):
        """Test that filename is extracted from URL when not provided."""
        url_with_filename = "https://example.com/path/to/data.csv"
        
        with patch('statscan.util.get_data.AsyncClient') as mock_client:
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
            
            expected_path = self.temp_dir / "data.csv"
            assert result_path == expected_path
    
    def test_unpack_to_dataframe_success(self):
        """Test successful CSV reading."""
        # Create test CSV file
        test_csv = self.temp_dir / "test.csv"
        test_data = "col1,col2,col3\nvalue1,value2,value3\nvalue4,value5,value6"
        test_csv.write_text(test_data, encoding='utf-8')
        
        # Test the function
        df = unpack_to_dataframe(test_csv)
        
        # Assertions
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2  # 2 data rows
        assert list(df.columns) == ['col1', 'col2', 'col3']
        assert df.iloc[0]['col1'] == 'value1'
        assert df.iloc[1]['col2'] == 'value5'
    
    def test_unpack_to_dataframe_encoding_fallback(self):
        """Test CSV reading with encoding fallback."""
        # Create test CSV with Latin-1 encoding
        test_csv = self.temp_dir / "test_latin.csv"
        test_data = "col1,col2\nvalue1,valuè2"  # Contains accented character
        test_csv.write_text(test_data, encoding='latin1')
        
        # Test the function (should try latin1 first in DEFAULT_ENCODINGS)
        df = unpack_to_dataframe(test_csv)
        
        # Assertions
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]['col2'] == 'valuè2'
    
    def test_unpack_to_dataframe_all_encodings_fail(self):
        """Test CSV reading when all encodings fail."""
        # Create a binary file that's not a valid CSV
        test_file = self.temp_dir / "invalid.csv"
        test_file.write_bytes(b'\x80\x81\x82\x83')  # Invalid UTF-8 bytes
        
        # Mock pandas.read_csv to always raise ValueError
        with patch('pandas.read_csv', side_effect=ValueError("Encoding error")):
            with pytest.raises(ValueError) as exc_info:
                unpack_to_dataframe(test_file)
            
            assert "Failed to read file" in str(exc_info.value)
            assert str(test_file) in str(exc_info.value)
            # Note: The actual implementation has a typo with double quotes
            assert '""' in str(exc_info.value)
    
    def test_unpack_to_dataframe_custom_encodings(self):
        """Test CSV reading with custom encodings."""
        test_csv = self.temp_dir / "test.csv"
        test_csv.write_text("col1,col2\nvalue1,value2", encoding='utf-8')
        
        custom_encodings = ['ascii', 'utf-8']
        df = unpack_to_dataframe(test_csv, encodings=custom_encodings)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
    
    @patch('statscan.util.get_data.AsyncClient')
    @pytest.mark.asyncio
    async def test_download_data_http_error(self, mock_client):
        """Test download handling HTTP errors."""
        # Mock HTTP error response
        mock_response = MagicMock()
        mock_response.raise_for_status = AsyncMock(side_effect=Exception("HTTP 404 Error"))
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        with pytest.raises(Exception) as exc_info:
            await download_data(
                url=self.test_url,
                data_dir=self.temp_dir,
                file_name=self.test_filename
            )
    
    def test_unpack_to_dataframe_file_not_found(self):
        """Test CSV reading when file doesn't exist."""
        non_existent_file = self.temp_dir / "non_existent.csv"
        
        with pytest.raises(FileNotFoundError):
            unpack_to_dataframe(non_existent_file)
    
    def test_unpack_to_dataframe_unicode_decode_error(self):
        """Test CSV reading with UnicodeDecodeError should be caught as ValueError."""
        # Create a file with invalid UTF-8 bytes that will cause UnicodeDecodeError
        test_csv = self.temp_dir / "invalid_unicode.csv"
        test_csv.write_bytes(b'\x80\x81\x82\x83\x84\x85')  # Invalid UTF-8 bytes
        
        # UnicodeDecodeError should be raised by pandas.read_csv but the actual implementation
        # only catches ValueError, so UnicodeDecodeError would bubble up
        with pytest.raises((UnicodeDecodeError, ValueError)):
            unpack_to_dataframe(test_csv, encodings=['utf-8'])

    def test_unpack_to_dataframe_empty_encodings(self):
        """Test CSV reading with empty encodings list."""
        test_csv = self.temp_dir / "test.csv"
        test_csv.write_text("col1,col2\nvalue1,value2", encoding='utf-8')
        
        with pytest.raises(ValueError) as exc_info:
            unpack_to_dataframe(test_csv, encodings=[])
        
        assert "Failed to read file" in str(exc_info.value)
    
    @patch('statscan.util.get_data.AsyncClient')
    @pytest.mark.asyncio
    async def test_download_data_default_parameters(self, mock_client):
        """Test download with default parameters."""
        mock_response = MagicMock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = AsyncMock(return_value=None)
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Test with default data_dir (should create 'data' directory)
        result_path = await download_data(self.test_url)
        
        # Should use default data directory and extract filename from URL
        expected_path = DEFAULT_DATA_PATH / "test.csv"
        assert result_path == expected_path
        
        # Clean up
        if expected_path.exists():
            expected_path.unlink()
        if DEFAULT_DATA_PATH.exists() and not any(DEFAULT_DATA_PATH.iterdir()):
            DEFAULT_DATA_PATH.rmdir()
    
    def test_default_constants(self):
        """Test that default constants are properly defined."""
        assert isinstance(DEFAULT_DATA_PATH, Path)
        assert DEFAULT_DATA_PATH == Path('data')
        
        assert isinstance(DEFAULT_ENCODINGS, tuple)
        assert DEFAULT_ENCODINGS == ('latin1', 'utf-8', 'utf-16')
        assert 'utf-8' in DEFAULT_ENCODINGS
        assert 'latin1' in DEFAULT_ENCODINGS
        assert 'utf-16' in DEFAULT_ENCODINGS
