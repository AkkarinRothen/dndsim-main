"""
Improved Selenium tests for Flask web UI combat system.

This module provides comprehensive UI testing with robust error handling,
logging, and validation for a combat web application.
"""

import os
import sys
import time
import logging
import subprocess
from typing import Optional
from contextlib import contextmanager

import requests
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://127.0.0.1:5000/"
DEFAULT_TIMEOUT = 10
MAX_COMBAT_TURNS = 50
RETRY_ATTEMPTS = 3
ELEMENT_INTERACTION_DELAY = 0.5


class TestConfig:
    """Test configuration and constants."""
    
    # Element IDs
    COMBAT_SETUP_FORM = "combat-setup-form"
    START_COMBAT_BTN = "start-combat-btn"
    NEXT_TURN_BTN = "next-turn-btn"
    RESET_COMBAT_BTN = "reset-combat-btn"
    COMBAT_LOG = "combat-log"
    
    # Expected text
    COMBAT_ENDED_TEXT = "Combat ended."
    START_COMBAT_TEXT = "Start Combat"


class UITestException(Exception):
    """Base exception for UI test errors."""
    pass


class ElementNotFoundError(UITestException):
    """Raised when an expected element is not found."""
    pass


class CombatTimeoutError(UITestException):
    """Raised when combat doesn't end within expected time."""
    pass


@contextmanager
def screenshot_on_failure(driver: webdriver.Chrome, test_name: str):
    """Context manager to take screenshot on test failure.
    
    Args:
        driver: Selenium WebDriver instance
        test_name: Name of the test for screenshot filename
    """
    try:
        yield
    except Exception as e:
        screenshot_path = f"/home/claude/screenshot_{test_name}_{int(time.time())}.png"
        try:
            driver.save_screenshot(screenshot_path)
            logger.error(f"Test failed. Screenshot saved to: {screenshot_path}")
            logger.error(f"Page source: {driver.page_source[:500]}...")
        except Exception as screenshot_error:
            logger.error(f"Failed to save screenshot: {screenshot_error}")
        raise e


@pytest.fixture(scope="function")
def chrome_driver():
    """Fixture to set up and tear down Chrome WebDriver.
    
    Yields:
        webdriver.Chrome: Configured Chrome WebDriver instance
    """
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Add additional options for stability
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")
    
    driver = None
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(2)  # Implicit wait for elements
        logger.info("Chrome WebDriver initialized successfully")
        yield driver
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {e}")
        raise
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Chrome WebDriver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")


def wait_for_element(
    driver: webdriver.Chrome,
    by: By,
    value: str,
    timeout: int = DEFAULT_TIMEOUT,
    condition: str = "presence"
) -> WebElement:
    """Wait for an element with enhanced error handling.
    
    Args:
        driver: Selenium WebDriver instance
        by: Selenium By locator strategy
        value: Element identifier
        timeout: Maximum wait time in seconds
        condition: Expected condition type ('presence', 'visible', 'clickable')
    
    Returns:
        WebElement: The located element
        
    Raises:
        ElementNotFoundError: If element is not found within timeout
    """
    conditions = {
        "presence": EC.presence_of_element_located,
        "visible": EC.visibility_of_element_located,
        "clickable": EC.element_to_be_clickable
    }
    
    if condition not in conditions:
        raise ValueError(f"Invalid condition: {condition}")
    
    try:
        logger.debug(f"Waiting for element {value} with condition {condition}")
        element = WebDriverWait(driver, timeout).until(
            conditions[condition]((by, value))
        )
        logger.debug(f"Element {value} found successfully")
        return element
    except TimeoutException as e:
        logger.error(f"Element {value} not found within {timeout} seconds")
        raise ElementNotFoundError(
            f"Element '{value}' not found within {timeout} seconds using {condition} condition"
        ) from e


