import os
import sys
import time
import subprocess
import requests # Keep requests for wait_for_flask_app
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import pytest

# Base URL of your Flask app
BASE_URL = "http://127.0.0.1:5000/"

# ... (rest of the file remains the same until the while loop in test_full_combat_flow) ...

        # --- Run Turns ---
        # Click Next Turn until combat is over or a reasonable number of rounds (e.g., 20)
        # This prevents infinite loops in case combat logic has issues
        max_turns = 50
        turn_count = 0
        while turn_count < max_turns:
            # Wait for the button to be enabled
            try:
                WebDriverWait(driver, 10).until_not(
                    EC.element_attribute_to_include((By.ID, "next-turn-btn"), "disabled")
                )
            except TimeoutException:
                # If button remains disabled, combat is likely over
                next_turn_button = driver.find_element(By.ID, "next-turn-btn")
                if "disabled" in next_turn_button.get_attribute("class"):
                    break
                else:
                    raise # Re-raise if some other timeout issue

            next_turn_button = driver.find_element(By.ID, "next-turn-btn") # Get the enabled button
            driver.execute_script("arguments[0].click();", next_turn_button)
            time.sleep(0.5) # Short delay to allow UI to update
            turn_count += 1
            # Check if combat is reported as over
            if "Combat ended." in driver.find_element(By.ID, "combat-log").text:
                break
        
        assert turn_count < max_turns, "Combat did not end within expected number of turns."
        assert "Combat ended." in driver.find_element(By.ID, "combat-log").text

        # --- Reset Combat ---
        driver.find_element(By.ID, "reset-combat-btn").click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "combat-setup-form")))
        assert "Start Combat" in driver.page_source
        assert "combat-log" not in driver.page_source # Combat log should be gone
