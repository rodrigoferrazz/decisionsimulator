# **Define Simulator Scope and Decision Logic**

## **1\. Simulator Objective**

The simulator will support agricultural decision-making by helping users identify the best seed density strategy under different environmental and operational conditions. Based on user inputs related to climate, soil conditions, and probability scenarios, the system will calculate and recommend the most advantageous strategy according to quantitative decision criteria.

The simulator is directly connected to the analyses developed in previous sprints, especially:

* Problem Framing  
* Payoff Matrix  
* Decision Tree  
* Data Characterization  
* Wireframe Prototype

The goal is to transform the analytical logic previously modeled into an interactive and accessible decision support tool.

# **2\. Decision Criteria Implemented**

## **Primary Criterion \-  Expected Value (EV)**

The main decision criterion implemented in Version 1 of the simulator will be Expected Value (EV).

The simulator will:

1. Receive probabilities for different agricultural scenarios;  
2. Associate each scenario with an expected productivity payoff;  
3. Calculate the weighted average outcome for each strategy;  
4. Recommend the strategy with the highest expected value.

Expected Value was selected because:

* it aligns with the probabilistic analysis developed in previous sprints;  
* it allows comparison between different agricultural strategies;  
* it supports rational decision-making under uncertainty;  
* it is simple enough to be interpreted by non-technical users.

The implemented logic follows:

***EV=∑(Pi​×Vi​)*** 

## **Secondary Criterion \- Minimax (Going Beyond)**

As a “going beyond” implementation, the simulator may also include the Minimax criterion.

This criterion focuses on minimizing the worst possible loss for each strategy, helping more risk-averse users.

The simulator will compare:

* Strategy with highest Expected Value;  
* Strategy with lowest maximum risk (Minimax).

This comparison increases the interpretability of the recommendation process and allows users to evaluate different decision perspectives.

# **3\. Simulator Inputs**

The simulator will contain configurable input parameters representing key uncertainties identified during the project.

## **Main Inputs**

| Input Variable | Description |
| ----- | ----- |
| Climate Scenario Probability | Probability of favorable, moderate, or unfavorable climate conditions |
| Soil pH | Soil acidity level impacting productivity |
| Seed Density Strategy | Strategy selected for simulation (Conservative, Adaptive, Intensive) |
| Expected Productivity | Estimated yield for each scenario |
| Risk Level | Operational/agricultural uncertainty associated with the strategy |

# **4\. States of the World**

The simulator logic will consider different states of the world previously explored in the Payoff Matrix.

## **Example States**

| State of the World | Description |
| ----- | ----- |
| Favorable Climate | Stable rainfall and ideal conditions |
| Moderate Climate | Some instability but manageable production |
| Unfavorable Climate | Drought, irregular rainfall, or high operational risk |

Each state will contain:

* a probability value;  
* a payoff/productivity estimation;  
* associated operational risk.

# **5\. Decision Alternatives**

The simulator will compare predefined agricultural strategies.

## **Example Alternatives**

| Strategy | Description |
| ----- | ----- |
| Conservative | Lower operational risk and moderate productivity |
| Adaptive | Balanced approach between productivity and stability |
| Intensive | Higher productivity potential with greater risk exposure |

# **6\. Simulator Output**

The output section will present:

* Recommended strategy;  
* Expected Value calculation;  
* Comparison between strategies;  
* Risk interpretation;  
* Simple explanation for non-technical users.

## **Example Output**

Recommended Strategy: Adaptive Strategy

Expected Value: 5,302 sacks/hectare

Reason: This strategy achieved the highest expected productivity considering the probability distribution of climate scenarios.

# **7\. Alignment With Previous Sprints**

The simulator directly reuses the analytical structure developed during earlier project stages.

| Previous Artifact | Contribution to Simulator |
| ----- | ----- |
| Problem Framing | Defined the central agricultural decision |
| Data Characterization | Identified relevant variables and uncertainties |
| Payoff Matrix | Established payoff relationships between strategies and scenarios |
| Decision Tree | Structured probabilistic logic and expected outcomes |
| Wireframe | Defined user interaction and interface flow |

# **8\. Planned Functionalities**

## **Baseline Functionalities**

* User input fields;  
* Expected Value calculation;  
* Strategy recommendation;  
* Clear output visualization;  
* README documentation.

## **Going Beyond Functionalities**

* Multiple decision criteria comparison;  
* Input validation for probabilities;  
* Simple payoff matrix visualization;  
* Interactive charts.

# **9\. Technical Implementation**

## **Proposed Stack**

| Component | Technology |
| ----- | ----- |
| Front-End Interface | Streamlit |
| Data Processing | Python |
| Calculations | NumPy / Pandas |
| Visualizations | Plotly |
| Repository | GitLab |

The simulator will be accessible through a public URL and runnable directly from the repository.

# **10\. Expected User Flow**

1. User selects agricultural conditions;  
2. User inputs probabilities and scenario parameters;  
3. Simulator processes decision criteria;  
4. System compares strategies;  
5. Final recommendation is displayed.

The interface will abstract technical complexity and focus on practical decision support for agricultural stakeholders.

