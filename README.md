# Algorithmic Oligopoly Simulation with Large Language Models

## Overview

This repository contains the Python source code for a longitudinal economic simulation designed to evaluate the strategic behavior of large language models in a competitive market. The script facilitates a one thousand round oligopoly game among four distinct artificial intelligence agents using the OpenRouter application programming interface.

The simulated agents include GPT 5.4, DeepSeek V3.2, Claude Sonnet 4.6, and Gemini 3 Flash Preview.

## Key Features

* **Dynamic Market Phases:** The simulation automatically transitions through four distinct macroeconomic environments (Baseline Stability, Economic Contraction, Network Conformity, and Regulation). Each phase applies a completely different mathematical payoff matrix to test algorithmic adaptability.
* **The Delta Axiom:** A specialized prompt engineering framework that supplies agents with real time leaderboard rankings and score gaps. This mathematical logic forces trailing models to compete aggressively, preventing artificial stagnation and triggering realistic price wars.
* **Asynchronous Execution:** The script leverages asynchronous functions to query all four language models simultaneously, ensuring rapid and efficient simulation cycles.
* **Automated Data Export:** Upon completion, the code generates a highly detailed Excel workbook containing advanced economic metrics suitable for academic research and visualization.

## Prerequisites

Ensure you have Python installed on your system. You will need to install three external libraries to run the script successfully. Run the following command in your terminal:

`pip install openai pandas openpyxl`

## Configuration and Usage

1. Clone or download this repository to your local machine.
2. Open the Python script in your preferred code editor.
3. Locate the configuration section at the top of the file and replace `"YOUR API KEY"` with your actual OpenRouter API key.
4. Execute the simulation by running the script in your terminal:

`python oligopoly_simulation.py`

*Note: The simulation makes four thousand total application programming interface requests. Execution time will depend on network speeds and server response times.*

## Output Data

Once the one thousand rounds are completed, the script automatically generates an Excel file that contains three comprehensive spreadsheets:

1. **Leaderboard:** Ranks the models based on total cumulative profit while calculating their risk variance and overall cooperation rate.
2. **Phase Analysis:** Details exactly how each model adapted its strategy and average profit across the four shifting market environments.
3. **Full Time Series:** Provides a chronological log of every single decision, the resulting points, and the fifty round moving average of global market aggression.