def safe_click(
    driver: webdriver.Chrome,
    element: WebElement,
    max_retries: int = RETRY_ATTEMPTS
) -> None:
    """Safely click an element with retry logic.
    
    Args:
        driver: Selenium WebDriver instance
        element: Element to click
        max_retries: Maximum number of retry attempts
        
    Raises:
        UITestException: If click fails after all retries
    """
    for attempt in range(max_retries):
        try:
            # Try standard click first
            element.click()
            logger.debug("Element clicked successfully")
            return
        except ElementClickInterceptedException:
            logger.warning(f"Click intercepted, attempt {attempt + 1}/{max_retries}")
            try:
                # Try JavaScript click as fallback
                driver.execute_script("arguments[0].click();", element)
                logger.debug("Element clicked via JavaScript")
                return
            except Exception as js_error:
                logger.warning(f"JavaScript click failed: {js_error}")
        except StaleElementReferenceException:
            logger.warning(f"Stale element, attempt {attempt + 1}/{max_retries}")
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Unexpected error clicking element: {e}")
            if attempt == max_retries - 1:
                raise UITestException(f"Failed to click element after {max_retries} attempts") from e
        
        time.sleep(0.5)
    
    raise UITestException(f"Failed to click element after {max_retries} attempts")


def is_element_enabled(element: WebElement) -> bool:
    """Check if an element is enabled.
    
    Args:
        element: WebElement to check
        
    Returns:
        bool: True if element is enabled, False otherwise
    """
    try:
        is_enabled = element.is_enabled()
        has_disabled_class = "disabled" in (element.get_attribute("class") or "")
        has_disabled_attr = element.get_attribute("disabled") is not None
        
        return is_enabled and not has_disabled_class and not has_disabled_attr
    except Exception as e:
        logger.error(f"Error checking element enabled state: {e}")
        return False


def wait_for_element_enabled(
    driver: webdriver.Chrome,
    by: By,
    value: str,
    timeout: int = DEFAULT_TIMEOUT
) -> WebElement:
    """Wait for an element to be enabled.
    
    Args:
        driver: Selenium WebDriver instance
        by: Selenium By locator strategy
        value: Element identifier
        timeout: Maximum wait time in seconds
        
    Returns:
        WebElement: The enabled element
        
    Raises:
        TimeoutException: If element doesn't become enabled within timeout
    """
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        try:
            element = driver.find_element(by, value)
            if is_element_enabled(element):
                logger.debug(f"Element {value} is enabled")
                return element
        except NoSuchElementException:
            pass
        
        time.sleep(0.2)
    
    raise TimeoutException(f"Element '{value}' did not become enabled within {timeout} seconds")


def get_element_text_safe(driver: webdriver.Chrome, by: By, value: str) -> str:
    """Safely get text from an element.
    
    Args:
        driver: Selenium WebDriver instance
        by: Selenium By locator strategy
        value: Element identifier
        
    Returns:
        str: Element text or empty string if not found
    """
    try:
        element = driver.find_element(by, value)
        return element.text
    except NoSuchElementException:
        logger.warning(f"Element {value} not found when getting text")
        return ""
    except Exception as e:
        logger.error(f"Error getting text from element {value}: {e}")
        return ""


def verify_page_loaded(driver: webdriver.Chrome, expected_url: Optional[str] = None) -> None:
    """Verify that the page has loaded successfully.
    
    Args:
        driver: Selenium WebDriver instance
        expected_url: Expected URL to verify (optional)
        
    Raises:
        UITestException: If page is not loaded correctly
    """
    try:
        # Check if page is loaded
        WebDriverWait(driver, DEFAULT_TIMEOUT).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Verify URL if provided
        if expected_url:
            current_url = driver.current_url
            if not current_url.startswith(expected_url):
                raise UITestException(
                    f"Expected URL to start with '{expected_url}', got '{current_url}'"
                )
        
        logger.info(f"Page loaded successfully: {driver.current_url}")
    except TimeoutException as e:
        raise UITestException("Page did not load within timeout") from e


@pytest.fixture(scope="session")
def flask_app():
    """Fixture to manage Flask application lifecycle.
    
    This can be expanded to actually start/stop the Flask app if needed.
    """
    # Wait for Flask app to be available
    max_wait = 30
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(BASE_URL, timeout=2)
            if response.status_code == 200:
                logger.info("Flask application is ready")
                yield
                return
        except requests.exceptions.RequestException:
            time.sleep(1)
    
    raise UITestException(f"Flask application not available at {BASE_URL} after {max_wait} seconds")


def test_homepage_loads(chrome_driver, flask_app):
    """Test that the homepage loads successfully.
    
    Args:
        chrome_driver: Chrome WebDriver fixture
        flask_app: Flask application fixture
    """
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "homepage_loads"):
        logger.info("Testing homepage load")
        driver.get(BASE_URL)
        
        verify_page_loaded(driver, BASE_URL)
        
        # Verify essential elements are present
        wait_for_element(driver, By.ID, TestConfig.COMBAT_SETUP_FORM)
        
        assert TestConfig.START_COMBAT_TEXT in driver.page_source, \
            "Expected 'Start Combat' text not found on homepage"
        
        logger.info("Homepage loaded successfully")


