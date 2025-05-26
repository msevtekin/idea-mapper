import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile

# Add project root to PYTHONPATH to allow direct import of app
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import export_mind_map_as_png

class TestPngExport(unittest.TestCase):

    def setUp(self):
        # Create a dummy html file that will be used by multiple tests
        # Suffix is important for os.path.abspath in the tested function
        self.tmp_html_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w")
        self.html_path = self.tmp_html_file.name
        self.tmp_html_file.write("<html><body><h1>Test</h1></body></html>")
        self.tmp_html_file.close()

    def tearDown(self):
        # Clean up the dummy html file
        os.remove(self.html_path)
        # Clean up any PNG files that might be created (though mocks shouldn't create them)
        if os.path.exists("test_map.png"):
            os.remove("test_map.png")
        if os.path.exists("test_map_fail.png"):
            os.remove("test_map_fail.png")

    @patch('app.time.sleep') # Patch time.sleep used in the function
    @patch('app.st') # Mock streamlit as st.error is called
    @patch('app.webdriver.Chrome') # Patch where it's looked up (app.webdriver)
    def test_export_successful(self, mock_chrome_driver, mock_st_error, mock_sleep):
        # Configure mock for webdriver.Chrome
        mock_driver_instance = MagicMock()
        mock_chrome_driver.return_value = mock_driver_instance
        
        png_path = "test_map.png"
        
        # Call the function
        result = export_mind_map_as_png(self.html_path, png_path)
        
        # Assertions
        self.assertEqual(result, png_path)
        mock_chrome_driver.assert_called_once() # Check if webdriver.Chrome was instantiated
        
        # Check that options were configured
        args, kwargs = mock_chrome_driver.call_args
        self.assertIn("options", kwargs)
        options = kwargs["options"]
        self.assertIn("--headless", options.arguments)
        self.assertIn("--no-sandbox", options.arguments)
        self.assertIn("--disable-dev-shm-usage", options.arguments)
        self.assertIn("--window-size=1200,800", options.arguments)

        mock_driver_instance.get.assert_called_once_with("file://" + os.path.abspath(self.html_path))
        mock_sleep.assert_called_once_with(5) # Check that time.sleep was called
        mock_driver_instance.save_screenshot.assert_called_once_with(png_path)
        mock_driver_instance.quit.assert_called_once()
        
        mock_st_error.error.assert_not_called() # st.error should not be called

    @patch('app.time.sleep') # Patch time.sleep
    @patch('app.st') # Mock streamlit
    @patch('app.webdriver.Chrome')
    def test_export_selenium_exception_on_screenshot(self, mock_chrome_driver, mock_st_error, mock_sleep):
        # Configure mock
        mock_driver_instance = MagicMock()
        mock_chrome_driver.return_value = mock_driver_instance
        
        # Configure save_screenshot to raise an exception
        exception_message = "Selenium screenshot broke"
        mock_driver_instance.save_screenshot.side_effect = Exception(exception_message)
        
        png_path = "test_map_fail.png"
        
        # Call the function
        result = export_mind_map_as_png(self.html_path, png_path)
        
        # Assertions
        self.assertIsNone(result) # Function should return None on error
        
        mock_chrome_driver.assert_called_once()
        mock_driver_instance.get.assert_called_once_with("file://" + os.path.abspath(self.html_path))
        mock_sleep.assert_called_once_with(5) # time.sleep should have been called
        mock_driver_instance.save_screenshot.assert_called_once_with(png_path)

        # Assert that st.error was called with the correct message
        mock_st_error.error.assert_called_once_with(f"Error exporting to PNG: {exception_message}")
        
        mock_driver_instance.quit.assert_called_once() # quit should still be called in finally

    @patch('app.st') # Mock streamlit
    @patch('app.webdriver.Chrome') # No time.sleep if 'get' fails early
    def test_export_selenium_exception_on_get(self, mock_chrome_driver, mock_st_error): # mock_sleep is not needed here
        # Configure mock
        mock_driver_instance = MagicMock()
        mock_chrome_driver.return_value = mock_driver_instance
        
        # Configure driver.get to raise an exception
        exception_message = "Selenium get broke"
        mock_driver_instance.get.side_effect = Exception(exception_message)
        
        png_path = "test_map_fail_get.png"
        
        # Call the function
        result = export_mind_map_as_png(self.html_path, png_path)
        
        # Assertions
        self.assertIsNone(result) # Function should return None on error
        
        mock_chrome_driver.assert_called_once()
        mock_driver_instance.get.assert_called_once_with("file://" + os.path.abspath(self.html_path))
        
        mock_driver_instance.save_screenshot.assert_not_called() # Should not be called if get fails
        
        # Assert that st.error was called
        mock_st_error.error.assert_called_once_with(f"Error exporting to PNG: {exception_message}")
        
        mock_driver_instance.quit.assert_called_once() # quit should still be called

if __name__ == '__main__':
    unittest.main()
