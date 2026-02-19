"""
Basic tests for ProjectGoombaStomp CLI

Run with: pytest tests/
"""
import os
import tempfile
import shutil
from pathlib import Path

# Import our CLI functions
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from projectgoombastomp.cli import (
    build_folder_structure,
    collect_file_contents,
    generate_markdown,
    validate_directory
)


def test_build_folder_structure():
    """Test folder structure generation with a simple directory."""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some test files and directories
        test_dir = Path(temp_dir) / "test_project"
        test_dir.mkdir()
        
        (test_dir / "README.md").write_text("# Test Project")
        (test_dir / "src").mkdir()
        (test_dir / "src" / "main.py").write_text("print('Hello World')")
        (test_dir / "docs").mkdir()
        (test_dir / "docs" / "guide.txt").write_text("User guide")
        
        # Test the folder structure function
        result = build_folder_structure(str(test_dir))
        
        # Check that key elements are in the output
        assert "test_project/" in result
        assert "README.md" in result
        assert "src" in result
        assert "docs" in result
        assert "├──" in result or "└──" in result  # Tree symbols


def test_collect_file_contents():
    """Test file content collection."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_files"
        test_dir.mkdir()
        
        # Create test files
        (test_dir / "config.json").write_text('{"name": "test"}')
        (test_dir / "README.md").write_text("# Test\nThis is a test.")
        (test_dir / "script.py").write_text("print('hello')")
        
        # Test with basic extensions (should include .json and .md)
        extensions = {".json", ".md", ".txt"}
        result = collect_file_contents(str(test_dir), extensions)
        
        # Check that content is included
        assert "config.json" in result
        assert "README.md" in result
        assert '{"name": "test"}' in result
        assert "# Test" in result
        
        # Python file should NOT be included (not in extensions)
        assert "script.py" not in result


def test_collect_file_contents_max_size():
    """Test file content collection with max size limit."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_size"
        test_dir.mkdir()

        # Create a small file (10 bytes)
        small_file = test_dir / "small.txt"
        small_file.write_text("a" * 10)

        # Create a large file (20 bytes)
        large_file = test_dir / "large.txt"
        large_file.write_text("b" * 20)

        extensions = {".txt"}

        # Test with max_file_size=15
        result = collect_file_contents(str(test_dir), extensions, max_file_size=15)

        # small.txt should be included
        assert "small.txt" in result
        assert "aaaaaaaaaa" in result

        # large.txt should be skipped with message
        assert "large.txt" in result
        assert "[File too large: 20 bytes - skipped]" in result
        assert "bbbbbbbbbbbbbbbbbbbb" not in result


def test_validate_directory():
    """Test directory validation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Valid directory should return absolute path
        result = validate_directory(temp_dir)
        assert os.path.isabs(result)
        assert os.path.exists(result)
        
        # Test with non-existent directory (should exit, but we can't easily test that)
        # This would require mocking sys.exit()


def test_generate_markdown():
    """Test complete markdown generation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_project"
        test_dir.mkdir()
        
        (test_dir / "README.md").write_text("# Project")
        (test_dir / "config.json").write_text('{"version": "1.0"}')
        
        extensions = {".md", ".json"}
        result = generate_markdown(str(test_dir), extensions)
        
        # Check structure
        assert "# test_project - Project Documentation" in result
        assert "## Folder Structure" in result
        assert "## File Contents" in result
        assert "README.md" in result
        assert "config.json" in result


def test_symlink_skipping():
    """Test that symbolic links are skipped in folder structure and content collection."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_symlinks"
        test_dir.mkdir()

        # Create a real file
        real_file = test_dir / "real.txt"
        real_file.write_text("Real content")

        # Create a symlink to the real file
        link_file = test_dir / "link.txt"
        try:
            os.symlink(str(real_file), str(link_file))
        except OSError:
            # Skip if system doesn't support symlinks (e.g. some Windows configs)
            import pytest
            pytest.skip("Symlinks not supported")

        # Test folder structure
        structure = build_folder_structure(str(test_dir))
        assert "real.txt" in structure
        assert "link.txt" not in structure

        # Test file content collection
        extensions = {".txt"}
        contents = collect_file_contents(str(test_dir), extensions)
        assert "real.txt" in contents
        assert "Real content" in contents
        assert "link.txt" not in contents


if __name__ == "__main__":
    # Run tests manually if executed directly
    test_build_folder_structure()
    test_collect_file_contents()
    test_collect_file_contents_max_size()
    test_validate_directory()
    test_generate_markdown()
    test_symlink_skipping()
    print("✅ All tests passed!")
