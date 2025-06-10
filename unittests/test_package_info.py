"""
Unit tests for the package version information system.
"""
import unittest
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
import sys
import os

# Add the project root to Python path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from package_info import (
    VersionInfo, 
    get_git_head_ref_hash, 
    get_git_head_hash,
    create_version_info,
    PACKAGE_NAME,
    VERSION_FILE
)


class TestVersionInfo(unittest.TestCase):
    """Test cases for version information functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_commit_hash = "abcd1234567890abcd1234567890abcd12345678"
        self.test_ref = "refs/heads/main"
        
        # Store original Path.open for fallback
        original_path_open = Path.open
        test_ref = self.test_ref
        test_commit_hash = self.test_commit_hash
        
        # Set up mock for git operations at file system level
        def mock_path_open(path_instance, *args, **kwargs):
            """Mock git file operations."""
            mock_file = MagicMock()
            
            # Check if this is a version file operation (read or write)
            if str(path_instance).endswith('.py'):
                # For version file operations, use real file operations
                return original_path_open(path_instance, *args, **kwargs)
            
            # Check the path to determine which git file is being opened
            if 'HEAD' in str(path_instance):
                # HEAD file contains "ref: refs/heads/main"
                mock_file.__enter__.return_value.read.return_value = f"ref: {test_ref}"
            else:
                # Ref file contains the commit hash
                mock_file.__enter__.return_value.read.return_value = test_commit_hash
            return mock_file
        
        self.git_mock_patcher = patch.object(Path, 'open', mock_path_open)
        self.git_mock_patcher.start()
        
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.git_mock_patcher.stop()
    
    def test_version_info_creation(self):
        """Test basic VersionInfo creation."""
        vi = VersionInfo()
        
        self.assertEqual(vi.package_name, PACKAGE_NAME)
        self.assertIsInstance(vi.build_time, datetime)
        self.assertEqual(vi.commit, self.test_commit_hash)
        self.assertIsInstance(vi.version, str)
        
        # Version should be in format YYYY.M.D.HHMMSS
        version_parts = vi.version.split('.')
        self.assertEqual(len(version_parts), 4)
        self.assertEqual(len(version_parts[3]), 6)  # HHMMSS
    
    def test_version_str_from_datetime(self):
        """Test version string generation from datetime."""
        test_time = datetime(2025, 6, 9, 14, 30, 45, tzinfo=timezone.utc)
        version = VersionInfo.version_str_from_datetime(test_time)
        
        self.assertEqual(version, "2025.6.9.143045")
    
    def test_get_git_head_ref_hash_success(self):
        """Test successful git reference and hash retrieval."""
        ref, commit_hash = get_git_head_ref_hash()
        
        self.assertEqual(ref, self.test_ref)
        self.assertEqual(commit_hash, self.test_commit_hash)
    
    def test_get_git_head_ref_hash_no_git_dir(self):
        """Test git hash retrieval when .git directory doesn't exist."""
        with patch('pathlib.Path.open', side_effect=FileNotFoundError("Git repository not found")):
            with self.assertRaises(FileNotFoundError):
                get_git_head_ref_hash()
    
    def test_get_git_head_hash(self):
        """Test that get_git_head_hash returns just the hash."""
        hash_result = get_git_head_hash()
        self.assertEqual(hash_result, self.test_commit_hash)
    
    @patch('package_info.get_git_head_ref_hash')
    def test_create_version_info(self, mock_ref_hash):
        """Test create_version_info function."""
        mock_ref_hash.return_value = (self.test_ref, self.test_commit_hash)
        
        with patch('package_info.datetime') as mock_datetime:
            test_time = datetime(2025, 6, 9, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = test_time
            mock_datetime.timezone = timezone  # Keep the real timezone
            
            version_info = create_version_info()
            
            expected_version = "2025.6.9.120000"
            self.assertEqual(version_info['__version__'], expected_version)
            self.assertEqual(version_info['__build_time__'], test_time)
            self.assertEqual(version_info['__commit__'], (self.test_ref, self.test_commit_hash))
    
    def test_write_version_file(self):
        """Test writing version file."""
        test_file = self.temp_dir / "test_version.py"
        
        vi = VersionInfo()
        result_path = vi.write_version_file(test_file)
        
        self.assertEqual(result_path, test_file)
        self.assertTrue(test_file.exists())
        
        # Check file contents
        content = test_file.read_text()
        self.assertIn("__version__:", content)
        self.assertIn("__build_time__:", content)
        self.assertIn("__commit__:", content)
        self.assertIn(self.test_commit_hash, content)
    
    def test_from_version_file(self):
        """Test reading version info from file."""
        test_file = self.temp_dir / "test_version.py"
        
        # Create a test version file with all required fields
        test_content = f'''# This file is automatically generated by ../package_info.py 
__version__: str = '2025.6.9.120000'
__build_time__: str = '2025-06-09T12:00:00+00:00'
__commit__: str = '{self.test_commit_hash}'
'''
        test_file.write_text(test_content)
        
        vi = VersionInfo.from_version_file(test_file)
        
        # The commit should be read correctly from the file
        self.assertEqual(vi.commit, self.test_commit_hash)
        self.assertIsInstance(vi.build_time, datetime)
        self.assertEqual(vi.package_name, test_file.parent.name)
        
        # Check that the build_time was parsed correctly from the file
        expected_time = datetime(2025, 6, 9, 12, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(vi.build_time, expected_time)
        
        # Check that the version is derived from the parsed build_time
        self.assertEqual(vi.version, "2025.6.9.120000")
    
    def test_from_version_file_missing_fields(self):
        """Test that from_version_file raises exception when fields are missing."""
        test_file = self.temp_dir / "incomplete_version.py"
        
        # Create a test version file missing some required fields
        test_content = '''# This file is automatically generated by ../package_info.py 
__version__: str = '2025.6.9.120000'
__build_time__: str = '2025-06-09T12:00:00+00:00'
# Missing __commit__ field
'''
        test_file.write_text(test_content)
        
        with self.assertRaises(ValueError) as context:
            VersionInfo.from_version_file(test_file)
        
        self.assertIn("Missing required fields", str(context.exception))
        self.assertIn("commit", str(context.exception))
    
    def test_update_version_file_no_change(self):
        """Test update_version_file when commit hasn't changed."""
        test_file = self.temp_dir / "test_version.py"
        
        # Create initial version
        vi1 = VersionInfo()
        vi1.write_version_file(test_file)
        
        # Try to update with same commit (should not update)
        updated, vi2, path = VersionInfo.update_version_file(test_file)
        
        self.assertFalse(updated)  # Should not update
        self.assertEqual(vi2.commit, self.test_commit_hash)
        self.assertEqual(path, test_file)
    
    def test_update_version_file_with_change(self):
        """Test update_version_file when commit has changed."""
        test_file = self.temp_dir / "test_version.py"
        old_commit = "old_commit_hash"
        new_commit = "new_commit_hash"
        
        # Temporarily modify the mock to return old commit
        self.git_mock_patcher.stop()
        
        original_path_open = Path.open
        test_ref = self.test_ref
        
        def mock_old_commit(path_instance, *args, **kwargs):
            mock_file = MagicMock()
            # For .py files, use real file operations
            if str(path_instance).endswith('.py'):
                return original_path_open(path_instance, *args, **kwargs)
            if 'HEAD' in str(path_instance):
                mock_file.__enter__.return_value.read.return_value = f"ref: {test_ref}"
            else:
                mock_file.__enter__.return_value.read.return_value = old_commit
            return mock_file
        
        with patch.object(Path, 'open', mock_old_commit):
            vi1 = VersionInfo()
            vi1.write_version_file(test_file)
            print(f"DEBUG: vi1.commit = {vi1.commit}")
        
        # Now modify the mock to return new commit
        def mock_new_commit(path_instance, *args, **kwargs):
            mock_file = MagicMock()
            # For .py files, use real file operations
            if str(path_instance).endswith('.py'):
                return original_path_open(path_instance, *args, **kwargs)
            if 'HEAD' in str(path_instance):
                mock_file.__enter__.return_value.read.return_value = f"ref: {test_ref}"
            else:
                mock_file.__enter__.return_value.read.return_value = new_commit
            return mock_file
        
        with patch.object(Path, 'open', mock_new_commit):
            updated, vi2, path = VersionInfo.update_version_file(test_file)
            print(f"DEBUG: vi2.commit = {vi2.commit}")
            print(f"DEBUG: updated = {updated}")
        
        # Restart the original mock
        self.git_mock_patcher.start()
        
        self.assertTrue(updated)  # Should update
        self.assertEqual(vi2.commit, new_commit)
        self.assertEqual(path, test_file)
    
    def test_get_latest(self):
        """Test get_latest method."""
        with patch.object(VersionInfo, 'update_version_file') as mock_update:
            test_vi = VersionInfo()
            mock_update.return_value = (True, test_vi, Path("test"))
            
            result = VersionInfo.get_latest()
            
            self.assertEqual(result, test_vi)
            mock_update.assert_called_once()
    
    def test_version_info_with_invalid_datetime_in_file(self):
        """Test handling of invalid datetime in version file."""
        test_file = self.temp_dir / "test_version.py"
        
        # Create file with invalid datetime
        test_content = '''# Test version file
__version__: str = '2025.6.9.120000'
__build_time__: str = 'invalid-datetime'
__commit__: str = 'test_commit'
'''
        test_file.write_text(test_content)
        
        # Should raise ValueError for invalid datetime
        with self.assertRaises(ValueError) as context:
            VersionInfo.from_version_file(test_file)
        
        self.assertIn("Invalid datetime format", str(context.exception))


class TestConstants(unittest.TestCase):
    """Test that package constants are properly defined."""
    
    def test_package_constants(self):
        """Test that required constants exist and have expected types."""
        self.assertIsInstance(PACKAGE_NAME, str)
        self.assertEqual(PACKAGE_NAME, 'statscan')
        
        self.assertIsInstance(VERSION_FILE, Path)
        self.assertTrue(str(VERSION_FILE).endswith('_version.py'))


if __name__ == '__main__':
    unittest.main()