def test_combat_setup_form_validation(chrome_driver, flask_app):
    """Test combat setup form validation.
    
    Args:
        chrome_driver: Chrome WebDriver fixture
        flask_app: Flask application fixture
    """
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "combat_setup_validation"):
        logger.info("Testing combat setup form validation")
        driver.get(BASE_URL)
        verify_page_loaded(driver, BASE_URL)
        
        # Verify form elements exist
        form = wait_for_element(driver, By.ID, TestConfig.COMBAT_SETUP_FORM)
        assert form is not None, "Combat setup form not found"
        
        start_button = wait_for_element(
            driver, By.ID, TestConfig.START_COMBAT_BTN, condition="clickable"
        )
        assert start_button is not None, "Start combat button not found"
        
        logger.info("Combat setup form validation passed")


def test_full_combat_flow(chrome_driver, flask_app):
    """Test complete combat flow from start to finish.
    
    This test covers:
    - Starting combat
    - Running combat turns
    - Verifying combat completion
    - Resetting combat
    
    Args:
        chrome_driver: Chrome WebDriver fixture
        flask_app: Flask application fixture
    """
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "full_combat_flow"):
        logger.info("=== Starting Full Combat Flow Test ===")
        
        # Navigate to homepage
        driver.get(BASE_URL)
        verify_page_loaded(driver, BASE_URL)
        logger.info("Homepage loaded")
        
        # --- Start Combat ---
        try:
            setup_form = wait_for_element(driver, By.ID, TestConfig.COMBAT_SETUP_FORM)
            logger.info("Combat setup form found")
            
            start_button = wait_for_element(
                driver, By.ID, TestConfig.START_COMBAT_BTN, condition="clickable"
            )
            safe_click(driver, start_button)
            logger.info("Start combat button clicked")
            
            time.sleep(ELEMENT_INTERACTION_DELAY)
            
        except ElementNotFoundError as e:
            logger.error(f"Failed to start combat: {e}")
            raise UITestException("Could not start combat") from e
        
        # Verify combat started
        try:
            combat_log = wait_for_element(driver, By.ID, TestConfig.COMBAT_LOG, timeout=5)
            assert combat_log is not None, "Combat log not found after starting combat"
            logger.info("Combat started successfully - log present")
        except ElementNotFoundError as e:
            raise UITestException("Combat did not start - log not found") from e
        
        # --- Run Combat Turns ---
        logger.info(f"Starting combat turns (max: {MAX_COMBAT_TURNS})")
        turn_count = 0
        combat_ended = False
        
        while turn_count < MAX_COMBAT_TURNS:
            try:
                # Wait for next turn button to be enabled
                try:
                    next_turn_button = wait_for_element_enabled(
                        driver,
                        By.ID,
                        TestConfig.NEXT_TURN_BTN,
                        timeout=10
                    )
                except TimeoutException:
                    # Button didn't become enabled - check if combat ended
                    logger.info("Next turn button not enabled - checking if combat ended")
                    combat_log_text = get_element_text_safe(driver, By.ID, TestConfig.COMBAT_LOG)
                    
                    if TestConfig.COMBAT_ENDED_TEXT in combat_log_text:
                        logger.info("Combat ended (button disabled)")
                        combat_ended = True
                        break
                    else:
                        # Try to find the button and check its state
                        try:
                            button = driver.find_element(By.ID, TestConfig.NEXT_TURN_BTN)
                            if not is_element_enabled(button):
                                logger.warning("Button disabled but no 'Combat ended' message")
                                break
                        except NoSuchElementException:
                            raise UITestException("Next turn button disappeared unexpectedly")
                        
                        raise CombatTimeoutError(
                            f"Next turn button not enabled after turn {turn_count}, but combat not ended"
                        )
                
                # Click next turn button
                safe_click(driver, next_turn_button)
                turn_count += 1
                
                logger.debug(f"Turn {turn_count} executed")
                time.sleep(ELEMENT_INTERACTION_DELAY)
                
                # Check if combat ended
                combat_log_text = get_element_text_safe(driver, By.ID, TestConfig.COMBAT_LOG)
                if TestConfig.COMBAT_ENDED_TEXT in combat_log_text:
                    logger.info(f"Combat ended after {turn_count} turns")
                    combat_ended = True
                    break
                
            except StaleElementReferenceException:
                logger.warning(f"Stale element at turn {turn_count}, retrying...")
                time.sleep(0.5)
                continue
                
            except Exception as e:
                logger.error(f"Error during turn {turn_count}: {e}")
                # Take screenshot for debugging
                screenshot_path = f"/home/claude/turn_error_{turn_count}.png"
                try:
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"Error screenshot saved: {screenshot_path}")
                except:
                    pass
                raise UITestException(f"Combat flow failed at turn {turn_count}") from e
        
        # Verify combat completed successfully
        if not combat_ended:
            combat_log_text = get_element_text_safe(driver, By.ID, TestConfig.COMBAT_LOG)
            raise CombatTimeoutError(
                f"Combat did not end within {MAX_COMBAT_TURNS} turns. "
                f"Last log state: {combat_log_text[:200]}"
            )
        
        assert turn_count < MAX_COMBAT_TURNS, \
            f"Combat exceeded maximum turns ({MAX_COMBAT_TURNS})"
        
        # Verify combat ended message
        combat_log_text = get_element_text_safe(driver, By.ID, TestConfig.COMBAT_LOG)
        assert TestConfig.COMBAT_ENDED_TEXT in combat_log_text, \
            "Combat ended but 'Combat ended.' message not found in log"
        
        logger.info(f"Combat completed successfully in {turn_count} turns")
        
        # --- Reset Combat ---
        logger.info("Resetting combat")
        try:
            reset_button = wait_for_element(
                driver, By.ID, TestConfig.RESET_COMBAT_BTN, condition="clickable"
            )
            safe_click(driver, reset_button)
            time.sleep(ELEMENT_INTERACTION_DELAY)
            
            # Verify reset successful
            wait_for_element(driver, By.ID, TestConfig.COMBAT_SETUP_FORM, timeout=10)
            
            assert TestConfig.START_COMBAT_TEXT in driver.page_source, \
                "Start Combat text not found after reset"
            
            # Verify combat log is removed
            try:
                driver.find_element(By.ID, TestConfig.COMBAT_LOG)
                raise UITestException("Combat log still present after reset")
            except NoSuchElementException:
                logger.info("Combat log properly removed after reset")
            
            logger.info("Combat reset successfully")
            
        except Exception as e:
            logger.error(f"Failed to reset combat: {e}")
            raise UITestException("Combat reset failed") from e
        
        logger.info("=== Full Combat Flow Test Completed Successfully ===")


def test_multiple_combat_cycles(chrome_driver, flask_app):
    """Test running multiple combat cycles to verify stability.
    
    Args:
        chrome_driver: Chrome WebDriver fixture
        flask_app: Flask application fixture
    """
    driver = chrome_driver
    cycles = 3
    
    with screenshot_on_failure(driver, "multiple_combat_cycles"):
        logger.info(f"Testing {cycles} combat cycles")
        
        for cycle in range(cycles):
            logger.info(f"--- Cycle {cycle + 1}/{cycles} ---")
            
            driver.get(BASE_URL)
            verify_page_loaded(driver, BASE_URL)
            
            # Start combat
            start_button = wait_for_element(
                driver, By.ID, TestConfig.START_COMBAT_BTN, condition="clickable"
            )
            safe_click(driver, start_button)
            time.sleep(ELEMENT_INTERACTION_DELAY)
            
            # Run a few turns
            for turn in range(5):
                try:
                    next_button = wait_for_element_enabled(
                        driver, By.ID, TestConfig.NEXT_TURN_BTN, timeout=5
                    )
                    safe_click(driver, next_button)
                    time.sleep(0.3)
                    
                    # Check if combat ended early
                    log_text = get_element_text_safe(driver, By.ID, TestConfig.COMBAT_LOG)
                    if TestConfig.COMBAT_ENDED_TEXT in log_text:
                        logger.info(f"Combat ended early at turn {turn + 1}")
                        break
                except TimeoutException:
                    logger.info("Combat ended during cycle")
                    break
            
            logger.info(f"Cycle {cycle + 1} completed")
        
        logger.info("Multiple combat cycles test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
